import pytest
from datetime import date, timedelta
from src.utils.datetime_utils import utcnow_naive


@pytest.mark.asyncio
async def test_borrow_book(client, test_book, auth_headers):
    """Member can borrow a book"""
    response = await client.post(
        "/borrowings",
        json={"book_id": test_book.id},
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["book_id"] == test_book.id
    assert data["returned_at"] is None
    assert "due_date" in data
    assert "borrowed_at" in data


@pytest.mark.asyncio
async def test_borrow_book_requires_auth(client, test_book):
    """Borrowing requires authentication"""
    response = await client.post(
        "/borrowings",
        json={"book_id": test_book.id}
    )
    
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_borrow_nonexistent_book(client, auth_headers):
    """Cannot borrow non-existent book"""
    response = await client.post(
        "/borrowings",
        json={"book_id": 99999},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_borrow_already_borrowed_book(client, test_book, auth_headers, db_session):
    """Cannot borrow already borrowed book"""
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": 1,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    response = await client.post(
        "/borrowings",
        json={"book_id": test_book.id},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "you already have a book borrowed" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_return_book(client, test_book, librarian_auth_headers, db_session):
    """Librarian can return a book"""
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    borrowing = await borrowing_repo.create({
        "user_id": 1,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    response = await client.patch(
        f"/borrowings/{borrowing.id}/return",
        headers=librarian_auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["returned_at"] is not None


@pytest.mark.asyncio
async def test_return_already_returned_book(client, test_book, librarian_auth_headers, db_session):
    """Cannot return already returned book"""
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    borrowing = await borrowing_repo.create({
        "user_id": 1,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14),
        "returned_at": utcnow_naive()
    })
    await db_session.commit()
    
    response = await client.patch(
        f"/borrowings/{borrowing.id}/return",
        headers=librarian_auth_headers
    )
    
    assert response.status_code == 400
    assert "already returned" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_user_borrowings(client, auth_headers, test_user, db_session):
    """User can list their own borrowings"""
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": test_user.id,
        "book_id": 1,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    response = await client.get(
        "/borrowings",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_borrowings_by_user_id(client, admin_auth_headers, test_user, db_session):
    """Admin can list borrowings by user_id"""
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": test_user.id,
        "book_id": 1,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    response = await client.get(
        f"/borrowings?user_id={test_user.id}",
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_borrowings_by_book_id(client, admin_auth_headers, test_book, db_session):
    """Admin can list borrowings by book_id"""
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": 1,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    response = await client.get(
        f"/borrowings?book_id={test_book.id}",
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_active_borrowings(client, admin_auth_headers, db_session):
    """Admin can list active borrowings"""
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": 1,
        "book_id": 1,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    response = await client.get(
        "/borrowings?active_only=true",
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_borrowing_by_id(client, auth_headers, test_user, db_session):
    """User can get their own borrowing"""
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    borrowing = await borrowing_repo.create({
        "user_id": test_user.id,
        "book_id": 1,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    response = await client.get(
        f"/borrowings/{borrowing.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == borrowing.id


@pytest.mark.asyncio
async def test_get_other_user_borrowing_denied(client, auth_headers, db_session):
    """User cannot get other user's borrowing"""
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    borrowing = await borrowing_repo.create({
        "user_id": 999,  # Different user
        "book_id": 1,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    response = await client.get(
        f"/borrowings/{borrowing.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_max_books_limit(client, auth_headers, db_session):
    """User cannot borrow more than MAX_BOOKS_PER_USER (5)"""
    from src.repository.book import BookRepository
    from src.repository.borrowing import BorrowingRepository
    
    book_repo = BookRepository(db_session)
    borrowing_repo = BorrowingRepository(db_session)
    
    # Create 5 books and borrow them
    for i in range(5):
        book = await book_repo.create({
            "title": f"Book {i}",
            "description": f"Description {i}",
            "isbn": f"978-0-88888-8{i}0-9",
            "author": f"Author {i}",
            "genre": "Fiction",
            "published_date": date(2023, 1, 1)
        })
        
        await borrowing_repo.create({
            "user_id": 1,
            "book_id": book.id,
            "due_date": utcnow_naive() + timedelta(days=14)
        })
    
    # Try to borrow 6th book
    new_book = await book_repo.create({
        "title": "Extra Book",
        "description": "Extra",
        "isbn": "978-0-88888-999-9",
        "author": "Extra Author",
        "genre": "Fiction",
        "published_date": date(2023, 1, 1)
    })
    
    response = await client.post(
        "/borrowings",
        json={"book_id": new_book.id},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "You already have a book borrowed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_borrow_after_return(client, test_book, auth_headers, librarian_auth_headers, db_session):
    """User can borrow a book after it's returned"""
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    
    # Create and return a borrowing
    borrowing = await borrowing_repo.create({
        "user_id": 1,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    # Return it
    await client.patch(
        f"/borrowings/{borrowing.id}/return",
        headers=librarian_auth_headers
    )
    
    # Now borrow it again
    response = await client.post(
        "/borrowings",
        json={"book_id": test_book.id},
        headers=auth_headers
    )
    
    assert response.status_code == 201
