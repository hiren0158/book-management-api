from .auth_route import router as auth_router
from .users_route import router as users_router
from .books_route import router as books_router
from .borrowings_route import router as borrowings_router
from .reviews_route import router as reviews_router
from .ai_tools_route import router as ai_tools_router
from .rag import router as rag_router
from .admin_route import router as admin_router

__all__ = [
    "auth_router",
    "users_router",
    "books_router",
    "borrowings_router",
    "reviews_router",
    "ai_tools_router",
    "rag_router",
    "admin_router",
]
