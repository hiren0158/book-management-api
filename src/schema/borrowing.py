from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BorrowingCreate(BaseModel):
    user_id: int
    book_id: int
    due_date: datetime


class BorrowingRead(BaseModel):
    id: int
    user_id: int
    book_id: int
    borrowed_at: datetime
    due_date: datetime
    returned_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
