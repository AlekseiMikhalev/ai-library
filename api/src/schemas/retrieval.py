from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str


class SearchResult(BaseModel):
    id: str
    title: str
    book: str
    author: str
    page: int
    relevance: float
    excerpt: str


class SearchResults(BaseModel):
    results: list[SearchResult]
