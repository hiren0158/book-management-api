from typing import Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from src.core.database import get_session
from src.service.ai import AIService
from src.service.book import BookService
from src.model.user import User
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/ai", tags=["AI Tools"])
logger = logging.getLogger(__name__)


@router.get("/books/recommend")
async def recommend_books(
    limit: int = Query(5, ge=1, le=20),
    genre: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ai_service = AIService(session)

    try:
        recommendations = await ai_service.recommend_books(
            user_id=current_user.id, genre=genre, limit=limit
        )
        return {
            "user_id": current_user.id,
            "genre_filter": genre,
            "recommendations": recommendations,
            "count": len(recommendations),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI recommendation service unavailable",
        )


class NLSearchRequest(BaseModel):
    query: str


@router.post("/books/search_nl")
async def search_books_natural_language(
    search_data: NLSearchRequest,
    limit: int = Query(10, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    session: AsyncSession = Depends(get_session),
):
    """
    Natural language book search with AI-powered SQL generation.
    Falls back to filter extraction if SQL generation fails.
    """
    from src.tools.ai_tools import nl_to_sql_where
    from src.repository.book import BookRepository

    ai_service = AIService(session)
    book_service = BookService(session)
    book_repo = BookRepository(session)

    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(
        f"[AI Search Started] Query: '{search_data.query}' | Sort: {sort_order}"
    )
    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    logger.info("[Step 1] Calling Gemini to generate SQL WHERE clause...")
    sql_result = await nl_to_sql_where(search_data.query)

    if sql_result["success"]:
        logger.info(f"[Step 2] ✓ Gemini generated SQL WHERE clause")
        logger.info(f"[Step 2] Generated: {sql_result['where_clause']}")
        logger.info(f"[Step 3] ✓ WHERE clause passed security validation")

        try:
            logger.info(f"[Step 4] Executing SQL search with WHERE clause...")
            books, next_cursor = await book_repo.search_books_with_where_clause(
                where_clause=sql_result["where_clause"],
                limit=limit,
                cursor=cursor,
                sort_order=sort_order,
            )

            logger.info(f"[Step 5] ✓ SQL search completed successfully")
            logger.info(f"[Result] Method: SQL WHERE | Found: {len(books)} books")
            logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            return {
                "query": search_data.query,
                "method": "sql_where_clause",
                "where_clause": sql_result["where_clause"],
                "books": books,
                "count": len(books),
                "next_cursor": next_cursor,
                "fallback_used": False,
            }
        except Exception as e:
            logger.warning(f"[Step 4] ✗ SQL execution failed: {e}")
            logger.warning("[Fallback] Switching to filter extraction method...")
    else:
        logger.warning(f"[Step 2] ✗ Gemini SQL generation failed")
        logger.warning(
            f"[Reason] {sql_result.get('fallback_reason', 'unknown')}: {sql_result.get('error', '')}"
        )
        logger.warning("[Fallback] Switching to filter extraction method...")

    # Fallback to filter extraction
    logger.info("")
    logger.info("[Fallback Step 1] Calling Gemini for filter extraction...")

    try:
        filters = await ai_service.nl_to_filters_validated(search_data.query)

        author = filters.get("author")
        genre = filters.get("genre")
        keywords = filters.get("search_query")
        published_year = filters.get("published_year")

        if author or genre or keywords or published_year:
            logger.info(f"[Fallback Step 2] ✓ Gemini extracted filters")
            logger.info(
                f"[Fallback Step 2] Author: {author}, Genre: {genre}, Year: {published_year}"
            )
        else:
            logger.info(
                f"[Fallback Step 2] Gemini returned no specific filters, using raw query"
            )

        logger.info(f"[Fallback Step 3] Building ILIKE query...")
        logger.info(
            f"[Fallback Step 3] Keywords: {keywords if keywords else search_data.query}"
        )

        books, next_cursor = await book_service.search_books_ilike(
            query=keywords if keywords else search_data.query,
            author=author,
            genre=genre,
            published_year=published_year,
            limit=limit,
            cursor=cursor,
            sort_order=sort_order,
        )

        logger.info(f"[Fallback Step 4] ✓ ILIKE search completed successfully")
        logger.info(
            f"[Result] Method: FILTER EXTRACTION | Found: {len(books)} books | Fallback Reason: {sql_result.get('fallback_reason', 'unknown')}"
        )
        logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        return {
            "query": search_data.query,
            "method": "filter_extraction",
            "extracted_filters": {
                "author": author,
                "genre": genre,
                "search_query": keywords,
                "published_year": published_year,
            },
            "books": books,
            "count": len(books),
            "next_cursor": next_cursor,
            "fallback_used": True,
            "fallback_reason": sql_result.get("fallback_reason"),
        }

    except ValueError as e:
        logger.error(f"[Fallback] ✗ Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[Fallback] ✗ Filter extraction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI search service unavailable",
        )
