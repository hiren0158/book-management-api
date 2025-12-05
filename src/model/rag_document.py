from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from src.model.user import User


class RagDocument(SQLModel, table=True):
    """Model for storing RAG documents with ownership tracking."""

    __tablename__ = "rag_documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(index=True)
    chunk_count: int
    user_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    user: Optional[User] = Relationship(back_populates="rag_documents")
