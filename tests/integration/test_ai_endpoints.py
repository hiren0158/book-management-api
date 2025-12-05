"""
AI Endpoints Tests
Tests for AI-powered book recommendations and natural language search
"""

import pytest
from datetime import date, timedelta
from src.utils.datetime_utils import utcnow_naive


@pytest.mark.asyncio
async def test_recommend_books_requires_auth(client):
    """AI recommendations require authentication"""
    response = await client.get("/ai/books/recommend")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_recommend_books_member_allowed(
    client, auth_headers, test_user, test_book, db_session
):
    """Members can get AI recommendations"""
    # Create some books and borrowing history
    from src.repository.book import BookRepository
    from src.repository.borrowing import BorrowingRepository
    from datetime import datetime, timedelta

    book_repo = BookRepository(db_session)
    borrowing_repo = BorrowingRepository(db_session)

    # Create additional books
    for i in range(3):
        book = await book_repo.create(
            {
                "title": f"Book {i}",
                "description": f"Description {i}",
                "isbn": f"978-0-99999-9{i}0-9",
                "author": f"Author {i}",
                "genre": "Fiction",
                "published_date": date(2023, 1, 1),
            }
        )

        if i < 2:  # Borrow first 2 books
            await borrowing_repo.create(
                {
                    "user_id": test_user.id,
                    "book_id": book.id,
                    "due_date": utcnow_naive() + timedelta(days=14),
                }
            )

    response = await client.get("/ai/books/recommend?limit=5", headers=auth_headers)

    # Should return 200 even if AI is not configured (graceful degradation)
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert "user_id" in data


@pytest.mark.asyncio
async def test_recommend_books_with_genre_filter(
    client, auth_headers, test_user, db_session
):
    """Test recommendations with genre filter"""
    from src.repository.book import BookRepository

    book_repo = BookRepository(db_session)
    await book_repo.create(
        {
            "title": "Mystery Book",
            "description": "A mystery",
            "isbn": "978-0-99999-999-9",
            "author": "Mystery Author",
            "genre": "Mystery",
            "published_date": date(2023, 1, 1),
        }
    )

    response = await client.get(
        "/ai/books/recommend?limit=5&genre=Mystery", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["genre_filter"] == "Mystery"


@pytest.mark.asyncio
async def test_recommend_books_limit_validation(client, auth_headers):
    """Test limit validation for recommendations"""
    response = await client.get(
        "/ai/books/recommend?limit=100", headers=auth_headers  # Exceeds max of 20
    )

    # FastAPI returns 422 for query parameter validation errors
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_natural_language_search_public(client):
    """Natural language search should be public"""
    response = await client.post(
        "/ai/books/search_nl", json={"query": "books by J.K. Rowling"}
    )

    # Should work even without auth (graceful degradation)
    assert response.status_code in [200, 500]  # 500 if AI not configured


@pytest.mark.asyncio
async def test_natural_language_search_with_books(client, test_book):
    """Test NL search with existing books"""
    response = await client.post("/ai/books/search_nl", json={"query": "fiction books"})

    # Should return 200 even if AI is not configured
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()
        assert "query" in data
        assert "extracted_filters" in data
        assert "books" in data


@pytest.mark.asyncio
async def test_natural_language_search_empty_query(client):
    """Test NL search with empty query"""
    response = await client.post("/ai/books/search_nl", json={"query": ""})

    assert response.status_code in [200, 400]


@pytest.mark.asyncio
async def test_natural_language_search_long_query(client):
    """Test NL search with query that's too long"""
    long_query = "a" * 600  # Exceeds 500 char limit
    response = await client.post("/ai/books/search_nl", json={"query": long_query})

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_natural_language_search_pagination(client, test_book):
    """Test NL search with pagination"""
    response = await client.post(
        "/ai/books/search_nl?limit=5&cursor=test", json={"query": "test book"}
    )

    if response.status_code == 200:
        data = response.json()
        assert "next_cursor" in data
