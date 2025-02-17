from typing import Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from neo4j import AsyncGraphDatabase, GraphDatabase
from api.src.schemas.upload import ProcessedDocument
from pymongo import ReturnDocument


class PDFProcessingRepository:
    def __init__(
        self,
        mongodb_client: AsyncIOMotorDatabase,
        neo4j_async_driver: AsyncGraphDatabase,
        neo4j_sync_driver: GraphDatabase,
    ) -> None:
        self.mongodb_client = mongodb_client
        self.neo4j_async_driver = neo4j_async_driver
        self.neo4j_sync_driver = neo4j_sync_driver
        return None

    async def save_pdf_processing_metadata(
        self, document: ProcessedDocument
    ) -> dict[str, Any] | None:
        pdf_processing_collection = self.mongodb_client.get_collection("pdf_processing")
        document_dict = document.model_dump()
        if "document_id" in document_dict:
            updated_document = await pdf_processing_collection.find_one_and_update(
                {"document_id": document_dict["document_id"]},
                {"$set": document_dict},
                return_document=ReturnDocument.AFTER,
            )
            return updated_document
        else:
            insert_result = await pdf_processing_collection.insert_one(document_dict)
            if insert_result.inserted_id:
                inserted_document = await pdf_processing_collection.find_one(
                    {"_id": insert_result.inserted_id}
                )
                return inserted_document

        return None

    async def update_pdf_processing_metadata(
        self, document: ProcessedDocument
    ) -> dict[str, Any] | None:
        pdf_processing_collection = self.mongodb_client.get_collection("pdf_processing")
        document_dict = document.model_dump()
        updated_document = await pdf_processing_collection.find_one_and_update(
            {"document_id": document_dict["document_id"]},
            {"$set": document_dict},
            return_document=ReturnDocument.AFTER,
        )
        return updated_document

    async def get_processing_status(self, document_id: str) -> ProcessedDocument:
        document_id = ObjectId(document_id)
        collection = self.mongodb_client.get_collection("pdf_processing")
        return await collection.find_one({"_id": document_id})
