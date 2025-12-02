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

    model_config = ConfigDict(from_attributes=True)
