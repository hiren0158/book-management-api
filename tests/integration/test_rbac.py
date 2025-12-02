"""
Comprehensive RBAC (Role-Based Access Control) Tests
Tests all role permissions across all endpoints
"""
import pytest
from datetime import date, timedelta
from src.utils.datetime_utils import utcnow_naive


# ==================== BOOKS ENDPOINTS RBAC ====================

@pytest.mark.asyncio
async def test_create_book_member_denied(client, auth_headers):
    """Members cannot create books"""
    response = await client.post(
        "/books",
        json={
            "title": "Member Book",
            "description": "Description",
            "isbn": "978-1-111111-11-1",
            "author": "Author",
            "genre": "Fiction",
            "published_date": "2021-01-01"
        },
        headers=auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_book_admin_allowed(client, admin_auth_headers):
    """Admins can create books"""
    response = await client.post(
        "/books",
        json={
            "title": "Admin Book",
            "description": "Description",
            "isbn": "978-1-111111-11-2",
            "author": "Author",
            "genre": "Fiction",
            "published_date": "2021-01-01"
        },
        headers=admin_auth_headers
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_book_librarian_allowed(client, librarian_auth_headers):
    """Librarians can create books"""
    response = await client.post(
        "/books",
        json={
            "title": "Librarian Book",
            "description": "Description",
            "isbn": "978-1-111111-11-3",
            "author": "Author",
            "genre": "Fiction",
            "published_date": "2021-01-01"
        },
        headers=librarian_auth_headers
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_update_book_member_denied(client, test_book, auth_headers):
    """Members cannot update books"""
    response = await client.put(
        f"/books/{test_book.id}",
        json={"title": "Updated"},
        headers=auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_book_admin_allowed(client, test_book, admin_auth_headers):
    """Admins can update books"""
    response = await client.put(
        f"/books/{test_book.id}",
        json={"title": "Admin Updated"},
        headers=admin_auth_headers
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_book_librarian_allowed(client, test_book, librarian_auth_headers):
    """Librarians can update books"""
    response = await client.put(
        f"/books/{test_book.id}",
        json={"title": "Librarian Updated"},
        headers=librarian_auth_headers
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_book_member_denied(client, test_book, auth_headers):
    """Members cannot delete books"""
    response = await client.delete(
        f"/books/{test_book.id}",
        headers=auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_book_librarian_denied(client, test_book, librarian_auth_headers):
    """Librarians cannot delete books"""
    response = await client.delete(
        f"/books/{test_book.id}",
        headers=librarian_auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_book_admin_allowed(client, test_book, admin_auth_headers):
    """Only Admins can delete books"""
    response = await client.delete(
        f"/books/{test_book.id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 204


# ==================== BORROWINGS ENDPOINTS RBAC ====================

@pytest.mark.asyncio
async def test_borrow_book_member_allowed(client, test_book, auth_headers):
    """Only Members can borrow books"""
    response = await client.post(
        "/borrowings",
        json={"book_id": test_book.id},
        headers=auth_headers
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_borrow_book_admin_denied(client, test_book, admin_auth_headers):
    """Admins cannot borrow books"""
    response = await client.post(
        "/borrowings",
        json={"book_id": test_book.id},
        headers=admin_auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_borrow_book_librarian_denied(client, test_book, librarian_auth_headers):
    """Librarians cannot borrow books"""
    response = await client.post(
        "/borrowings",
        json={"book_id": test_book.id},
        headers=librarian_auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_return_book_member_denied(client, test_book, auth_headers, db_session):
    """Members cannot return books"""
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    borrowing = await borrowing_repo.create({
        "user_id": 1,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    response = await client.patch(
        f"/borrowings/{borrowing.id}/return",
        headers=auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_return_book_admin_allowed(client, test_book, admin_auth_headers, db_session):
    """Admins can return books"""
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    borrowing = await borrowing_repo.create({
        "user_id": 1,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    response = await client.patch(
        f"/borrowings/{borrowing.id}/return",
        headers=admin_auth_headers
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_return_book_librarian_allowed(client, test_book, librarian_auth_headers, db_session):
    """Librarians can return books"""
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


# ==================== REVIEWS ENDPOINTS RBAC ====================

@pytest.mark.asyncio
async def test_create_review_member_allowed(client, test_book, auth_headers, db_session):
    """Only Members can create reviews"""
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": 1,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    response = await client.post(
        f"/books/{test_book.id}/reviews",
        json={"rating": 5, "text": "Great book!"},
        headers=auth_headers
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_review_admin_denied(client, test_book, admin_auth_headers):
    """Admins cannot create reviews"""
    response = await client.post(
        f"/books/{test_book.id}/reviews",
        json={"rating": 5, "text": "Great book!"},
        headers=admin_auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_review_librarian_denied(client, test_book, librarian_auth_headers):
    """Librarians cannot create reviews"""
    response = await client.post(
        f"/books/{test_book.id}/reviews",
        json={"rating": 5, "text": "Great book!"},
        headers=librarian_auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_review_own_review_member_allowed(client, test_book, auth_headers, db_session):
    """Members can delete their own reviews"""
    from src.repository.review import ReviewRepository
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": 1,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    review_repo = ReviewRepository(db_session)
    review = await review_repo.create({
        "user_id": 1,
        "book_id": test_book.id,
        "rating": 4,
        "text": "Good book"
    })
    
    response = await client.delete(
        f"/reviews/{review.id}",
        headers=auth_headers
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_review_other_review_member_denied(client, test_book, auth_headers, db_session):
    """Members cannot delete other users' reviews"""
    from src.repository.review import ReviewRepository
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": 2,  # Different user
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    review_repo = ReviewRepository(db_session)
    review = await review_repo.create({
        "user_id": 2,  # Different user
        "book_id": test_book.id,
        "rating": 4,
        "text": "Good book"
    })
    
    response = await client.delete(
        f"/reviews/{review.id}",
        headers=auth_headers
    )
    # Service raises ValueError which becomes 400, but the message indicates permission denied
    assert response.status_code == 400
    assert "permission denied" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_review_admin_allowed(client, test_book, admin_auth_headers, db_session):
    """Admins can delete any review"""
    from src.repository.review import ReviewRepository
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": 1,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    review_repo = ReviewRepository(db_session)
    review = await review_repo.create({
        "user_id": 1,
        "book_id": test_book.id,
        "rating": 4,
        "text": "Good book"
    })
    
    response = await client.delete(
        f"/reviews/{review.id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 204


# ==================== USERS ENDPOINTS RBAC ====================

@pytest.mark.asyncio
async def test_list_users_member_denied(client, auth_headers):
    """Members cannot list all users"""
    response = await client.get("/users", headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_users_admin_allowed(client, admin_auth_headers):
    """Admins can list all users"""
    response = await client.get("/users", headers=admin_auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_users_librarian_allowed(client, librarian_auth_headers):
    """Librarians can list all users"""
    response = await client.get("/users", headers=librarian_auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_user_member_denied(client, test_role, auth_headers):
    """Members cannot create users"""
    response = await client.post(
        "/users",
        json={
            "email": "new@example.com",
            "name": "New User",
            "password": "Password123!",
            "role_id": test_role.id
        },
        headers=auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_user_admin_allowed(client, test_role, admin_auth_headers):
    """Admins can create users"""
    response = await client.post(
        "/users",
        json={
            "email": "newadmin@example.com",
            "name": "New User",
            "password": "Password123!",
            "role_id": test_role.id
        },
        headers=admin_auth_headers
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_user_librarian_allowed(client, test_role, librarian_auth_headers):
    """Librarians can create users"""
    response = await client.post(
        "/users",
        json={
            "email": "newlib@example.com",
            "name": "New User",
            "password": "Password123!",
            "role_id": test_role.id
        },
        headers=librarian_auth_headers
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_delete_user_member_denied(client, test_user, auth_headers):
    """Members cannot delete users"""
    response = await client.delete(
        f"/users/{test_user.id}",
        headers=auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_librarian_denied(client, test_user, librarian_auth_headers):
    """Librarians cannot delete users"""
    response = await client.delete(
        f"/users/{test_user.id}",
        headers=librarian_auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_admin_allowed(client, test_user, admin_auth_headers):
    """Only Admins can delete users"""
    response = await client.delete(
        f"/users/{test_user.id}",
        headers=admin_auth_headers
    )
    assert response.status_code == 204
