from datetime import datetime
from pydantic import BaseModel, Field


class SectionParagraphData(BaseModel):
    level: int
    text: str
    page: int
    parent_text: str
    parent_chain: list


class Concepts(BaseModel):
    name: str
    embedding: list[float] = []


class SectionData(BaseModel):
    section_name: str
    section_paragraphs_data: list[SectionParagraphData]
    section_text: str
    concepts: list[Concepts] = []


class SectionsFeatures(BaseModel):
    sections_features: list[SectionData]


class ProcessedBook(BaseModel):
    document_id: str = Field(...)
    title: str = "Untitled"
    author: str = "Unknown"
    pages: int = 0
    published_date: datetime = None
    added_date: datetime = datetime.now()
    cover_image: str = ""
    description: str = ""
    concepts: list[str] = []
    sections: list[SectionData]
    status: str = ""


class ProcessedBookMongoDB(BaseModel):
    document_id: str = Field(...)
    status: str


class ExtractedConcepts(BaseModel):
    concepts: list[str]
