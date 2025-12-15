from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ReviewCreate(BaseModel):
    user_id: int
    book_id: int
    rating: int = Field(ge=1, le=5)
    text: str


class ReviewRead(BaseModel):
    id: int
    user_id: int
    book_id: int
    rating: int
    text: str
    created_at: datetime
    user_name: str | None = None  # Reviewer's name
    user_email: str | None = None  # Reviewer's email (fallback)

    model_config = ConfigDict(from_attributes=True)
