import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.service.book import BookService
from src.model.book import Book
from datetime import date

@pytest.mark.asyncio
async def test_fts_basic_search(db_session: AsyncSession):
    # Setup data
    book1 = Book(
        title="Python Programming",
        description="A comprehensive guide to Python.",
        isbn="ISBN-FTS-001",
        author="John Doe",
        genre="Education",
        published_date=date(2023, 1, 1)
    )
    book2 = Book(
        title="Cooking with Python",
        description="Recipes for snakes.",
        isbn="ISBN-FTS-002",
        author="Jane Smith",
        genre="Cooking",
        published_date=date(2023, 1, 1)
    )
    db_session.add_all([book1, book2])
    await db_session.commit()
    
    # Force refresh to ensure computed column is populated (though it's generated on write)
    await db_session.refresh(book1)
    await db_session.refresh(book2)

    repo = BookService(db_session)
    
    # Test FTS match
    items, _ = await repo.search_books_fts(query="comprehensive")
    assert len(items) == 1
    assert items[0].title == "Python Programming"

@pytest.mark.asyncio
async def test_fts_ranking(db_session: AsyncSession):
    # Setup data
    book1 = Book(
        title="Python Data Science",
        description="Python is great for data.",
        isbn="ISBN-RANK-001",
        author="Data Guru",
        genre="Tech",
        published_date=date(2023, 1, 1)
    )
    book2 = Book(
        title="Advanced Python",
        description="Python python python.", # More mentions = higher rank usually
        isbn="ISBN-RANK-002",
        author="Pythonista",
        genre="Tech",
        published_date=date(2023, 1, 1)
    )
    db_session.add_all([book1, book2])
    await db_session.commit()

    repo = BookService(db_session)
    
    # Test Ranking: "python" appears more in book2 description + title
    items, _ = await repo.search_books_fts(query="python")
    assert len(items) >= 2
    # Note: Ranking logic can be subtle with small text, but let's check relative ordering
    # Ideally book2 should be first due to frequency
    assert items[0].isbn == "ISBN-RANK-002"


@pytest.mark.asyncio
async def test_fts_matches_genre(db_session: AsyncSession):
    book1 = Book(
        title="Space Biology",
        description="How organisms adapt beyond Earth.",
        isbn="ISBN-GENRE-001",
        author="Nova Keen",
        genre="Education",
        published_date=date(2023, 5, 5)
    )
    db_session.add(book1)
    await db_session.commit()
    await db_session.refresh(book1)

    repo = BookService(db_session)
    items, _ = await repo.search_books_fts(query="education")

    assert len(items) == 1
    assert items[0].genre == "Education"

@pytest.mark.asyncio
async def test_fts_fallback(db_session: AsyncSession):
    # Setup data
    book1 = Book(
        title="UniqueWord",
        description="Something special.",
        isbn="ISBN-FALLBACK-001",
        author="Fallback Author",
        genre="Test",
        published_date=date(2023, 1, 1)
    )
    db_session.add(book1)
    await db_session.commit()

    repo = BookService(db_session)
    
    # Test Fallback: Search for substring that FTS might miss (e.g., "nique" from "Unique")
    # FTS usually stems, so "Unique" -> "uniqu". "nique" is a substring.
    # websearch_to_tsquery('english', 'nique') might not match 'UniqueWord'
    # But ILIKE '%nique%' WILL match 'UniqueWord'
    
    items, _ = await repo.search_books_fts(query="nique")
    assert len(items) == 1
    assert items[0].title == "UniqueWord"

@pytest.mark.asyncio
async def test_fts_combined_filters(db_session: AsyncSession):
    # Setup data
    book1 = Book(
        title="Space Travel",
        description="Journey to Mars.",
        isbn="ISBN-FILTER-001",
        author="Elon",
        genre="Sci-Fi",
        published_date=date(2023, 1, 1)
    )
    book2 = Book(
        title="Space Cooking",
        description="Cooking on Mars.",
        isbn="ISBN-FILTER-002",
        author="Chef",
        genre="Cooking",
        published_date=date(2023, 1, 1)
    )
    db_session.add_all([book1, book2])
    await db_session.commit()

    repo = BookService(db_session)
    
    # Test FTS + Genre Filter
    items, _ = await repo.search_books_fts(query="Mars", genre="Sci-Fi")
    assert len(items) == 1
    assert items[0].title == "Space Travel"
