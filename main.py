import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.endpoints import (
    auth_router,
    users_router,
    books_router,
    borrowings_router,
    reviews_router,
    ai_tools_router,
    rag_router,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# Suppress noisy Chroma telemetry errors
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)
logging.getLogger("chromadb.telemetry.product").setLevel(logging.CRITICAL)
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
logging.getLogger("posthog").setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    import os
    from dotenv import load_dotenv

    # Startup
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY")

    logger.info("=" * 60)
    logger.info("Book Management API - Starting up")
    logger.info("=" * 60)

    if api_key:
        masked = (
            f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***MASKED***"
        )
        logger.info(f"✓ Gemini API Key: {masked} ({len(api_key)} chars)")
    else:
        logger.warning("✗ Gemini API Key: NOT CONFIGURED")

    logger.info("=" * 60)

    yield  # Application runs here

    # Shutdown
    logger.info("Book Management API - Shutting down")


app = FastAPI(
    title="Book Management API",
    description="A modern book library management system with AI-powered features",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

import os

# CORS Configuration - Restrict in production
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:8080",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(books_router)
app.include_router(borrowings_router)
app.include_router(reviews_router)
app.include_router(ai_tools_router)
app.include_router(rag_router)


@app.get("/")
async def root():
    return {
        "message": "Book Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check with dependency validation."""
    from datetime import datetime
    from src.core.database import get_session
    from sqlalchemy import select

    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {},
    }

    # Check database connection
    try:
        async for session in get_session():
            await session.execute(select(1))
            health_status["checks"]["database"] = "connected"
            break
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)}"

    # Check Gemini API key
    gemini_key = os.getenv("GEMINI_API_KEY")
    health_status["checks"]["gemini_api"] = "configured" if gemini_key else "missing"

    # Check ChromaDB
    try:
        import chromadb

        health_status["checks"]["chromadb"] = "available"
    except Exception:
        health_status["checks"]["chromadb"] = "unavailable"

    return health_status


@app.get("/setup-db")
async def setup_database():
    """
    Temporary endpoint to initialize database since Shell is restricted.
    Runs migrations and creates initial roles.
    """
    try:
        from scripts.init_database import main as init_db_main

        # Run the initialization script
        result = init_db_main()

        if result == 0:
            return {
                "status": "success",
                "message": "Database initialized successfully! Tables created.",
            }
        else:
            return {
                "status": "error",
                "message": "Database initialization failed. Check logs.",
            }

    except Exception as e:
        return {"status": "error", "message": f"Critical error during setup: {str(e)}"}
