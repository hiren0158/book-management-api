from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.review import ReviewRepository
from src.repository.book import BookRepository
from src.repository.borrowing import BorrowingRepository
from src.model.review import Review
from src.model.user import User
from src.schema.review import ReviewCreate


class ReviewService:
    def __init__(self, session: AsyncSession):
        self.review_repo = ReviewRepository(session)
        self.book_repo = BookRepository(session)
        self.borrowing_repo = BorrowingRepository(session)

    async def create_review(
        self,
        review_data: ReviewCreate,
        current_user: User
    ) -> Review:
        if review_data.user_id != current_user.id:
            raise ValueError("Cannot create review for other users")

        book = await self.book_repo.get_by_id(review_data.book_id)
        if not book:
            raise ValueError("Book not found")

        # Check if user has borrowed this book
        user_borrowings, _ = await self.borrowing_repo.get_user_borrowings(
            user_id=current_user.id,
            limit=100  # Get enough to check all borrowings
        )
        
        has_borrowed = any(
            borrowing.book_id == review_data.book_id 
            for borrowing in user_borrowings
        )
        
        if not has_borrowed:
            raise ValueError("You can only review books you have borrowed")

        existing_review = await self.review_repo.get_user_review_for_book(
            user_id=review_data.user_id,
            book_id=review_data.book_id
        )
        if existing_review:
            raise ValueError("You have already reviewed this book")

        review_dict = review_data.model_dump()
        return await self.review_repo.create(review_dict)

    async def get_review(self, review_id: int) -> Optional[Review]:
        return await self.review_repo.get_by_id(review_id)

    async def get_book_reviews(
        self,
        book_id: int,
        limit: int = 10,
        cursor: Optional[str] = None
    ):
        return await self.review_repo.get_book_reviews(
            book_id=book_id,
            limit=limit,
            cursor=cursor
        )

    async def get_user_reviews(
        self,
        user_id: int,
        limit: int = 10,
        cursor: Optional[str] = None
    ):
        return await self.review_repo.get_user_reviews(
            user_id=user_id,
            limit=limit,
            cursor=cursor
        )

    async def get_book_average_rating(self, book_id: int) -> Optional[float]:
        return await self.review_repo.get_book_average_rating(book_id)

    async def update_review(
        self,
        review_id: int,
        rating: Optional[int] = None,
        text: Optional[str] = None,
        current_user: User = None
    ) -> Review:
        review = await self.review_repo.get_by_id(review_id)
        if not review:
            raise ValueError("Review not found")

        if review.user_id != current_user.id:
            raise ValueError("Permission denied")

        update_dict = {}
        if rating is not None:
            update_dict["rating"] = rating
        if text is not None:
            update_dict["text"] = text

        updated_review = await self.review_repo.update(review_id, update_dict)
        return updated_review

    async def delete_review(self, review_id: int, current_user: User) -> bool:
        review = await self.review_repo.get_by_id(review_id)
        if not review:
            raise ValueError("Review not found")

        if review.user_id != current_user.id and current_user.role.name != "Admin":
            raise ValueError("Permission denied")

        return await self.review_repo.delete(review_id)
