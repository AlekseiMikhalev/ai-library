import json

from llmsherpa.readers import LayoutPDFReader
from motor.motor_asyncio import AsyncIOMotorDatabase
from neo4j import AsyncDriver, Driver
from ollama import AsyncClient
from src.schemas.upload import ProcessedBook, ProcessedBookMongoDB
from functools import lru_cache
from pathlib import Path
from bson import ObjectId

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    BackgroundTasks,
)
from src.repository.pdf_processing import PDFProcessingRepository
import logging

from src.services.pdf_processing import PDFProcessorService
from src.utils.ollama_client import get_ollama_client
from src.utils.pdf_reader import get_pdf_reader
from src.database.mongodb import get_mongodb
from src.database.neo4j import get_neo4j_sync, get_neo4j_async

router = APIRouter(prefix="/v1")

# Documentation
BASE_DOCS_PATH = Path("src/docs")

# Directory to save neo4j files inside the Docker volume or locally
UPLOAD_DIRECTORY_NEO4J = Path("/neo4j_import")
UPLOAD_DIRECTORY_PDF = Path("src/pdf_uploads")


@lru_cache(maxsize=50)
@router.post(
    "/upload",
    tags=["features extraction"],
    response_model=ProcessedBookMongoDB,
    description=(BASE_DOCS_PATH / "upload_router.md").read_text(),
    response_description="Return upload and feature extraction results",
    responses=json.loads((BASE_DOCS_PATH / "examples_responses.json").read_text()),
)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(
        ..., example=json.loads((BASE_DOCS_PATH / "examples_requests.json").read_text())
    ),
    ollama_client: AsyncClient = Depends(get_ollama_client),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongodb),
    neo4j_sync_driver: Driver = Depends(get_neo4j_sync),
    neo4j_async_driver: AsyncDriver = Depends(get_neo4j_async),
    pdf_reader: LayoutPDFReader = Depends(get_pdf_reader),
):
    document_id = str(ObjectId())

    try:
        file_location = str(UPLOAD_DIRECTORY_PDF / f"{document_id}.pdf")
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())

        background_tasks.add_task(
            perform_processing,
            file_location,
            document_id,
            ollama_client,
            mongo_db,
            neo4j_sync_driver,
            neo4j_async_driver,
            pdf_reader,
        )

        return ProcessedBookMongoDB(
            document_id=document_id, sections=[], status="PROCESSING"
        )

    except Exception as e:
        logging.error(f"Upload failed: {e}")
        raise HTTPException(500, "PDF processing failed")


@router.get(
    "/status/{document_id}",
    response_model=ProcessedBookMongoDB,
    tags=["features extraction"],
)
async def get_status(
    document_id: str,
    neo4j_async_driver: AsyncDriver = Depends(get_neo4j_async),
    neo4j_sync_driver: Driver = Depends(get_neo4j_sync),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongodb),
):
    try:
        pdf_processing_repository = PDFProcessingRepository(
            neo4j_async_driver=neo4j_async_driver,
            neo4j_sync_driver=neo4j_sync_driver,
            mongodb_client=mongo_db,
        )
        processed_document_status = (
            await pdf_processing_repository.get_processing_status(document_id)
        )
        return ProcessedBookMongoDB(**processed_document_status)
    except Exception as e:
        logging.error(f"Processing failed: {e}")
        raise HTTPException(500, "PDF processing failed")


async def perform_processing(
    file_location: str,
    document_id: str,
    ollama_client: AsyncClient,
    mongo_db: AsyncIOMotorDatabase,
    neo4j_sync_driver: Driver,
    neo4j_async_driver: AsyncDriver,
    pdf_reader: LayoutPDFReader,
):
    pdf_processor_service = PDFProcessorService(
        ollama_client=ollama_client,
        mongo_db=mongo_db,
        neo4j_sync_driver=neo4j_sync_driver,
        neo4j_async_driver=neo4j_async_driver,
        pdf_reader=pdf_reader,
    )
    processed_document = await pdf_processor_service.process_pdf(
        file_location, document_id
    )
    processed_document.status = "COMPLETED"
    logging.info(f"Processing completed for document {document_id}")
    return processed_document
