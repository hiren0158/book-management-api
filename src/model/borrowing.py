from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from src.utils.datetime_utils import utcnow_naive


class Borrowing(SQLModel, table=True):
    __tablename__ = "borrowings"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    book_id: int = Field(foreign_key="books.id")
    borrowed_at: datetime = Field(default_factory=utcnow_naive)
    due_date: datetime
    returned_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow_naive)

    user: "User" = Relationship(back_populates="borrowings")
    book: "Book" = Relationship(back_populates="borrowings")
