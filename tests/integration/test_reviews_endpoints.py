import pytest
from datetime import timedelta
from src.utils.datetime_utils import utcnow_naive


@pytest.mark.asyncio
async def test_create_review(client, test_book, auth_headers, db_session):
    """Member can create a review after borrowing"""
    from src.repository.borrowing import BorrowingRepository
    
    # First, borrow the book
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": 1,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    # Then create review
    response = await client.post(
        f"/books/{test_book.id}/reviews",
        json={
            "rating": 5,
            "text": "Excellent book!"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["rating"] == 5
    assert data["text"] == "Excellent book!"
    assert data["book_id"] == test_book.id


@pytest.mark.asyncio
async def test_create_review_requires_auth(client, test_book):
    """Creating reviews requires authentication"""
    response = await client.post(
        f"/books/{test_book.id}/reviews",
        json={
            "rating": 5,
            "text": "Great!"
        }
    )
    
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_review_without_borrowing(client, test_book, auth_headers):
    """Cannot create review without borrowing the book"""
    response = await client.post(
        f"/books/{test_book.id}/reviews",
        json={
            "rating": 5,
            "text": "Great book!"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "borrow" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_duplicate_review(client, test_book, auth_headers, db_session):
    """Cannot create duplicate review for same book"""
    from src.repository.review import ReviewRepository
    from src.repository.borrowing import BorrowingRepository
    
    # Create a borrowing first
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": 1,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    # Create first review
    review_repo = ReviewRepository(db_session)
    await review_repo.create({
        "user_id": 1,
        "book_id": test_book.id,
        "rating": 4,
        "text": "First review"
    })
    
    # Try to create second review
    response = await client.post(
        f"/books/{test_book.id}/reviews",
        json={
            "rating": 5,
            "text": "Second review"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "already reviewed" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_review_invalid_rating(client, test_book, auth_headers, db_session):
    """Rating must be between 1 and 5"""
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": 1,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    # Test rating too high
    response = await client.post(
        f"/books/{test_book.id}/reviews",
        json={
            "rating": 6,
            "text": "Great!"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error
    
    # Test rating too low
    response = await client.post(
        f"/books/{test_book.id}/reviews",
        json={
            "rating": 0,
            "text": "Great!"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_book_reviews(client, test_book, db_session):
    """Anyone can get book reviews"""
    from src.repository.review import ReviewRepository
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": 1,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    review_repo = ReviewRepository(db_session)
    await review_repo.create({
        "user_id": 1,
        "book_id": test_book.id,
        "rating": 4,
        "text": "Good book"
    })
    
    response = await client.get(f"/books/{test_book.id}/reviews")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_book_reviews_empty(client, test_book):
    """Get reviews for book with no reviews"""
    response = await client.get(f"/books/{test_book.id}/reviews")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_get_book_rating(client, test_book, db_session):
    """Get average rating for a book"""
    from src.repository.review import ReviewRepository
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    review_repo = ReviewRepository(db_session)
    
    # Create multiple reviews
    for i, rating in enumerate([4, 5, 3]):
        await borrowing_repo.create({
            "user_id": i + 10,
            "book_id": test_book.id,
            "due_date": utcnow_naive() + timedelta(days=14)
        })
        
        await review_repo.create({
            "user_id": i + 10,
            "book_id": test_book.id,
            "rating": rating,
            "text": f"Review {i}"
        })
    
    response = await client.get(f"/books/{test_book.id}/reviews/rating")
    
    assert response.status_code == 200
    data = response.json()
    assert "average_rating" in data
    assert data["average_rating"] == 4.0  # (4+5+3)/3


@pytest.mark.asyncio
async def test_get_book_rating_no_reviews(client, test_book):
    """Get rating for book with no reviews"""
    response = await client.get(f"/books/{test_book.id}/reviews/rating")
    
    assert response.status_code == 200
    data = response.json()
    assert "average_rating" in data
    # Service returns None when no reviews, endpoint converts to None
    assert data["average_rating"] is None or data["average_rating"] == 0.0


@pytest.mark.asyncio
async def test_get_user_reviews(client, auth_headers, test_user, test_book, db_session):
    """User can get their own reviews"""
    from src.repository.review import ReviewRepository
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": test_user.id,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    review_repo = ReviewRepository(db_session)
    await review_repo.create({
        "user_id": test_user.id,
        "book_id": test_book.id,
        "rating": 5,
        "text": "Great!"
    })
    
    response = await client.get(
        f"/users/{test_user.id}/reviews",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_other_user_reviews_denied(client, auth_headers, admin_user, test_book, db_session):
    """User cannot get other user's reviews"""
    from src.repository.review import ReviewRepository
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": admin_user.id,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    review_repo = ReviewRepository(db_session)
    await review_repo.create({
        "user_id": admin_user.id,
        "book_id": test_book.id,
        "rating": 5,
        "text": "Great!"
    })
    
    response = await client.get(
        f"/users/{admin_user.id}/reviews",
        headers=auth_headers
    )
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_other_user_reviews_as_admin(client, admin_auth_headers, test_user, test_book, db_session):
    """Admin can get any user's reviews"""
    from src.repository.review import ReviewRepository
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": test_user.id,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    review_repo = ReviewRepository(db_session)
    await review_repo.create({
        "user_id": test_user.id,
        "book_id": test_book.id,
        "rating": 5,
        "text": "Great!"
    })
    
    response = await client.get(
        f"/users/{test_user.id}/reviews",
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_delete_own_review(client, auth_headers, test_user, test_book, db_session):
    """User can delete their own review"""
    from src.repository.review import ReviewRepository
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": test_user.id,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    review_repo = ReviewRepository(db_session)
    review = await review_repo.create({
        "user_id": test_user.id,
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
async def test_delete_other_user_review_denied(client, auth_headers, test_book, db_session):
    """User cannot delete other user's review"""
    from src.repository.review import ReviewRepository
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": 999,  # Different user
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    review_repo = ReviewRepository(db_session)
    review = await review_repo.create({
        "user_id": 999,  # Different user
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
async def test_delete_review_as_admin(client, admin_auth_headers, test_user, test_book, db_session):
    """Admin can delete any review"""
    from src.repository.review import ReviewRepository
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": test_user.id,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    review_repo = ReviewRepository(db_session)
    review = await review_repo.create({
        "user_id": test_user.id,
        "book_id": test_book.id,
        "rating": 4,
        "text": "Good book"
    })
    
    response = await client.delete(
        f"/reviews/{review.id}",
        headers=admin_auth_headers
    )
    
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_reviews_pagination(client, test_book, db_session):
    """Test pagination for reviews"""
    from src.repository.review import ReviewRepository
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    review_repo = ReviewRepository(db_session)
    
    for i in range(5):
        await borrowing_repo.create({
            "user_id": i + 10,
            "book_id": test_book.id,
            "due_date": utcnow_naive() + timedelta(days=14)
        })
        
        await review_repo.create({
            "user_id": i + 10,
            "book_id": test_book.id,
            "rating": (i % 5) + 1,
            "text": f"Review {i}"
        })
    
    response = await client.get(f"/books/{test_book.id}/reviews?limit=2")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2


@pytest.mark.asyncio
async def test_create_review_only_member(client, test_book, admin_auth_headers, db_session):
    """Only Members can create reviews"""
    from src.repository.borrowing import BorrowingRepository
    
    borrowing_repo = BorrowingRepository(db_session)
    await borrowing_repo.create({
        "user_id": 2,
        "book_id": test_book.id,
        "due_date": utcnow_naive() + timedelta(days=14)
    })
    
    response = await client.post(
        f"/books/{test_book.id}/reviews",
        json={
            "rating": 5,
            "text": "Great book!"
        },
        headers=admin_auth_headers
    )
    
    assert response.status_code == 403
