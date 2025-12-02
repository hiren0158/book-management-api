import pytest
from datetime import date


@pytest.mark.asyncio
async def test_list_books_public(client, test_book):
    """Anyone can list books"""
    response = await client.get("/books")
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1


@pytest.mark.asyncio
async def test_get_book_by_id(client, test_book):
    """Anyone can get a book by ID"""
    response = await client.get(f"/books/{test_book.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_book.id
    assert data["title"] == test_book.title
    assert data["author"] == test_book.author


@pytest.mark.asyncio
async def test_get_nonexistent_book(client):
    """Should return 404 for non-existent book"""
    response = await client.get("/books/99999")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_book_requires_auth(client):
    """Creating books requires authentication"""
    response = await client.post(
        "/books",
        json={
            "title": "New Book",
            "description": "Description",
            "isbn": "978-1-234567-89-0",
            "author": "Author",
            "genre": "Fiction",
            "published_date": "2021-01-01"
        }
    )
    
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_book_as_admin(client, admin_auth_headers):
    """Admin can create books"""
    response = await client.post(
        "/books",
        json={
            "title": "Admin Book",
            "description": "Book by admin",
            "isbn": "978-1-234567-89-1",
            "author": "Admin Author",
            "genre": "Non-Fiction",
            "published_date": "2022-03-15"
        },
        headers=admin_auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Admin Book"
    assert data["isbn"] == "978-1-234567-89-1"


@pytest.mark.asyncio
async def test_create_book_duplicate_isbn(client, test_book, admin_auth_headers):
    """Cannot create book with duplicate ISBN"""
    response = await client.post(
        "/books",
        json={
            "title": "Duplicate ISBN Book",
            "description": "Description",
            "isbn": test_book.isbn,  # Same ISBN
            "author": "Author",
            "genre": "Fiction",
            "published_date": "2021-01-01"
        },
        headers=admin_auth_headers
    )
    
    assert response.status_code == 400
    assert "isbn" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_search_books_by_author(client, test_book):
    """Search books by author"""
    response = await client.get(f"/books?author={test_book.author}")
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    if len(data["data"]) > 0:
        assert any(book["author"] == test_book.author for book in data["data"])


@pytest.mark.asyncio
async def test_search_books_by_genre(client, test_book):
    """Search books by genre"""
    response = await client.get(f"/books?genre={test_book.genre}")
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    if len(data["data"]) > 0:
        assert all(book["genre"] == test_book.genre for book in data["data"])


@pytest.mark.asyncio
async def test_search_books_by_published_year(client, test_book, db_session):
    """Search books by published year"""
    from src.repository.book import BookRepository
    
    book_repo = BookRepository(db_session)
    await book_repo.create({
        "title": "2023 Book",
        "description": "Description",
        "isbn": "978-1-234567-89-2",
        "author": "Author",
        "genre": "Fiction",
        "published_date": date(2023, 1, 1)
    })
    
    response = await client.get("/books?published_year=2023")
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data


@pytest.mark.asyncio
async def test_search_books_with_query(client, test_book):
    """Search books with general query"""
    response = await client.get(f"/books?q={test_book.title}")
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_search_books_combined_filters(client, test_book):
    """Search with multiple filters"""
    response = await client.get(
        f"/books?author={test_book.author}&genre={test_book.genre}&q=Test"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data


@pytest.mark.asyncio
async def test_search_books_case_insensitive(client, test_book):
    """Search should be case-insensitive"""
    response = await client.get("/books?author=test author")  # lowercase
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data


@pytest.mark.asyncio
async def test_update_book_requires_librarian_or_admin(client, test_book, auth_headers):
    """Members cannot update books"""
    response = await client.put(
        f"/books/{test_book.id}",
        json={"title": "Updated Title"},
        headers=auth_headers
    )
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_book_as_admin(client, test_book, admin_auth_headers):
    """Admin can update books"""
    response = await client.put(
        f"/books/{test_book.id}",
        json={"title": "Updated by Admin"},
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated by Admin"


@pytest.mark.asyncio
async def test_update_book_partial_update(client, test_book, admin_auth_headers):
    """Can update only specific fields"""
    response = await client.put(
        f"/books/{test_book.id}",
        json={"description": "New description only"},
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "New description only"
    assert data["title"] == test_book.title  # Unchanged


@pytest.mark.asyncio
async def test_delete_book_requires_admin(client, test_book, auth_headers):
    """Only Admin can delete books"""
    response = await client.delete(
        f"/books/{test_book.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_book_as_admin(client, test_book, admin_auth_headers):
    """Admin can delete books"""
    response = await client.delete(
        f"/books/{test_book.id}",
        headers=admin_auth_headers
    )
    
    assert response.status_code == 204
    
    # Verify book is deleted
    get_response = await client.get(f"/books/{test_book.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_pagination_books(client, db_session):
    """Test pagination for books"""
    from src.repository.book import BookRepository
    
    book_repo = BookRepository(db_session)
    for i in range(5):
        await book_repo.create({
            "title": f"Paginated Book {i}",
            "description": f"Description {i}",
            "isbn": f"978-0-99999-9{i}0-9",
            "author": f"Author {i}",
            "genre": "Fiction",
            "published_date": date(2023, 1, 1)
        })
    
    response = await client.get("/books?limit=2")
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) <= 2
    assert "next_cursor" in data
    assert "has_next_page" in data


@pytest.mark.asyncio
async def test_pagination_with_cursor(client, db_session):
    """Test pagination with cursor"""
    from src.repository.book import BookRepository
    
    book_repo = BookRepository(db_session)
    for i in range(5):
        await book_repo.create({
            "title": f"Cursor Book {i}",
            "description": f"Description {i}",
            "isbn": f"978-0-88888-8{i}0-9",
            "author": f"Author {i}",
            "genre": "Fiction",
            "published_date": date(2023, 1, 1)
        })
    
    # Get first page
    first_response = await client.get("/books?limit=2")
    assert first_response.status_code == 200
    first_data = first_response.json()
    
    if first_data.get("next_cursor"):
        # Get second page using cursor
        second_response = await client.get(f"/books?limit=2&cursor={first_data['next_cursor']}")
        assert second_response.status_code == 200
        second_data = second_response.json()
        assert "data" in second_data
        assert len(second_data["data"]) <= 2


@pytest.mark.asyncio
async def test_sort_order_asc(client, db_session):
    """Test sorting in ascending order"""
    from src.repository.book import BookRepository
    
    book_repo = BookRepository(db_session)
    await book_repo.create({
        "title": "A Book",
        "description": "Description",
        "isbn": "978-0-77777-77-7",
        "author": "Author",
        "genre": "Fiction",
        "published_date": date(2023, 1, 1)
    })
    
    response = await client.get("/books?sort_order=asc&limit=10")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_sort_order_desc(client, db_session):
    """Test sorting in descending order"""
    response = await client.get("/books?sort_order=desc&limit=10")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_ai_query_parameter(client, test_book):
    """Test AI query parameter for natural language search"""
    response = await client.get("/books?ai_query=books by Test Author")
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
