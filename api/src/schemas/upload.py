from pydantic import BaseModel, Field


class SectionParagraphData(BaseModel):
    level: int
    text: str
    page: int
    parent_text: str
    parent_chain: set


class SectionData(BaseModel):
    section_name: str
    section_paragraphs_data: list[SectionParagraphData]
    section_text: str
    section_text_embedding: list[float] = None
    cluster: str = None


class SectionsFeatures(BaseModel):
    sections_features: list[SectionData]


class ProcessedDocument(BaseModel):
    document_id: str = Field(...)
    sections: list[SectionData]
    status: str
