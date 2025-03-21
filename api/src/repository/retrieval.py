from motor.motor_asyncio import AsyncIOMotorDatabase
from neo4j import AsyncDriver
from src.schemas.retrieval import SearchResults, SearchResult


class RetrievalRepository:
    """Repository for retrieving data from MongoDB and Neo4j"""

    CYPHER_GET_BOOK_KNOWLEDGE_GRAPH = """
    MATCH (b: Book {id: $document_id})-[:HAS_SECTION]-(s: Section)<-[:MENTIONS]-(c: Concept)
    RETURN s, c
    """

    CYPHER_GET_LIBRARY_KNOWLEDGE_GRAPH = """
    MATCH (b: Book)-[:HAS_SECTION]-(s: Section)<-[:MENTIONS]-(c: Concept)
    RETURN s, c
    """

    CYPHER_GET_RELEVANT_BOOKS = """
    MATCH (b: Book) WHERE b.embedding IS NOT NULL
    WITH b, gds.alpha.similarity.cosine(b.embedding, $query_embedding) as similarity
    RETURN b.id, b.title, b.embedding, similarity
    ORDER BY similarity DESC
    SKIP $skip LIMIT $limit
    """

    def __init__(
        self, neo4j_async_driver: AsyncDriver, mongodb_client: AsyncIOMotorDatabase
    ):
        self.neo4j_async_driver = neo4j_async_driver
        self.mongodb_client = mongodb_client

    async def get_search_results(
        self, query_embedding: list[float], page: int = 1, per_page: int = 10
    ) -> SearchResults:
        """Search for documents matching a query"""
        async with self.neo4j_async_driver.session() as session:
            tx = await session.begin_transaction()
            result = await tx.run(
                self.CYPHER_GET_RELEVANT_BOOKS,
                query_embedding=query_embedding,
                skip=(page - 1) * per_page,
                limit=per_page,
            )
            return [
                SearchResult(
                    id=record["b.id"],
                    title=record["b.title"],
                    book=record["b.title"],
                    author=record["b.author"],
                    page=record["b.page"],
                    relevance=record["similarity"],
                    excerpt=record["b.excerpt"],
                )
                for record in result
            ]

    # TODO: implement these methods
    # async def get_book_knowledge_graph(self, document_id: str) -> list[Section]:
    #     """Get the knowledge graph of a book"""
    #     async with self.neo4j_async_driver.session() as session:
    #         tx = await session.begin_transaction()
    #         result = await tx.run(
    #             self.CYPHER_GET_BOOK_KNOWLEDGE_GRAPH, document_id=document_id
    #         )
    #         sections = []
    #         for record in result:
    #             sections.append(
    #                 Section(
    #                     id=record["s"]["id"],
    #                     title=record["s"]["title"],
    #                     concepts=[
    #                         Concept(id=concept["id"], name=concept["name"])
    #                         for concept in record["c"]
    #                     ],
    #                 )
    #             )
    #         return sections

    # async def get_library_knowledge_graph(self) -> List[Section]:
    #     """Get the knowledge graph of the whole library"""
    #     async with self.neo4j_async_driver.session() as session:
    #         tx = await session.begin_transaction()
    #         result = await tx.run(self.CYPHER_GET_LIBRARY_KNOWLEDGE_GRAPH)
    #         sections = []
    #         for record in result:
    #             sections.append(
    #                 Section(
    #                     id=record["s"]["id"],
    #                     title=record["s"]["title"],
    #                     concepts=[
    #                         Concept(id=concept["id"], name=concept["name"])
    #                         for concept in record["c"]
    #                     ],
    #                 )
    #             )
    #         return sections
