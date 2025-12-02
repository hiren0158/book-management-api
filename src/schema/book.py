from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BookCreate(BaseModel):
    title: str
    description: str
    isbn: str
    author: str
    genre: str
    published_date: date


class BookUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    isbn: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    published_date: Optional[date] = None


class BookRead(BaseModel):
    id: int
    title: str
    description: str
    isbn: str
    author: str
    genre: str
    published_date: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
