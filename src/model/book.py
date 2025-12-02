import os
from datetime import datetime, date

from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, Index, String, event
from sqlalchemy.dialects.postgresql import TSVECTOR
from src.utils.datetime_utils import utcnow_naive

if TYPE_CHECKING:
    from src.model.borrowing import Borrowing
    from src.model.review import Review


class Book(SQLModel, table=True):
    __tablename__ = "books"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: str
    isbn: str = Field(unique=True)
    author: str = Field(index=True)
    genre: str
    published_date: date
    created_at: datetime = Field(default_factory=utcnow_naive)
    
    if os.getenv("TESTING"):
        search_vector: Optional[str] = Field(
            default=None,
            sa_column=Column(String, nullable=True)
        )
    else:
        search_vector: Optional[str] = Field(
            default=None,
            sa_column=Column(
                TSVECTOR,
                nullable=True
            )
        )

    if not os.getenv("TESTING"):
        __table_args__ = (
            Index("ix_books_search_vector", "search_vector", postgresql_using="gin"),
            Index(
                "ix_books_title_trgm",
                "title",
                postgresql_using="gin",
                postgresql_ops={"title": "gin_trgm_ops"}
            ),
            Index(
                "ix_books_author_trgm",
                "author",
                postgresql_using="gin",
                postgresql_ops={"author": "gin_trgm_ops"}
            ),
        )
    else:
        __table_args__ = ()

    borrowings: list["Borrowing"] = Relationship(back_populates="book")
    reviews: list["Review"] = Relationship(back_populates="book")


def _compose_search_text(book: "Book") -> str:
    """Compose a lightweight search text for SQLite-based tests."""
    parts = [
        getattr(book, "title", "") or "",
        getattr(book, "description", "") or "",
        getattr(book, "author", "") or "",
        getattr(book, "genre", "") or "",
    ]
    return " ".join(filter(None, parts)).strip()


if os.getenv("TESTING"):
    @event.listens_for(Book, "before_insert")
    def _set_search_vector_before_insert(mapper, connection, target):  # type: ignore[unused-arg]
        target.search_vector = _compose_search_text(target)

    @event.listens_for(Book, "before_update")
    def _set_search_vector_before_update(mapper, connection, target):  # type: ignore[unused-arg]
        target.search_vector = _compose_search_text(target)
