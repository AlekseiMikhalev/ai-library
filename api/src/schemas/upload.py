from datetime import datetime
from pydantic import BaseModel, Field


class SectionParagraphData(BaseModel):
    level: int
    text: str
    page: int
    parent_text: str
    parent_chain: list


class SectionData(BaseModel):
    section_name: str
    section_paragraphs_data: list[SectionParagraphData]
    section_text: str
    section_text_embedding: list[float] = None
    cluster: str = None


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
