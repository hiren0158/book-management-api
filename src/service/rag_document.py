from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.rag_document import RagDocumentRepository
from src.model.rag_document import RagDocument
from src.model.user import User


class RagDocumentService:
    """Service for RAG document business logic."""

    def __init__(self, session: AsyncSession):
        self.repository = RagDocumentRepository(session)

    async def create_document(
        self, filename: str, chunk_count: int, user: User
    ) -> RagDocument:
        """Create a new RAG document."""
        return await self.repository.create(filename, chunk_count, user.id)

    async def get_document(self, document_id: int) -> Optional[RagDocument]:
        """Get a document by ID."""
        return await self.repository.get_by_id(document_id)

    async def check_document_access(self, document_id: int, user: User) -> bool:
        """Check if user has access to a document.

        Admin and Librarian can access all documents.
        Members can only access their own documents.
        """
        document = await self.repository.get_by_id(document_id)
        if not document:
            return False

        # Admin and Librarian have access to all documents
        if user.role.name in ["Admin", "Librarian"]:
            return True

        # Regular users can only access their own documents
        return document.user_id == user.id

    async def get_user_documents(self, user: User) -> list[RagDocument]:
        """Get all documents for a user.

        Admin and Librarian get all documents.
        Members get only their own documents.
        """
        if user.role.name in ["Admin", "Librarian"]:
            # TODO: Return all documents - needs additional repository method
            return await self.repository.get_user_documents(user.id)
        else:
            return await self.repository.get_user_documents(user.id)

    async def delete_document(self, document_id: int, user: User) -> bool:
        """Delete a document if user has access."""
        has_access = await self.check_document_access(document_id, user)
        if not has_access:
            return False

        return await self.repository.delete(document_id)
