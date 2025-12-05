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
    limit: int = Query(10, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    borrowing_service = BorrowingService(session)

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
    elif book_id:
        borrowings, next_cursor = await borrowing_service.get_book_borrowings(
            book_id=book_id, limit=limit, cursor=cursor
        )
    elif active_only:
        borrowings, next_cursor = await borrowing_service.get_active_borrowings(
            limit=limit, cursor=cursor
        )
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
