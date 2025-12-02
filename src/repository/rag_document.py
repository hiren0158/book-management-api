from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.model.rag_document import RagDocument


class RagDocumentRepository:
    """Repository for RAG document database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, filename: str, chunk_count: int, user_id: int) -> RagDocument:
        """Create a new RAG document record."""
        document = RagDocument(
            filename=filename,
            chunk_count=chunk_count,
            user_id=user_id
        )
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document
    
    async def get_by_id(self, document_id: int) -> Optional[RagDocument]:
        """Get a document by ID."""
        result = await self.session.execute(
            select(RagDocument).where(RagDocument.id == document_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_documents(self, user_id: int) -> list[RagDocument]:
        """Get all documents belonging to a user."""
        result = await self.session.execute(
            select(RagDocument).where(RagDocument.user_id == user_id)
        )
        return list(result.scalars().all())
    
    async def delete(self, document_id: int) -> bool:
        """Delete a document."""
        document = await self.get_by_id(document_id)
        if document:
            await self.session.delete(document)
            await self.session.commit()
            return True
        return False
