from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.datetime_utils import utcnow_naive
from src.repository.borrowing import BorrowingRepository
from src.repository.book import BookRepository
from src.model.borrowing import Borrowing
from src.model.user import User
from src.schema.borrowing import BorrowingCreate


class BorrowingService:
    MAX_BOOKS_PER_USER = 1  # Changed from 5 to 1 - users can only borrow 1 book at a time
    DEFAULT_BORROW_DAYS = 14

    def __init__(self, session: AsyncSession):
        self.borrowing_repo = BorrowingRepository(session)
        self.book_repo = BookRepository(session)

    async def borrow_book(
        self,
        user_id: int,
        book_id: int,
        current_user: User
    ) -> Borrowing:
        if not hasattr(current_user, 'role') or current_user.role is None:
            raise ValueError("User role not loaded")
        
        if user_id != current_user.id and current_user.role.name != "Admin":
            raise ValueError("Cannot borrow books for other users")

        book = await self.book_repo.get_by_id(book_id)
        if not book:
            raise ValueError("Book not found")

        # Check if user has any active (unreturned) borrowings
        active_borrowings, _ = await self.borrowing_repo.get_user_borrowings(
            user_id=user_id,
            limit=100
        )
        active_count = sum(1 for b in active_borrowings if b.returned_at is None)

        if active_count >= self.MAX_BOOKS_PER_USER:
            raise ValueError("You already have a book borrowed. Please return it before borrowing another book")

        book_borrowings, _ = await self.borrowing_repo.get_book_borrowings(
            book_id=book_id,
            limit=10
        )
        for b in book_borrowings:
            if b.returned_at is None:
                raise ValueError("Book is currently borrowed")

        due_date = utcnow_naive() + timedelta(days=self.DEFAULT_BORROW_DAYS)
        
        borrowing_data = {
            "user_id": user_id,
            "book_id": book_id,
            "due_date": due_date
        }

        try:
            return await self.borrowing_repo.create(borrowing_data)
        except Exception as e:
            print(f"Error creating borrowing: {e}")
            raise ValueError(f"Failed to create borrowing: {str(e)}")

    async def return_book(
        self,
        borrowing_id: int,
        current_user: User
    ) -> Borrowing:
        borrowing = await self.borrowing_repo.get_by_id(borrowing_id)
        if not borrowing:
            raise ValueError("Borrowing not found")

        if borrowing.user_id != current_user.id and current_user.role.name not in ["Admin", "Librarian"]:
            raise ValueError("Permission denied")

        if borrowing.returned_at:
            raise ValueError("Book already returned")

        return await self.borrowing_repo.return_book(borrowing_id)

    async def get_borrowing(self, borrowing_id: int) -> Optional[Borrowing]:
        return await self.borrowing_repo.get_by_id(borrowing_id)

    async def get_user_borrowings(
        self,
        user_id: int,
        limit: int = 10,
        cursor: Optional[str] = None
    ):
        return await self.borrowing_repo.get_user_borrowings(
            user_id=user_id,
            limit=limit,
            cursor=cursor
        )

    async def get_book_borrowings(
        self,
        book_id: int,
        limit: int = 10,
        cursor: Optional[str] = None
    ):
        return await self.borrowing_repo.get_book_borrowings(
            book_id=book_id,
            limit=limit,
            cursor=cursor
        )

    async def get_active_borrowings(
        self,
        limit: int = 10,
        cursor: Optional[str] = None
    ):
        return await self.borrowing_repo.get_active_borrowings(
            limit=limit,
            cursor=cursor
        )

    async def get_overdue_borrowings(self, limit: int = 10, cursor: Optional[str] = None):
        active_borrowings, next_cursor = await self.borrowing_repo.get_active_borrowings(
            limit=limit,
            cursor=cursor
        )
        
        now = datetime.now(timezone.utc)
        overdue = [b for b in active_borrowings if b.due_date < now]
        
        return overdue, next_cursor
