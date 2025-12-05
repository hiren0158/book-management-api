import base64
import json
import logging
from typing import Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import extract, distinct, func, literal, or_
from src.model.book import Book
from .base import BaseRepository

logger = logging.getLogger(__name__)


class BookRepository(BaseRepository[Book]):
    def __init__(self, session: AsyncSession):
        super().__init__(Book, session)

    async def get_by_isbn(self, isbn: str) -> Optional[Book]:
        statement = select(Book).where(Book.isbn == isbn)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_all_genres(self) -> list[str]:
        """Fetch all unique genres from the database."""
        statement = select(distinct(Book.genre)).where(Book.genre.isnot(None))
        result = await self.session.execute(statement)
        genres = result.scalars().all()
        return [genre for genre in genres if genre]

    async def get_all_authors(self) -> list[str]:
        """Fetch all unique author names from the database."""
        statement = select(distinct(Book.author)).where(Book.author.isnot(None))
        result = await self.session.execute(statement)
        authors = result.scalars().all()
        return [author for author in authors if author]

    # Traditional search (GET /books) - Uses FTS + Trigram + ILIKE fallback

    async def search_books_fts(
        self,
        query: Optional[str] = None,
        author: Optional[str] = None,
        genre: Optional[str] = None,
        published_year: Optional[int] = None,
        limit: int = 10,
        cursor: Optional[str] = None,
        sort_order: str = "desc",
    ):
        """Traditional search using PostgreSQL FTS + Trigram similarity with ILIKE fallback."""
        base_filters = []
        if author:
            base_filters.append(Book.author.ilike(f"%{author}%"))
        if genre:
            base_filters.append(Book.genre.ilike(f"%{genre}%"))
        if published_year:
            base_filters.append(extract("year", Book.published_date) == published_year)

        # Strategy 1: Full-Text Search
        # Check dialect to avoid FTS errors on SQLite during tests
        is_postgres = self.session.bind.dialect.name == "postgresql"

        if query and is_postgres:
            normalized_query = query.strip()
            ts_query = func.websearch_to_tsquery("english", normalized_query)

            # Calculate trigram similarity for ALL searchable fields
            title_trigram_score = func.similarity(
                func.lower(Book.title), func.lower(literal(normalized_query))
            )
            author_trigram_score = func.similarity(
                func.lower(Book.author), func.lower(literal(normalized_query))
            )
            description_trigram_score = func.similarity(
                func.lower(Book.description), func.lower(literal(normalized_query))
            )
            genre_trigram_score = func.similarity(
                func.lower(Book.genre), func.lower(literal(normalized_query))
            )
            isbn_trigram_score = func.similarity(
                func.lower(Book.isbn), func.lower(literal(normalized_query))
            )

            # Use the maximum trigram score across all fields
            trigram_score = func.greatest(
                title_trigram_score,
                author_trigram_score,
                description_trigram_score,
                genre_trigram_score,
                isbn_trigram_score,
            )

            fts_rank = func.ts_rank_cd(Book.search_vector, ts_query)
            combined_rank = (fts_rank * 0.7 + trigram_score * 0.3).label(
                "combined_rank"
            )

            stmt = select(Book, combined_rank).where(
                or_(Book.search_vector.op("@@")(ts_query), trigram_score > 0.2)
            )

            for filter_clause in base_filters:
                stmt = stmt.where(filter_clause)

            stmt = stmt.order_by(combined_rank.desc(), Book.created_at.desc())

            offset = self._decode_rank_cursor(cursor) if cursor else 0
            stmt = stmt.offset(offset).limit(limit + 1)

            result = await self.session.execute(stmt)
            rows = result.all()
            items = [row[0] for row in rows[:limit]]

            has_more = len(rows) > limit
            next_cursor = self._encode_rank_cursor(offset + limit) if has_more else None

            if items:
                logger.info(
                    f"[FTS+Trigram] Query: '{query}' | Found {len(items)} results"
                )
                return items, next_cursor
            else:
                logger.info(
                    f"[FTS+Trigram] Query: '{query}' | No results, falling back to ILIKE"
                )

        # Strategy 2: Fallback (ILIKE) or No Query
        # If FTS yielded no results OR if there was no query, use the standard list method
        # Build custom filters for the repository's list method
        custom_filters = []

        if author:
            custom_filters.append(lambda s: s.where(Book.author.ilike(f"%{author}%")))
        if genre:
            custom_filters.append(lambda s: s.where(Book.genre.ilike(f"%{genre}%")))
        if published_year:
            custom_filters.append(
                lambda s: s.where(
                    extract("year", Book.published_date) == published_year
                )
            )

        search_fields = ["title", "description", "author", "genre", "isbn"]

        logger.info(
            f"[ILIKE Fallback] Query: '{query}' | Filters: author={author}, genre={genre}, year={published_year}"
        )

        return await self.list(
            limit=limit,
            cursor=cursor,
            filters={},
            search_fields=search_fields,
            search_query=query,
            sort_order=sort_order,
            custom_filters=custom_filters if custom_filters else None,
        )

    # AI-driven search (POST /ai/books/search_nl) - Uses ILIKE only

    async def search_books_ilike(
        self,
        query: Optional[str] = None,
        author: Optional[str] = None,
        genre: Optional[str] = None,
        published_year: Optional[int] = None,
        limit: int = 10,
        cursor: Optional[str] = None,
        sort_order: str = "desc",
    ):
        """ILIKE-based search for AI natural language search. AI extracts filters, this applies them."""
        # Build filter query
        stmt = select(Book)

        # Apply structured filters (AND conditions)
        if author:
            stmt = stmt.where(Book.author.ilike(f"%{author}%"))
        if genre:
            stmt = stmt.where(Book.genre.ilike(f"%{genre}%"))
        if published_year:
            stmt = stmt.where(extract("year", Book.published_date) == published_year)

        # Apply keyword search (OR conditions for better matching)
        if query:
            # Split query into keywords (remove common words)
            stop_words = {
                "a",
                "an",
                "the",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
                "any",
                "me",
                "my",
                "find",
                "show",
                "get",
            }
            keywords = [
                word.strip()
                for word in query.lower().split()
                if word.strip()
                and word.strip() not in stop_words
                and len(word.strip()) > 2
            ]

            if keywords:
                # Create OR conditions for each keyword across all searchable fields
                keyword_conditions = []
                for keyword in keywords:
                    keyword_conditions.append(
                        or_(
                            Book.title.ilike(f"%{keyword}%"),
                            Book.description.ilike(f"%{keyword}%"),
                            Book.author.ilike(f"%{keyword}%"),
                            Book.genre.ilike(f"%{keyword}%"),
                        )
                    )

                # Combine with OR (match ANY keyword)
                if keyword_conditions:
                    stmt = stmt.where(or_(*keyword_conditions))

        # Apply sorting
        if sort_order == "asc":
            stmt = stmt.order_by(Book.created_at.asc())
        else:
            stmt = stmt.order_by(Book.created_at.desc())

        # Apply pagination
        offset = self._decode_rank_cursor(cursor) if cursor else 0
        stmt = stmt.offset(offset).limit(limit + 1)

        # Execute query
        result = await self.session.execute(stmt)
        rows = result.scalars().all()

        items = list(rows[:limit])
        has_more = len(rows) > limit
        next_cursor = self._encode_rank_cursor(offset + limit) if has_more else None

        logger.info(
            f"[AI ILIKE-only] Query: '{query}' | Keywords: {keywords if query else 'none'} | Filters: author={author}, genre={genre}, year={published_year} | Found: {len(items)}"
        )

        return items, next_cursor

    async def search_books_with_where_clause(
        self,
        where_clause: str,
        limit: int = 10,
        cursor: Optional[str] = None,
        sort_order: str = "desc",
    ) -> tuple[list[Book], Optional[str]]:
        """
        Execute a book search with a pre-validated WHERE clause.

        SECURITY: The where_clause MUST be validated by SQLWhereValidator before calling this method.

        Args:
            where_clause: Pre-validated SQL WHERE clause (without 'WHERE' keyword)
            limit: Maximum number of results
            cursor: Pagination cursor
            sort_order: Sort direction ('asc' or 'desc')

        Returns:
            Tuple of (books list, next_cursor)
        """
        from sqlalchemy import text

        # Database compatibility: Convert ILIKE to LIKE for SQLite (tests use SQLite)
        # ILIKE is case-insensitive in PostgreSQL, LIKE in SQLite is case-insensitive by default
        db_url = str(self.session.bind.url) if self.session.bind else ""
        if "sqlite" in db_url.lower():
            where_clause = where_clause.replace(" ILIKE ", " LIKE ")
            where_clause = where_clause.replace("ILIKE ", "LIKE ")

        # Decode cursor if provided
        offset = self._decode_rank_cursor(cursor) if cursor else 0

        # Build and execute query using text() for WHERE clause
        stmt = select(Book).where(text(where_clause))

        # Apply sorting
        if sort_order == "asc":
            stmt = stmt.order_by(Book.created_at.asc())
        else:
            stmt = stmt.order_by(Book.created_at.desc())

        # Apply pagination
        stmt = stmt.offset(offset).limit(limit + 1)

        # Execute query
        result = await self.session.execute(stmt)
        rows = list(result.scalars().all())

        # Generate pagination
        items = rows[:limit]
        has_more = len(rows) > limit
        next_cursor = self._encode_rank_cursor(offset + limit) if has_more else None

        logger.info(
            f"[AI SQL WHERE] WHERE clause: '{where_clause}' | Found: {len(items)}"
        )

        return items, next_cursor

    def _encode_rank_cursor(self, offset: int) -> str:
        data = json.dumps({"offset": offset})
        return base64.b64encode(data.encode()).decode()

    def _decode_rank_cursor(self, cursor: str) -> int:
        try:
            data = base64.b64decode(cursor.encode()).decode()
            payload = json.loads(data)
            return int(payload.get("offset", 0))
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError("Invalid cursor format") from exc
