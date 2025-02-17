import json
from functools import lru_cache
from pathlib import Path
import uuid

from api.src.database.neo4j import get_neo4j_async, get_neo4j_sync
from api.src.database.mongodb import get_mongodb
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, BackgroundTasks
from api.src.repository.pdf_processing import PDFProcessingRepository
from api.src.schemas.upload import ProcessedDocument
from motor.motor_asyncio import AsyncIOMotorDatabase
from neo4j import AsyncGraphDatabase, GraphDatabase
import logging

from api.src.services.pdf_processing import PDFProcessorService

router = APIRouter(prefix="/v1")

# Documentation
BASE_DOCS_PATH = Path("/api.src/docs")
BASE_EXAMPLES_REQUESTS_PATH = Path("/api.src/docs/examples_requests")  # TODO
BASE_EXAMPLES_RESPONSES_PATH = Path("/api.src/docs/examples_responses")  # TODO

# Directory to save neo4j files inside the Docker volume or locally
UPLOAD_DIRECTORY_NEO4J = Path("/neo4j_import")
UPLOAD_DIRECTORY_PDF = Path("/pdf_uploads")


@lru_cache(maxsize=50)
@router.post(
    "/upload",
    tags=["features extraction"],
    response_model=ProcessedDocument,
    description=(BASE_DOCS_PATH / "upload.md").read_text(),
    response_description="Return upload and feature extraction results",
    responses=json.loads((BASE_EXAMPLES_RESPONSES_PATH / "upload.json").read_text()),
)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    neo4j_driver_async: AsyncGraphDatabase = Depends(get_neo4j_async),
    neo4j_driver_sync: GraphDatabase = Depends(get_neo4j_sync),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb),
):
    document_id = str(uuid.uuid4())

    try:
        file_location = UPLOAD_DIRECTORY_PDF / f"{document_id}.pdf"
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())

        pdf_processing_service = PDFProcessorService(
            mongodb, neo4j_driver_async, neo4j_driver_sync
        )

        background_tasks.add_task(
            pdf_processing_service.process_pdf, file_location, document_id
        )

        return ProcessedDocument(
            documentId=document_id, sections=[], status="PROCESSING"
        )

    except Exception as e:
        logging.error(f"Upload failed: {e}")
        raise HTTPException(500, "PDF processing failed")


@router.get("/status/{document_id}", response_model=ProcessedDocument)
async def get_status(
    document_id: str,
    neo4j_driver_async: AsyncGraphDatabase = Depends(get_neo4j_async),
    neo4j_driver_sync: GraphDatabase = Depends(get_neo4j_sync),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb),
):
    try:
        pdf_processing_repository = PDFProcessingRepository(
            mongodb, neo4j_driver_async, neo4j_driver_sync
        )
        processed_document_status = (
            await pdf_processing_repository.get_processing_status(document_id)
        )
        return ProcessedDocument(**processed_document_status)
    except Exception as e:
        logging.error(f"Processing failed: {e}")
        raise HTTPException(500, "PDF processing failed")
