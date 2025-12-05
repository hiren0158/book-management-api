import pytest
from src.repository.book import BookRepository
from src.model.book import Book
from datetime import date


@pytest.mark.asyncio
async def test_create_book(db_session):
    book_repo = BookRepository(db_session)

    book_data = {
        "title": "New Book",
        "description": "A new book",
        "isbn": "978-1-234567-89-0",
        "author": "Author Name",
        "genre": "Mystery",
        "published_date": date(2021, 5, 15),
    }

    book = await book_repo.create(book_data)

    assert book.title == "New Book"
    assert book.isbn == "978-1-234567-89-0"
    assert book.id is not None


@pytest.mark.asyncio
async def test_get_book_by_id(db_session, test_book):
    book_repo = BookRepository(db_session)

    book = await book_repo.get_by_id(test_book.id)

    assert book is not None
    assert book.title == test_book.title
    assert book.isbn == test_book.isbn


@pytest.mark.asyncio
async def test_get_book_by_isbn(db_session, test_book):
    book_repo = BookRepository(db_session)

    book = await book_repo.get_by_isbn(test_book.isbn)

    assert book is not None
    assert book.id == test_book.id


@pytest.mark.asyncio
async def test_search_books_by_author(db_session):
    book_repo = BookRepository(db_session)

    for i in range(3):
        await book_repo.create(
            {
                "title": f"Book {i}",
                "description": f"Description {i}",
                "isbn": f"978-0-12345-67{i}-9",
                "author": "John Doe",
                "genre": "Fiction",
                "published_date": date(2020, 1, i + 1),
            }
        )

    books, cursor = await book_repo.search_books_fts(author="John Doe", limit=10)

    assert len(books) == 3
    assert all(b.author == "John Doe" for b in books)


@pytest.mark.asyncio
async def test_list_books_pagination(db_session):
    book_repo = BookRepository(db_session)

    for i in range(5):
        await book_repo.create(
            {
                "title": f"Book {i}",
                "description": f"Description {i}",
                "isbn": f"978-0-12345-6{i}0-9",
                "author": f"Author {i}",
                "genre": "Fiction",
                "published_date": date(2020, 1, 1),
            }
        )

    books, cursor = await book_repo.list(limit=2)

    assert len(books) == 2
    assert cursor is not None

    next_books, next_cursor = await book_repo.list(limit=2, cursor=cursor)
    assert len(next_books) == 2
    assert next_books[0].id != books[0].id


@pytest.mark.asyncio
async def test_update_book(db_session, test_book):
    book_repo = BookRepository(db_session)

    updated = await book_repo.update(test_book.id, {"title": "Updated Title"})

    assert updated.title == "Updated Title"
    assert updated.id == test_book.id


@pytest.mark.asyncio
async def test_delete_book(db_session, test_book):
    book_repo = BookRepository(db_session)

    result = await book_repo.delete(test_book.id)

    assert result is True

    deleted_book = await book_repo.get_by_id(test_book.id)
    assert deleted_book is None
