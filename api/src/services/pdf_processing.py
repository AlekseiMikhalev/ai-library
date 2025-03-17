import gc
import json
import re
from llmsherpa.readers import LayoutPDFReader
from motor.motor_asyncio import AsyncIOMotorDatabase
from neo4j import Driver, AsyncDriver
import tiktoken
import torch
from src.repository.pdf_processing import PDFProcessingRepository
import asyncio
import logging
import time
from ollama import AsyncClient
from src.schemas.upload import (
    ProcessedBookMongoDB,
    SectionData,
    ProcessedBook,
    ExtractedConcepts,
)
from pathlib import Path
from PyPDF2 import PdfReader
from tqdm.asyncio import tqdm_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# LLM Models
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL")
GENERATION_MODEL: str = os.getenv("GENERATION_MODEL")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class PDFProcessorService:
    def __init__(
        self,
        ollama_client: AsyncClient,
        mongo_db: AsyncIOMotorDatabase,
        neo4j_sync_driver: Driver,
        neo4j_async_driver: AsyncDriver,
        pdf_reader: LayoutPDFReader,
    ):
        self.ollama_client = ollama_client
        self.mongo_db = mongo_db
        self.neo4j_sync_driver = neo4j_sync_driver
        self.neo4j_async_driver = neo4j_async_driver
        self.pdf_reader = pdf_reader
        self.processing_repository = PDFProcessingRepository(
            neo4j_async_driver=neo4j_async_driver,
            neo4j_sync_driver=neo4j_sync_driver,
            mongodb_client=mongo_db,
        )

        # Initialize memory management
        self.device = self._setup_gpu_memory()

        # Set chunk size based on model
        self.max_chunk_size = 4000

    def _setup_gpu_memory(self):
        """Configure GPU memory for optimal performance"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            return torch.device("cuda")
        return torch.device("cpu")

    def _manage_gpu_memory(self, force=False):
        """Smart GPU memory management"""
        if not torch.cuda.is_available():
            return

        # Only clean if memory usage is high or force is True
        if force or (
            torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated() > 0.7
        ):
            gc.collect()
            torch.cuda.empty_cache()

    async def _get_embedding(self, section_data: SectionData) -> SectionData:
        section_data = section_data.model_copy()
        if not section_data.concepts:
            return section_data
        concepts_string = ", ".join(section_data.concepts)
        embedding = await self.ollama_client.embed(
            model=EMBEDDING_MODEL, input=concepts_string
        )

        if embedding is not None:
            section_data.section_concepts_embedding = embedding.embeddings[0]
        return section_data

    def _split_text_by_size(self, text: str, max_tokens: int) -> list[str]:
        encoding = tiktoken.get_encoding("o200k_base")
        if not text.strip():
            return []

        # Split text into sentences (this regex splits on punctuation followed by whitespace)
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks = []
        current_chunk = ""
        current_chunk_tokens = 0

        for sentence in sentences:
            sentence_tokens = len(encoding.encode(sentence))
            # If the sentence alone exceeds max_tokens, split it further by words.
            if sentence_tokens > max_tokens:
                words = sentence.split()
                sub_chunk = ""
                sub_chunk_tokens = 0
                for word in words:
                    word_tokens = len(encoding.encode(word))
                    # Add a space if sub_chunk is not empty.
                    space_tokens = len(encoding.encode(" ")) if sub_chunk else 0
                    if sub_chunk_tokens + space_tokens + word_tokens <= max_tokens:
                        sub_chunk += (" " if sub_chunk else "") + word
                        sub_chunk_tokens += space_tokens + word_tokens
                    else:
                        # Try to add the finished sub_chunk to the current chunk if it fits.
                        if current_chunk:
                            space_tokens_chunk = len(encoding.encode(" "))
                            if (
                                current_chunk_tokens
                                + space_tokens_chunk
                                + sub_chunk_tokens
                                <= max_tokens
                            ):
                                current_chunk += " " + sub_chunk
                                current_chunk_tokens += (
                                    space_tokens_chunk + sub_chunk_tokens
                                )
                            else:
                                chunks.append(current_chunk)
                                current_chunk = sub_chunk
                                current_chunk_tokens = sub_chunk_tokens
                        else:
                            chunks.append(sub_chunk)
                        sub_chunk = word
                        sub_chunk_tokens = word_tokens
                # Append any remaining sub_chunk.
                if sub_chunk:
                    if current_chunk:
                        space_tokens_chunk = len(encoding.encode(" "))
                        if (
                            current_chunk_tokens + space_tokens_chunk + sub_chunk_tokens
                            <= max_tokens
                        ):
                            current_chunk += " " + sub_chunk
                            current_chunk_tokens += (
                                space_tokens_chunk + sub_chunk_tokens
                            )
                        else:
                            chunks.append(current_chunk)
                            current_chunk = sub_chunk
                            current_chunk_tokens = sub_chunk_tokens
                    else:
                        current_chunk = sub_chunk
                        current_chunk_tokens = sub_chunk_tokens
            else:
                # If sentence fits as a whole, add a space if needed.
                space_tokens = len(encoding.encode(" ")) if current_chunk else 0
                if current_chunk_tokens + space_tokens + sentence_tokens <= max_tokens:
                    current_chunk += (" " if current_chunk else "") + sentence
                    current_chunk_tokens += space_tokens + sentence_tokens
                else:
                    # Flush the current chunk and start a new one with the sentence.
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence
                    current_chunk_tokens = sentence_tokens

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    async def _extract_concepts_from_section(
        self, section_data: SectionData
    ) -> SectionData:
        section_data = section_data.model_copy()
        text = section_data.section_text

        if not text:
            return section_data

        chunks = self._split_text_by_size(text, self.max_chunk_size)

        PROMPT = "Extract main ideas described in the text below. The output should be a JSON `{'concepts': ['idea1', 'idea2']}`."

        # Function to process a single chunk
        async def process_chunk(chunk: str) -> list[str]:
            try:
                response = await self.ollama_client.chat(
                    model=GENERATION_MODEL,
                    messages=[{"role": "user", "content": f"{PROMPT}\n\n{chunk}"}],
                    format=ExtractedConcepts.model_json_schema(),
                    options={"num_ctx": 8000},
                )
                extracted_result = ExtractedConcepts.model_validate_json(
                    response.message.content
                )
                return extracted_result.concepts
            except Exception as e:
                logging.error(f"Error parsing concepts from chunk: {e}")
                return []

        # Run all chunk processing tasks concurrently
        results = await asyncio.gather(*(process_chunk(chunk) for chunk in chunks))
        if not results:
            return section_data

        flattened_results = [item for sublist in results for item in sublist]
        section_data.concepts = list(set(flattened_results))
        return section_data

    async def _get_embeddings(self, sections: list[SectionData]) -> list[SectionData]:
        tasks = [self._get_embedding(section) for section in sections]
        results = await asyncio.gather(*tasks)
        return results

    async def _read_pdf(self, pdf_url: str, document_id: str) -> ProcessedBook:
        doc = self.pdf_reader.read_pdf(pdf_url)

        # Get metadata
        metadata_reader = PdfReader(pdf_url)
        metadata = metadata_reader.metadata

        title = metadata.title
        author = metadata.author
        pages = len(metadata_reader.pages)
        published_date = metadata.creation_date

        # TODO: Get cover image
        cover_image = ""

        sections_with_all_paragraphs = []
        for section in doc.sections():
            section_paragraphs = section.paragraphs()
            section_extracted_paragraphs_dataset = []
            for section_paragraph in section_paragraphs:
                section_paragraphs_data = {
                    "level": section_paragraph.level,
                    "text": section_paragraph.to_text(
                        include_children=True, recurse=True
                    ),
                    "page": section_paragraph.page_idx + 1,
                    "parent_text": section_paragraph.parent_text(),
                    "parent_chain": list(
                        set(
                            [
                                item.to_text()
                                for item in section_paragraph.parent_chain()
                                if item.to_text() not in ["", None]
                            ]
                        )
                    ),
                }
                section_extracted_paragraphs_dataset.append(section_paragraphs_data)

            section_data = SectionData(
                section_name=section.title,
                section_paragraphs_data=section_extracted_paragraphs_dataset,
                section_text=section.to_text(include_children=True, recurse=True),
            )

            sections_with_all_paragraphs.append(section_data)

        processed_document = ProcessedBook(
            document_id=document_id,
            title=title,
            author=author,
            pages=pages,
            published_date=published_date,
            cover_image=cover_image,
            sections=sections_with_all_paragraphs,
        )

        return processed_document

    async def _extract_concepts(
        self, sections_features: list[SectionData]
    ) -> list[SectionData]:
        tasks = [
            self._extract_concepts_from_section(section)
            for section in sections_features
        ]

        # Progress of extracting concepts
        results = await tqdm_asyncio.gather(
            *tasks,
            desc="Extracting concepts",
            unit="sections",
            total=len(tasks),
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} sections",
            colour="cyan",
        )
        if not results:
            return sections_features
        return results

    async def process_pdf(self, pdf_url: str, document_id: str) -> ProcessedBook:
        try:
            # Save processing status
            await self.processing_repository.save_pdf_processing_metadata(
                ProcessedBookMongoDB(document_id=document_id, status="PROCESSING")
            )
            start_time = time.time()

            # Read PDF
            logging.info(f"Step 1/3: Reading and parsing PDF: {pdf_url}")
            processed_document = await self._read_pdf(pdf_url, document_id)
            sections_features = processed_document.sections

            # Clear GPU memory before LLM processing
            self._manage_gpu_memory(force=True)

            # Extract concepts
            logging.info("Step 2/3: Extracting concepts")
            sections_with_concepts = await self._extract_concepts(sections_features)
            processed_document.sections = sections_with_concepts
            flatten_concepts_per_book = [
                item for sublist in sections_with_concepts for item in sublist.concepts
            ]
            processed_document.concepts = list(set(flatten_concepts_per_book))

            logging.info("Concepts extracted")

            # Get embeddings
            logging.info("Step 3/3: Getting embeddings for sections concepts")
            sections_with_concepts_with_embeddings = await self._get_embeddings(
                processed_document.sections
            )
            processed_document.sections = sections_with_concepts_with_embeddings

            # Store into Neo4j
            logging.info("Step 4/4: Storing extracted features into Neo4j")
            await self.processing_repository.store_features_in_neo4j(processed_document)

            end_time = time.time()

            logging.info(
                f"Time spent on features extraction: {end_time - start_time:.2f} seconds"
            )

            # Clear GPU memory
            self._manage_gpu_memory(force=True)

            # Update processing status
            updated_document = (
                await self.processing_repository.update_pdf_processing_metadata(
                    ProcessedBookMongoDB(
                        document_id=document_id,
                        status="COMPLETED",
                    )
                )
            )

            # Remove temp PDF file after processing
            file_path = Path(pdf_url)
            if file_path.exists():
                file_path.unlink()

            return ProcessedBookMongoDB(**updated_document)
        except Exception as e:
            logging.error(f"Processing failed: {e}")
            updated_document = (
                await self.processing_repository.update_pdf_processing_metadata(
                    ProcessedBookMongoDB(document_id=document_id, status="FAILED")
                )
            )
            return ProcessedBookMongoDB(**updated_document)
