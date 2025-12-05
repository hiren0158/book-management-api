from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from src.core.database import get_session
from src.service.review import ReviewService
from src.schema.review import ReviewCreate, ReviewRead
from src.model.user import User
from src.api.dependencies import get_current_user, require_roles

router = APIRouter(tags=["Reviews"])


class CreateReviewRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    text: str


@router.post(
    "/books/{book_id}/reviews",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    book_id: int,
    review_data: CreateReviewRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("Member")),
):
    review_service = ReviewService(session)

    review_create = ReviewCreate(
        user_id=current_user.id,
        book_id=book_id,
        rating=review_data.rating,
        text=review_data.text,
    )

    try:
        review = await review_service.create_review(review_create, current_user)
        return review
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/books/{book_id}/reviews", response_model=list[ReviewRead])
async def get_book_reviews(
    book_id: int,
    limit: int = Query(10, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    review_service = ReviewService(session)

    reviews, next_cursor = await review_service.get_book_reviews(
        book_id=book_id, limit=limit, cursor=cursor
    )

    return reviews


@router.get("/books/{book_id}/reviews/rating")
async def get_book_rating(book_id: int, session: AsyncSession = Depends(get_session)):
    review_service = ReviewService(session)

    avg_rating = await review_service.get_book_average_rating(book_id)

    return {
        "book_id": book_id,
        "average_rating": avg_rating,
        "rating": round(avg_rating, 2) if avg_rating else None,
    }


@router.get("/users/{user_id}/reviews", response_model=list[ReviewRead])
async def get_user_reviews(
    user_id: int,
    limit: int = Query(10, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.id and current_user.role.name not in [
        "Admin",
        "Librarian",
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    review_service = ReviewService(session)

    reviews, next_cursor = await review_service.get_user_reviews(
        user_id=user_id, limit=limit, cursor=cursor
    )

    return reviews


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    review_service = ReviewService(session)

    try:
        await review_service.delete_review(review_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
