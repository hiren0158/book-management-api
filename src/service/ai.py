from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.user import UserRepository
from src.repository.book import BookRepository
from src.repository.borrowing import BorrowingRepository
from src.repository.review import ReviewRepository
from src.tools.ai_tools import recommend_books_ai, nl_to_filters


class AIService:
    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)
        self.book_repo = BookRepository(session)
        self.borrowing_repo = BorrowingRepository(session)
        self.review_repo = ReviewRepository(session)

    async def recommend_books(
        self, 
        user_id: int, 
        genre: Optional[str] = None, 
        limit: int = 5
    ) -> list[dict]:
        if limit < 1 or limit > 20:
            raise ValueError("Limit must be between 1 and 20")
        
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        borrowings, _ = await self.borrowing_repo.get_user_borrowings(user_id, limit=20)
        reviews, _ = await self.review_repo.get_user_reviews(user_id, limit=20)

        user_preferences = {
            "borrowed_books": [],
            "reviewed_books": []
        }

        for borrowing in borrowings:
            book = await self.book_repo.get_by_id(borrowing.book_id)
            if book:
                user_preferences["borrowed_books"].append({
                    "title": book.title,
                    "author": book.author,
                    "genre": book.genre
                })

        for review in reviews:
            book = await self.book_repo.get_by_id(review.book_id)
            if book:
                user_preferences["reviewed_books"].append({
                    "title": book.title,
                    "author": book.author,
                    "genre": book.genre,
                    "rating": review.rating
                })

        all_books, _ = await self.book_repo.list(limit=100)
        
        available_books = [
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "genre": b.genre
            }
            for b in all_books
        ]

        recommended_ids = await recommend_books_ai(
            user_preferences=user_preferences,
            available_books=available_books,
            genre=genre,
            limit=limit
        )
        
        recommendations = []
        for book_id in recommended_ids:
            if not isinstance(book_id, int) or book_id < 1:
                continue
                
            book = await self.book_repo.get_by_id(book_id)
            if book:
                recommendations.append({
                    "id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "genre": book.genre,
                    "isbn": book.isbn
                })

        return recommendations

    async def nl_to_filters_validated(self, query: str) -> dict:
        if not query or not isinstance(query, str):
            return {
                "author": None,
                "genre": None,
                "published_year": None,
                "search_query": None
            }
        
        if len(query) > 500:
            raise ValueError("Query too long (max 500 characters)")

        # Fetch current genres and authors from database
        available_genres = await self.book_repo.get_all_genres()
        available_authors = await self.book_repo.get_all_authors()
        
        filters = await nl_to_filters(
            query.strip(), 
            available_genres=available_genres,
            available_authors=available_authors
        )
        
        return filters
