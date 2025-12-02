from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.book import BookRepository
from src.model.book import Book
from src.model.user import User
from src.schema.book import BookCreate, BookUpdate


class BookService:
    ROLE_ADMIN = "Admin"
    ROLE_LIBRARIAN = "Librarian"

    def __init__(self, session: AsyncSession):
        self.book_repo = BookRepository(session)

    async def create_book(self, book_data: BookCreate, current_user: User) -> Book:
        if current_user.role.name not in [self.ROLE_ADMIN, self.ROLE_LIBRARIAN]:
            raise ValueError("Only Admin or Librarian can create books")

        existing_book = await self.book_repo.get_by_isbn(book_data.isbn)
        if existing_book:
            raise ValueError("Book with this ISBN already exists")

        book_dict = book_data.model_dump()
        return await self.book_repo.create(book_dict)

    async def get_book(self, book_id: int) -> Optional[Book]:
        return await self.book_repo.get_by_id(book_id)

    async def get_book_by_isbn(self, isbn: str) -> Optional[Book]:
        return await self.book_repo.get_by_isbn(isbn)

    async def list_books(self, limit: int = 10, cursor: Optional[str] = None, sort_order: str = "desc"):
        return await self.book_repo.list(limit=limit, cursor=cursor, sort_order=sort_order)

    # Traditional search for GET /books endpoint
    async def search_books_fts(
        self,
        query: Optional[str] = None,
        author: Optional[str] = None,
        genre: Optional[str] = None,
        published_year: Optional[int] = None,
        limit: int = 10,
        cursor: Optional[str] = None,
        sort_order: str = "desc"
    ):
        """FTS + Trigram search for traditional /books endpoint."""
        return await self.book_repo.search_books_fts(
            query=query,
            author=author,
            genre=genre,
            published_year=published_year,
            limit=limit,
            cursor=cursor,
            sort_order=sort_order
        )
    
    # AI-driven search for POST /ai/books/search_nl endpoint
    async def search_books_ilike(
        self,
        query: Optional[str] = None,
        author: Optional[str] = None,
        genre: Optional[str] = None,
        published_year: Optional[int] = None,
        limit: int = 10,
        cursor: Optional[str] = None,
        sort_order: str = "desc"
    ):
        """ILIKE-only search for AI natural language endpoint."""
        return await self.book_repo.search_books_ilike(
            query=query,
            author=author,
            genre=genre,
            published_year=published_year,
            limit=limit,
            cursor=cursor,
            sort_order=sort_order
        )

    async def update_book(
        self,
        book_id: int,
        book_data: BookUpdate,
        current_user: User
    ) -> Book:
        if current_user.role.name not in [self.ROLE_ADMIN, self.ROLE_LIBRARIAN]:
            raise ValueError("Only Admin or Librarian can update books")

        update_dict = book_data.model_dump(exclude_unset=True)
        
        if "isbn" in update_dict:
            existing_book = await self.book_repo.get_by_isbn(update_dict["isbn"])
            if existing_book and existing_book.id != book_id:
                raise ValueError("Book with this ISBN already exists")

        book = await self.book_repo.update(book_id, update_dict)
        if not book:
            raise ValueError("Book not found")

        return book

    async def delete_book(self, book_id: int, current_user: User) -> bool:
        if current_user.role.name not in [self.ROLE_ADMIN, self.ROLE_LIBRARIAN]:
            raise ValueError("Only Admin or Librarian can delete books")

        return await self.book_repo.delete(book_id)
