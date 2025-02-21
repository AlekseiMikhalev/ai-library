from typing import Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from neo4j import AsyncGraphDatabase, GraphDatabase
from src.database.mongodb import get_mongodb
from src.database.neo4j import get_neo4j_async, get_neo4j_sync
from src.schemas.upload import ProcessedDocument, ProcessedDocumentMongoDB
from pymongo import ReturnDocument
from bson import ObjectId


class PDFProcessingRepository:
    def __init__(
        self,
        neo4j_async_driver: AsyncGraphDatabase = get_neo4j_async(),
        neo4j_sync_driver: GraphDatabase = get_neo4j_sync(),
        mongodb_client: AsyncIOMotorDatabase = get_mongodb(),
    ) -> None:
        self.mongodb_client = mongodb_client
        self.neo4j_async_driver = neo4j_async_driver
        self.neo4j_sync_driver = neo4j_sync_driver

    async def save_pdf_processing_metadata(
        self, document: ProcessedDocument
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
        self, document: ProcessedDocument
    ) -> ProcessedDocument | None:
        pdf_processing_collection = self.mongodb_client.get_collection("pdf_processing")
        document_dict = document.model_dump()
        document_dict["_id"] = ObjectId(document.document_id)
        updated_document = await pdf_processing_collection.find_one_and_update(
            {"_id": document_dict["_id"]},
            {"$set": document_dict},
            return_document=ReturnDocument.AFTER,
        )
        return updated_document

    async def get_processing_status(self, document_id: str) -> ProcessedDocument:
        collection = self.mongodb_client.get_collection("pdf_processing")
        return await collection.find_one({"_id": ObjectId(document_id)})
