import gc
from llmsherpa.readers import LayoutPDFReader
import torch
from src.repository.pdf_processing import PDFProcessingRepository
from sklearn.cluster import AgglomerativeClustering
import asyncio
import logging
import time
from ollama import embed
from src.schemas.upload import SectionData, ProcessedDocument
from dotenv import load_dotenv
import os

load_dotenv()

LLMSHERPA_API_URL = os.getenv("LLMSHERPA_API_URL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class PDFProcessorService:
    def __init__(self):
        self.pdf_reader = LayoutPDFReader(LLMSHERPA_API_URL)
        self.processing_repository = PDFProcessingRepository()

    @staticmethod
    async def _get_embedding(section_data: SectionData) -> dict:
        section_data = section_data.model_copy()
        embedding = embed(model=EMBEDDING_MODEL, input=section_data.section_text)
        if embedding is not None:
            section_data.section_text_embedding = embedding.embeddings[0]
        return section_data

    async def _get_embeddings(self, sections: list[SectionData]) -> list[SectionData]:
        tasks = [self._get_embedding(section) for section in sections]
        results = await asyncio.gather(*tasks)
        return results

    def _read_pdf(self, pdf_url: str) -> list[SectionData]:
        doc = self.pdf_reader.read_pdf(pdf_url)
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
                    "parent_chain": set(
                        [
                            item.to_text()
                            for item in section_paragraph.parent_chain()
                            if item.to_text() not in ["", None]
                        ]
                    ),
                }
                section_extracted_paragraphs_dataset.append(section_paragraphs_data)

            section_data = SectionData(
                section_name=section.title,
                section_paragraphs_data=section_extracted_paragraphs_dataset,
                section_text=section.to_text(include_children=True, recurse=True),
            )

            sections_with_all_paragraphs.append(section_data)

        return sections_with_all_paragraphs

    def _get_clusters(self, sections_features_with_embeddings: list[SectionData]):
        embeddings_list = [
            section.section_text_embedding
            for section in sections_features_with_embeddings
        ]
        clustering = AgglomerativeClustering(
            n_clusters=None,
            linkage="complete",
            metric="cosine",
            distance_threshold=0.7,
        )
        cluster_labels = clustering.fit_predict(embeddings_list)

        sections_features_with_clusters = []
        for i, label in enumerate(cluster_labels):
            section_data = sections_features_with_embeddings[i].model_copy()
            section_data.cluster = f"cluster_{label}"
            sections_features_with_clusters.append(section_data)

        return sections_features_with_clusters

    async def process_pdf(self, pdf_url: str, document_id: str) -> ProcessedDocument:
        try:
            # Save processing status
            await self.processing_repository.save_pdf_processing_metadata(
                ProcessedDocument(
                    document_id=document_id, sections=[], status="PROCESSING"
                )
            )
            start_time = time.time()

            # Read PDF
            logging.info(f"Reading PDF: {pdf_url}")
            sections_features = self._read_pdf(pdf_url)

            # Get embeddings
            logging.info(f"Getting embeddings for {len(sections_features)} sections")
            sections_features_with_embeddings = await self._get_embeddings(
                sections_features
            )

            # Clear GPU memory
            logging.info("Clearing GPU memory")
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # Get clusters
            logging.info("Clustering sections")
            clustered_sections = self._get_clusters(sections_features_with_embeddings)

            end_time = time.time()

            logging.info(
                f"Time spent on features extraction: {end_time - start_time:.2f} seconds"
            )

            # Clear GPU memory
            logging.info("Clearing GPU memory")
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # Update processing status
            updated_document = (
                await self.processing_repository.update_pdf_processing_metadata(
                    ProcessedDocument(
                        document_id=document_id,
                        sections=clustered_sections,
                        status="COMPLETED",
                    )
                )
            )

            return ProcessedDocument(**updated_document)
        except Exception as e:
            logging.error(f"Processing failed: {e}")
            updated_document = (
                await self.processing_repository.update_pdf_processing_metadata(
                    ProcessedDocument(
                        document_id=document_id, sections=[], status="FAILED"
                    )
                )
            )
            return ProcessedDocument(**updated_document)
