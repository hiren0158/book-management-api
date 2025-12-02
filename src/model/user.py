from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from src.utils.datetime_utils import utcnow_naive


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    hashed_password: str
    role_id: int = Field(foreign_key="roles.id")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utcnow_naive)

    role: "Role" = Relationship(back_populates="users")
    borrowings: list["Borrowing"] = Relationship(back_populates="user")
    reviews: list["Review"] = Relationship(back_populates="user")
    rag_documents: list["RagDocument"] = Relationship(back_populates="user")
