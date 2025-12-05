"""RAG Client Service for communicating with RAG microservice."""

import os
import logging
from typing import List, Optional
import httpx
from fastapi import UploadFile, HTTPException

from src.schema.rag_models import UploadResponse, AskRequest, AskResponse

logger = logging.getLogger(__name__)


class RagClient:
    """HTTP client for RAG microservice."""
    
    def __init__(self):
        self.base_url = os.getenv("RAG_SERVICE_URL", "").rstrip("/")
        self.api_key = os.getenv("RAG_API_KEY", "")
        
        if not self.base_url:
            logger.error("RAG_SERVICE_URL not set in environment variables")
            raise ValueError("RAG_SERVICE_URL must be configured")
        
        if not self.api_key:
            logger.error("RAG_API_KEY not set in environment variables")
            raise ValueError("RAG_API_KEY must be configured")
        
        self.headers = {
            "X-API-Key": self.api_key
        }
        self.timeout = httpx.Timeout(120.0, connect=10.0)  # 2 min timeout for processing
    
    async def health_check(self) -> dict:
        """Check if RAG microservice is healthy."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"RAG service health check failed: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail="RAG service is currently unavailable"
            )
    
    async def upload_pdf(
        self,
        file: UploadFile,
        doc_id: int
    ) -> UploadResponse:
        """Upload PDF to RAG microservice for processing.
        
        Args:
            file: PDF file to upload
            doc_id: Document ID from main application database
        
        Returns:
            UploadResponse with document_id and chunk_count
        """
        try:
            # Read file content
            file_content = await file.read()
            
            # Reset file pointer in case it's used elsewhere
            await file.seek(0)
            
            # Prepare multipart form data with doc_id as a form field
            files = {
                "file": (file.filename, file_content, "application/pdf")
            }
            data = {
                "doc_id": doc_id  # Send as integer, not string
            }
            
            logger.info(f"[RAG Client] Uploading document {doc_id} to RAG service")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/upload",
                    files=files,
                    data=data,
                    headers=self.headers
                )
                
                if response.status_code == 503:
                    raise HTTPException(
                        status_code=503,
                        detail="RAG service is busy or timed out. Try a smaller PDF."
                    )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"[RAG Client] Upload successful: {result}")
                return UploadResponse(**result)
        
        except httpx.HTTPStatusError as e:
            logger.error(f"[RAG Client] HTTP error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"RAG service error: {e.response.text}"
            )
        except httpx.TimeoutException:
            logger.error("[RAG Client] Request timed out")
            raise HTTPException(
                status_code=504,
                detail="RAG service request timed out. The document may be too large."
            )
        except Exception as e:
            logger.error(f"[RAG Client] Upload failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to communicate with RAG service: {str(e)}"
            )
    
    async def ask_question(
        self,
        question: str,
        top_k: int = 5,
        doc_ids: Optional[List[int]] = None
    ) -> AskResponse:
        """Ask a question to RAG microservice.
        
        Args:
            question: Question to ask
            top_k: Number of context chunks to retrieve
            doc_ids: List of document IDs to search (None = search all)
        
        Returns:
            AskResponse with answer and context
        """
        try:
            request_data = AskRequest(
                question=question,
                top_k=top_k,
                doc_ids=doc_ids
            )
            
            logger.info(f"[RAG Client] Asking question: {question[:100]}...")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/ask",
                    json=request_data.model_dump(exclude_none=True),
                    headers=self.headers
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"[RAG Client] Question answered successfully")
                return AskResponse(**result)
        
        except httpx.HTTPStatusError as e:
            logger.error(f"[RAG Client] HTTP error: {e.response.status_code} - {e.response.text}")
            
            # Pass through 404 if no documents found
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail="No documents found. Upload documents first."
                )
            
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"RAG service error: {e.response.text}"
            )
        except httpx.TimeoutException:
            logger.error("[RAG Client] Request timed out")
            raise HTTPException(
                status_code=504,
                detail="RAG service request timed out"
            )
        except Exception as e:
            logger.error(f"[RAG Client] Ask failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to communicate with RAG service: {str(e)}"
            )
    
    async def delete_document(self, document_id: int) -> dict:
        """Delete document from RAG microservice.
        
        Args:
            document_id: Document ID to delete
        
        Returns:
            Success message
        """
        try:
            logger.info(f"[RAG Client] Deleting document {document_id}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.base_url}/documents/{document_id}",
                    headers=self.headers
                )
                
                # Handle 404 gracefully - document might not exist in vector store
                if response.status_code == 404:
                    logger.warning(f"[RAG Client] Document {document_id} not found in RAG service")
                    return {"message": "Document not found in RAG service"}
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"[RAG Client] Document deleted successfully")
                return result
        
        except httpx.HTTPStatusError as e:
            logger.error(f"[RAG Client] HTTP error: {e.response.status_code} - {e.response.text}")
            
            # Don't fail deletion if RAG service returns 404
            if e.response.status_code == 404:
                return {"message": "Document not found in RAG service"}
            
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"RAG service error: {e.response.text}"
            )
        except httpx.TimeoutException:
            logger.error("[RAG Client] Request timed out")
            raise HTTPException(
                status_code=504,
                detail="RAG service request timed out"
            )
        except Exception as e:
            logger.error(f"[RAG Client] Delete failed: {str(e)}", exc_info=True)
            # Don't fail the main deletion if RAG service has issues
            logger.warning("RAG service deletion failed, but continuing with database deletion")
            return {"message": "RAG service deletion failed, but database record removed"}
