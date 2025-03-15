import json
from functools import lru_cache
from pathlib import Path
from bson import ObjectId

from fastapi import APIRouter, File, HTTPException, UploadFile, BackgroundTasks
from src.repository.pdf_processing import PDFProcessingRepository
from src.schemas.upload import ProcessedBook, ProcessedBookMongoDB
import logging

from src.services.pdf_processing import PDFProcessorService

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
):
    document_id = str(ObjectId())

    try:
        file_location = str(UPLOAD_DIRECTORY_PDF / f"{document_id}.pdf")
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())

        background_tasks.add_task(perform_processing, file_location, document_id)

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
async def get_status(document_id: str):
    try:
        pdf_processing_repository = PDFProcessingRepository()
        processed_document_status = (
            await pdf_processing_repository.get_processing_status(document_id)
        )
        return ProcessedBookMongoDB(**processed_document_status)
    except Exception as e:
        logging.error(f"Processing failed: {e}")
        raise HTTPException(500, "PDF processing failed")


async def perform_processing(file_location: str, document_id: str):
    pdf_processor_service = PDFProcessorService()
    processed_document = await pdf_processor_service.process_pdf(
        file_location, document_id
    )
    processed_document.status = "COMPLETED"
    logging.info(f"Processing completed for document {document_id}")
    return processed_document
