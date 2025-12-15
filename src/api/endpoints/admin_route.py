from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.core.database import get_session
from src.model.user import User
from src.model.book import Book
from src.model.borrowing import Borrowing
from src.model.review import Review
from src.api.dependencies import require_roles

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats")
async def get_stats(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("Admin", "Librarian")),
):
    """Get system statistics for admin dashboard"""

    # Total users
    total_users = await session.execute(select(func.count(User.id)))
    total_users_count = total_users.scalar()

    # Total books
    total_books = await session.execute(select(func.count(Book.id)))
    total_books_count = total_books.scalar()

    # Total borrowings
    total_borrowings = await session.execute(select(func.count(Borrowing.id)))
    total_borrowings_count = total_borrowings.scalar()

    # Active borrowings (not returned)
    active_borrowings = await session.execute(
        select(func.count(Borrowing.id)).where(Borrowing.returned_at.is_(None))
    )
    active_borrowings_count = active_borrowings.scalar()

    # Total reviews
    total_reviews = await session.execute(select(func.count(Review.id)))
    total_reviews_count = total_reviews.scalar()

    # Average rating
    avg_rating = await session.execute(select(func.avg(Review.rating)))
    avg_rating_value = avg_rating.scalar() or 0

    return {
        "total_users": total_users_count,
        "total_books": total_books_count,
        "total_borrowings": total_borrowings_count,
        "active_borrowings": active_borrowings_count,
        "total_reviews": total_reviews_count,
        "average_rating": round(float(avg_rating_value), 2),
    }
