from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class RagDocumentBase(BaseModel):
    filename: str


class RagDocumentCreate(RagDocumentBase):
    pass


class RagDocumentRead(RagDocumentBase):
    id: int
    chunk_count: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UploadResponse(BaseModel):
    document_id: int = Field(..., description="Unique document identifier")
    chunk_count: int = Field(..., description="Number of stored chunks")


class RetrievedChunk(BaseModel):
    text: str
    score: float
    doc_id: str
    chunk_index: int
    page_number: Optional[int] = Field(None, description="Page number in source document")
    section: Optional[str] = Field(None, description="Document section if detected")
    position: Optional[int] = Field(None, description="Absolute position in document")


class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    doc_id: Optional[int] = None  # Changed to int


class AskResponse(BaseModel):
    answer: str
    context: list[RetrievedChunk]