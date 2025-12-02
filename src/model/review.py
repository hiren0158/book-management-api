from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from src.utils.datetime_utils import utcnow_naive


class Review(SQLModel, table=True):
    __tablename__ = "reviews"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    book_id: int = Field(foreign_key="books.id")
    rating: int
    text: str
    created_at: datetime = Field(default_factory=utcnow_naive)

    user: "User" = Relationship(back_populates="reviews")
    book: "Book" = Relationship(back_populates="reviews")
