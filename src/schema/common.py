from typing import Optional, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class Pagination(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)
    next_cursor: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class CursorPage(BaseModel, Generic[T]):
    data: list[T]
    next_cursor: Optional[str] = None
    has_next_page: bool


class BookFilters(BaseModel):
    author: Optional[str] = None
    genre: Optional[str] = None
    published_year: Optional[int] = None
    q: Optional[str] = None
