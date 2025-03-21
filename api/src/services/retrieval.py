import logging
from ollama import AsyncClient
import os
from src.schemas.retrieval import SearchResults
from src.repository.retrieval import RetrievalRepository
from neo4j import AsyncDriver
from motor.motor_asyncio import AsyncIOMotorDatabase


class RetrievalService:
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

    def __init__(
        self,
        ollama_client: AsyncClient,
        neo4j_async_driver: AsyncDriver,
        mongo_db: AsyncIOMotorDatabase,
    ):
        self.ollama_client = ollama_client
        self.retrieval_repository = RetrievalRepository(
            neo4j_async_driver=neo4j_async_driver, mongodb_client=mongo_db
        )

    async def _get_embedding(self, user_query: str) -> list[float]:
        embedding = await self.ollama_client.embed(
            model=self.EMBEDDING_MODEL, input=user_query
        )
        logging.info(f"Search Embedding: {embedding}")
        return embedding.embeddings[0] if embedding is not None else []

    async def get_search_results(self, user_query: str) -> SearchResults:
        # Convert query into embedding using ollama client
        query_embedding = await self._get_embedding(user_query)

        # Assuming you want to perform a search and get the knowledge graph
        results = await self.retrieval_repository.get_search_results(query_embedding)

        return SearchResults(sections=results)
