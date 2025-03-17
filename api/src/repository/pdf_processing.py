import logging
from typing import Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from neo4j import AsyncDriver, Driver
from neo4j._async.work.transaction import AsyncManagedTransaction
from src.database.mongodb import get_mongodb
from src.database.neo4j import get_neo4j_async, get_neo4j_sync
from src.schemas.upload import ProcessedBook, ProcessedBookMongoDB
from pymongo import ReturnDocument
from bson import ObjectId


class PDFProcessingRepository:
    def __init__(
        self,
        neo4j_async_driver: AsyncDriver = get_neo4j_async(),
        neo4j_sync_driver: Driver = get_neo4j_sync(),
        mongodb_client: AsyncIOMotorDatabase = get_mongodb(),
    ) -> None:
        self.mongodb_client = mongodb_client
        self.neo4j_async_driver = neo4j_async_driver
        self.neo4j_sync_driver = neo4j_sync_driver

    async def save_pdf_processing_metadata(
        self, document: ProcessedBook
    ) -> dict[str, Any] | None:
        pdf_processing_collection = self.mongodb_client.get_collection("pdf_processing")
        document_dict = document.model_dump()
        document_dict["_id"] = ObjectId(document.document_id)
        insert_result = await pdf_processing_collection.insert_one(document_dict)
        if insert_result.inserted_id:
            inserted_document = await pdf_processing_collection.find_one(
                {"_id": insert_result.inserted_id}
            )
            return inserted_document

        return None

    async def update_pdf_processing_metadata(
        self, document: ProcessedBook
    ) -> ProcessedBook | None:
        pdf_processing_collection = self.mongodb_client.get_collection("pdf_processing")
        document_dict = document.model_dump()
        document_dict["_id"] = ObjectId(document.document_id)
        updated_document = await pdf_processing_collection.find_one_and_update(
            {"_id": document_dict["_id"]},
            {"$set": document_dict},
            return_document=ReturnDocument.AFTER,
        )
        return updated_document

    async def get_processing_status(self, document_id: str) -> ProcessedBook:
        collection = self.mongodb_client.get_collection("pdf_processing")
        return await collection.find_one({"_id": ObjectId(document_id)})

    async def _neo4j_create_indexes(self, tx: AsyncManagedTransaction) -> None:
        """
        Create the necessary Neo4j indexes if they do not already exist.
        """
        # Full-text index for Paragraph nodes on the "text" property
        await tx.run(
            """
            CREATE FULLTEXT INDEX paragraphTextIndex IF NOT EXISTS
            FOR (n:Paragraph) ON EACH [n.text]
            OPTIONS {
                indexConfig: {
                    `fulltext.analyzer`: 'english',
                    `fulltext.eventually_consistent`: true
                }
            }
            """
        )

        # Fulltext index for Concept nodes on the "name" property
        await tx.run(
            """
            CREATE FULLTEXT INDEX conceptNameIndex IF NOT EXISTS
            FOR (n:Concept) ON EACH [n.name]
            OPTIONS {
                indexConfig: {
                    `fulltext.analyzer`: 'english',
                    `fulltext.eventually_consistent`: true
                }
            }
            """
        )

        # Vector index for Section nodes on the "section_concepts_embedding" property
        await tx.run(
            """
            CREATE VECTOR INDEX sectionEmbeddingIndex IF NOT EXISTS
            FOR (s:Section) ON (s.section_concepts_embedding)
            OPTIONS {
                indexConfig: {
                    `vector.dimensions`: 768,
                    `vector.similarity_function`: 'cosine'
                }
            }
            """
        )

        # Fulltext index for Section nodes on the "section_text" property
        await tx.run(
            """
            CREATE FULLTEXT INDEX sectionTextIndex IF NOT EXISTS
            FOR (s:Section) ON EACH [s.section_text]
            OPTIONS {
                indexConfig: {
                    `fulltext.analyzer`: 'english',
                    `fulltext.eventually_consistent`: true
                }
            }
            """
        )

    async def _neo4j_add_book_data(
        self, tx: AsyncManagedTransaction, processed_document: ProcessedBook
    ) -> None:
        """
        Merge the main Book node and related data (Sections, Paragraphs, Concepts, etc.) into Neo4j.
        """
        await tx.run(
            """
            MERGE (book:Book {name: $title, document_id: $document_id})
            SET book += $book_data
            
            WITH book
            CALL apoc.periodic.iterate(
            "UNWIND $sections AS section RETURN section",
            "
            MERGE (s:Section {name: section.section_name})
            SET s.section_text = section.section_text,
                s.section_concepts_embedding = section.section_concepts_embedding
            MERGE (book)-[:HAS_SECTION]->(s)

            WITH s, section
            UNWIND section.section_paragraphs_data AS paragraph
            CREATE (p:Paragraph)
            SET p = paragraph
            MERGE (s)-[:HAS_PARAGRAPH]->(p)

            WITH s, section
            UNWIND section.concepts AS section_concept
            MERGE (sc:Concept {name: section_concept})
            MERGE (s)-[:HAS_CONCEPT]->(sc)
            ",
            {batchSize: 100, iterateList: true, params: {sections: $sections}, logProgress: true, logBatchProgress: true}
            ) YIELD batches, total, errorMessages

            WITH book
            UNWIND $book_concepts AS book_concept
            MERGE (bc:Concept {name: book_concept})
            MERGE (book)-[:HAS_CONCEPT]->(bc)
            """,
            {
                "document_id": processed_document.document_id,
                "title": processed_document.title,
                "book_data": processed_document.model_dump(
                    exclude={"sections", "status", "id"}
                ),
                "sections": [
                    section.model_dump() for section in processed_document.sections
                ],
                "book_concepts": processed_document.concepts,
            },
        )

    async def store_features_in_neo4j(self, processed_document: ProcessedBook) -> None:
        """
        High-level function that creates required indexes and stores extracted features into Neo4j.
        """
        try:
            async with self.neo4j_async_driver.session() as session:
                # 1) Create indexes
                tx = await session.begin_transaction()
                await self._neo4j_create_indexes(tx)
                await tx.commit()

                # 2) Merge the graph data
                tx = await session.begin_transaction()
                await self._neo4j_add_book_data(tx, processed_document)
                await tx.commit()

            logging.info(
                f"Stored book {processed_document.document_id} into Neo4j successfully."
            )

        except Exception as e:
            logging.error(
                f"Error storing book {processed_document.document_id} into Neo4j: {e}"
            )
