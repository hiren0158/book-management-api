import logging
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.schema.rag_models import UploadResponse, AskRequest, AskResponse
from src.core.database import get_session
from src.api.dependencies import get_current_user, require_roles
from src.model.user import User
from src.service.rag_document import RagDocumentService
from src.service.rag_client import RagClient

router = APIRouter(prefix="/rag", tags=["RAG"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("Admin", "Librarian", "Member"))
):
    """Upload a PDF document for RAG. Accessible by Admin, Librarian, and Member."""
    logger.info(f"[RAG Upload] Started for file: {file.filename} by user {current_user.id}")
    
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        # Create document record in database first
        logger.info(f"[RAG Upload] Creating database record...")
        rag_service = RagDocumentService(session)
        document = await rag_service.create_document(
            filename=file.filename,
            chunk_count=0,  # Will be updated after successful upload
            user=current_user
        )
        logger.info(f"[RAG Upload] Created document record with ID: {document.id}")
        
        # Upload to RAG microservice
        try:
            rag_client = RagClient()
            result = await rag_client.upload_pdf(file, document.id)
            
            # Update chunk count in database
            document.chunk_count = result.chunk_count
            await session.commit()
            await session.refresh(document)
            
            logger.info(f"[RAG Upload] ✓ Successfully uploaded {result.chunk_count} chunks")
            return result
            
        except Exception as e:
            # If RAG service upload fails, delete the database record
            logger.error(f"[RAG Upload] RAG service upload failed, rolling back database record")
            await rag_service.delete_document(document.id, current_user)
            raise
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[RAG Upload] ❌ Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")



@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("Admin", "Librarian", "Member"))
):
    """Delete a RAG document. Users can delete their own documents. Admin/Librarian can delete any."""
    rag_service = RagDocumentService(session)
    
    # Check if document exists and user has access
    document = await rag_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    # Check access permissions
    has_access = await rag_service.check_document_access(document_id, current_user)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this document"
        )
    
    # Delete from RAG microservice (vector store)
    try:
        rag_client = RagClient()
        await rag_client.delete_document(document_id)
    except Exception as e:
        # Log but don't fail - continue with database deletion
        logger.warning(f"Failed to delete from RAG service: {str(e)}")
    
    # Delete from database
    success = await rag_service.delete_document(document_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document from database"
        )


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    payload: AskRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("Admin", "Librarian", "Member"))
):
    """Ask a question about uploaded documents. 
    
    - doc_id = 0 (default): Searches ALL documents you have access to
    - doc_id = specific_id: Searches only that specific document
    """
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    rag_service = RagDocumentService(session)
    
    # Determine which documents to search
    doc_ids_to_search = []
    
    # If doc_id is specific (not 0), search that document
    if payload.doc_id != 0:
        has_access = await rag_service.check_document_access(payload.doc_id, current_user)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this document"
            )
        doc_ids_to_search = [payload.doc_id]
    
    # If doc_id is 0, search ALL user's documents
    else:
        user_documents = await rag_service.get_user_documents(current_user)
        
        if not user_documents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You haven't uploaded any documents yet"
            )
        
        doc_ids_to_search = [doc.id for doc in user_documents]
    
    
    # Call RAG microservice
    try:
        rag_client = RagClient()
        
        # Always send as doc_ids list to microservice
        result = await rag_client.ask_question(
            question=question,
            top_k=payload.top_k,
            doc_ids=doc_ids_to_search
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[RAG Ask] ❌ Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")