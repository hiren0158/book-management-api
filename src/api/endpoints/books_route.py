from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_session
from src.service.book import BookService
from src.schema.book import BookCreate, BookUpdate, BookRead
from src.model.user import User
from src.api.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/books", tags=["Books"])

from src.schema.common import CursorPage

@router.get("", response_model=CursorPage[BookRead])
async def list_books(
    search: Optional[str] = Query(None, description="Search books by title, author, genre, description, or ISBN"),
    author: Optional[str] = Query(None, description="Filter by author name"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    published_year: Optional[int] = Query(None, description="Filter by publication year"),
    limit: int = Query(10, ge=1, le=100, description="Number of results per page"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order: asc (oldest first) or desc (newest first)"),
    session: AsyncSession = Depends(get_session)
):
    book_service = BookService(session)

    try:
        if any([author, genre, published_year, search]):
            books, next_cursor = await book_service.search_books_fts(
                query=search,
                author=author,
                genre=genre,
                published_year=published_year,
                limit=limit,
                cursor=cursor,
                sort_order=sort_order
            )
        else:
            books, next_cursor = await book_service.list_books(
                limit=limit, 
                cursor=cursor,
                sort_order=sort_order
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    return {
        "data": books,
        "next_cursor": next_cursor,
        "has_next_page": next_cursor is not None
    }


@router.get("/{book_id}", response_model=BookRead)
async def get_book(
    book_id: int,
    session: AsyncSession = Depends(get_session)
):
    book_service = BookService(session)
    book = await book_service.get_book(book_id)
    
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    return book


@router.post("", response_model=BookRead, status_code=status.HTTP_201_CREATED)
async def create_book(
    book_data: BookCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("Admin", "Librarian"))
):
    book_service = BookService(session)
    
    try:
        book = await book_service.create_book(book_data, current_user)
        return book
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{book_id}", response_model=BookRead)
async def update_book(
    book_id: int,
    book_data: BookUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("Admin", "Librarian"))
):
    book_service = BookService(session)
    
    try:
        book = await book_service.update_book(book_id, book_data, current_user)
        return book
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("Admin"))
):
    book_service = BookService(session)
    
    success = await book_service.delete_book(book_id, current_user)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
