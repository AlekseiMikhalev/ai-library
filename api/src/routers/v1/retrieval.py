import json

from motor.motor_asyncio import AsyncIOMotorDatabase
from neo4j import AsyncDriver
from ollama import AsyncClient
from src.schemas.retrieval import QueryRequest, SearchResults
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from src.repository.retrieval import RetrievalRepository
from src.services.retrieval import RetrievalService

from src.utils.ollama_client import get_ollama_client
from src.database.mongodb import get_mongodb
from src.database.neo4j import get_neo4j_async

router = APIRouter(prefix="/v1")

# Documentation
BASE_DOCS_PATH = Path("src/docs")


@lru_cache(maxsize=50)
@router.post(
    "/search-concept",
    tags=["retrieval"],
    response_model=SearchResults,
    description=(BASE_DOCS_PATH / "retrieval_router.md").read_text(),
    response_description="Return upload and feature extraction results",
    responses=json.loads((BASE_DOCS_PATH / "examples_responses.json").read_text()),
)
async def search_concept(
    query_request: QueryRequest,
    ollama_client: AsyncClient = Depends(get_ollama_client),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongodb),
    neo4j_async_driver: AsyncDriver = Depends(get_neo4j_async),
):
    try:
        retrieval_service = RetrievalService(
            ollama_client=ollama_client,
            neo4j_async_driver=neo4j_async_driver,
            mongo_db=mongo_db,
        )
        results = await retrieval_service.get_search_results(query_request.query)
        return SearchResults(**results.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
