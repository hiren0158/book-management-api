from typing import Optional
from datetime import datetime
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.model.borrowing import Borrowing
from src.utils.datetime_utils import utcnow_naive
from .base import BaseRepository


class BorrowingRepository(BaseRepository[Borrowing]):
    def __init__(self, session: AsyncSession):
        super().__init__(Borrowing, session)

    async def get_user_borrowings(
        self, user_id: int, limit: int = 10, cursor: Optional[str] = None
    ):
        return await self.list(limit=limit, cursor=cursor, filters={"user_id": user_id})

    async def get_book_borrowings(
        self, book_id: int, limit: int = 10, cursor: Optional[str] = None
    ):
        return await self.list(limit=limit, cursor=cursor, filters={"book_id": book_id})

    async def get_active_borrowings(
        self, limit: int = 10, cursor: Optional[str] = None
    ):
        statement = select(Borrowing).where(Borrowing.returned_at.is_(None))

        if cursor:
            cursor_data = self._decode_cursor(cursor)
            created_at = datetime.fromisoformat(cursor_data["created_at"])
            cursor_id = cursor_data["id"]
            statement = statement.where(
                (Borrowing.created_at < created_at)
                | ((Borrowing.created_at == created_at) & (Borrowing.id < cursor_id))
            )

        statement = statement.order_by(
            Borrowing.created_at.desc(), Borrowing.id.desc()
        ).limit(limit + 1)

        result = await self.session.execute(statement)
        items = list(result.scalars().all())

        next_cursor = None
        if len(items) > limit:
            items = items[:limit]
            last_item = items[-1]
            next_cursor = self._encode_cursor(last_item.created_at, last_item.id)

        return items, next_cursor

    async def return_book(self, borrowing_id: int) -> Optional[Borrowing]:
        borrowing = await self.get_by_id(borrowing_id)
        if not borrowing or borrowing.returned_at:
            return None

        # Use timezone-naive datetime to match model's utcnow_naive()
        borrowing.returned_at = utcnow_naive()
        await self.session.commit()
        await self.session.refresh(borrowing)
        return borrowing
