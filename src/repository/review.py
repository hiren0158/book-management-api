from typing import Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from src.model.review import Review
from .base import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    def __init__(self, session: AsyncSession):
        super().__init__(Review, session)

    async def get_book_reviews(
        self,
        book_id: int,
        limit: int = 10,
        cursor: Optional[str] = None
    ):
        return await self.list(
            limit=limit,
            cursor=cursor,
            filters={"book_id": book_id}
        )

    async def get_user_reviews(
        self,
        user_id: int,
        limit: int = 10,
        cursor: Optional[str] = None
    ):
        return await self.list(
            limit=limit,
            cursor=cursor,
            filters={"user_id": user_id}
        )

    async def get_book_average_rating(self, book_id: int) -> Optional[float]:
        statement = select(func.avg(Review.rating)).where(Review.book_id == book_id)
        result = await self.session.execute(statement)
        avg_rating = result.scalar_one_or_none()
        return float(avg_rating) if avg_rating else None

    async def get_user_review_for_book(
        self,
        user_id: int,
        book_id: int
    ) -> Optional[Review]:
        statement = select(Review).where(
            Review.user_id == user_id,
            Review.book_id == book_id
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
