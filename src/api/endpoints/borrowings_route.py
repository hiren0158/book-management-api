from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from src.core.database import get_session
from src.service.borrowing import BorrowingService
from src.schema.borrowing import BorrowingCreate, BorrowingRead
from src.model.user import User
from src.api.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/borrowings", tags=["Borrowings"])


class BorrowRequest(BaseModel):
    book_id: int


@router.post("", response_model=BorrowingRead, status_code=status.HTTP_201_CREATED)
async def borrow_book(
    borrow_data: BorrowRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("Member")),
):
    borrowing_service = BorrowingService(session)

    try:
        borrowing = await borrowing_service.borrow_book(
            user_id=current_user.id,
            book_id=borrow_data.book_id,
            current_user=current_user,
        )
        return borrowing
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log internal errors for debugging
        print(f"Internal error while borrowing book: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the borrowing request",
        )


@router.patch("/{borrowing_id}/return", response_model=BorrowingRead)
async def return_book(
    borrowing_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("Librarian", "Admin")),
):
    borrowing_service = BorrowingService(session)

    try:
        borrowing = await borrowing_service.return_book(borrowing_id, current_user)
        return borrowing
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[BorrowingRead])
async def list_borrowings(
    user_id: Optional[int] = Query(None),
    book_id: Optional[int] = Query(None),
    active_only: bool = Query(False),
    all: bool = Query(False, description="Get all borrowings (Admin/Librarian only)"),
    limit: int = Query(10, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    borrowing_service = BorrowingService(session)

    # Admin wants ALL borrowings (all users, all statuses)
    if all:
        if current_user.role.name not in ["Admin", "Librarian"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Only admins can view all borrowings"
            )
        # Get all borrowings without filtering
        from sqlalchemy import select
        from src.model.borrowing import Borrowing
        
        result = await session.execute(
            select(Borrowing).order_by(Borrowing.borrowed_at.desc()).limit(limit)
        )
        borrowings = result.scalars().all()
        return borrowings
    
    # Filter by specific user
    if user_id:
        if user_id != current_user.id and current_user.role.name not in [
            "Admin",
            "Librarian",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
            )
        borrowings, next_cursor = await borrowing_service.get_user_borrowings(
            user_id=user_id, limit=limit, cursor=cursor
        )
    # Filter by book
    elif book_id:
        borrowings, next_cursor = await borrowing_service.get_book_borrowings(
            book_id=book_id, limit=limit, cursor=cursor
        )
    # Active borrowings only
    elif active_only:
        borrowings, next_cursor = await borrowing_service.get_active_borrowings(
            limit=limit, cursor=cursor
        )
    # Default: current user's borrowings
    else:
        borrowings, next_cursor = await borrowing_service.get_user_borrowings(
            user_id=current_user.id, limit=limit, cursor=cursor
        )

    return borrowings


@router.get("/{borrowing_id}", response_model=BorrowingRead)
async def get_borrowing(
    borrowing_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    borrowing_service = BorrowingService(session)
    borrowing = await borrowing_service.get_borrowing(borrowing_id)

    if not borrowing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Borrowing not found"
        )

    if borrowing.user_id != current_user.id and current_user.role.name not in [
        "Admin",
        "Librarian",
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    return borrowing
