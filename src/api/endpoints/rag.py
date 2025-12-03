import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.text_chunker import chunk_text
from src.service.pdf_service import extract_text_from_pdf
from src.service.embedding_service import EmbeddingService
from src.service.vector_store import VectorStore
from src.schema.rag_models import UploadResponse, AskRequest, AskResponse, RetrievedChunk
from src.service.ai_search import get_gemini_model
from src.core.database import get_session
from src.api.dependencies import get_current_user, require_roles
from src.model.user import User
from src.service.rag_document import RagDocumentService

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
        # extract_text_from_pdf returns cleaned text and page segments
        logger.info(f"[RAG Upload] Extracting text from PDF...")
        text, page_segments = await extract_text_from_pdf(file)
        logger.info(f"[RAG Upload] Extracted {len(text)} characters from {len(page_segments)} pages")
        
        logger.info(f"[RAG Upload] Chunking text...")
        chunks = chunk_text(text, max_chunk_size=1200, overlap=200)
        logger.info(f"[RAG Upload] Created {len(chunks)} chunks")
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No extractable text found in PDF")

        # Determine page number for each chunk by finding which segment it came from
        logger.info(f"[RAG Upload] Mapping chunks to pages...")
        chunk_page_numbers = []
        for chunk in chunks:
            # Find the first page segment that contains part of this chunk
            page_num = 1  # Default
            chunk_start = chunk[:100].strip()  # Use first 100 chars to match
            
            for segment_text, seg_page_num in page_segments:
                if chunk_start in segment_text or segment_text[:100] in chunk:
                    page_num = seg_page_num
                    break
            
            chunk_page_numbers.append(page_num)

        logger.info(f"[RAG Upload] Generating embeddings for {len(chunks)} chunks...")
        embedder = EmbeddingService.instance()
        embeddings = embedder.embed_chunks(chunks)
        logger.info(f"[RAG Upload] Generated {len(embeddings)} embeddings")

        # Create document record in database
        logger.info(f"[RAG Upload] Creating database record...")
        rag_service = RagDocumentService(session)
        document = await rag_service.create_document(
            filename=file.filename,
            chunk_count=len(chunks),
            user=current_user
        )
        logger.info(f"[RAG Upload] Created document record with ID: {document.id}")
        
        # Store in vector database with integer document ID
        logger.info(f"[RAG Upload] Storing in vector database...")
        doc_id_str = f"doc_{document.id}"
        store = VectorStore()
        count = store.upsert(doc_id_str, chunks, embeddings, page_numbers=chunk_page_numbers)
        logger.info(f"[RAG Upload] ✓ Successfully stored {count} chunks in vector DB")

        return UploadResponse(document_id=document.id, chunk_count=count)
    
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
    
    # Delete from vector store
    doc_id_str = f"doc_{document_id}"
    store = VectorStore()
    store.delete_document(doc_id_str)
    
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
    
    - If doc_id is provided: searches only that document (if user has access)
    - If doc_id is NOT provided: searches ALL documents owned by the user
    """
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    rag_service = RagDocumentService(session)
    
    # Determine which documents to search
    if payload.doc_id:
        # Search specific document - check access
        has_access = await rag_service.check_document_access(payload.doc_id, current_user)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this document"
            )
        doc_id_filter = f"doc_{payload.doc_id}"
    else:
        # Search ALL user's documents
        # Get all documents owned by the user
        user_documents = await rag_service.get_user_documents(current_user)
        
        if not user_documents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You haven't uploaded any documents yet"
            )
        
        # Create list of doc IDs to search (for multi-document search)
        doc_ids = [f"doc_{doc.id}" for doc in user_documents]
        doc_id_filter = doc_ids  # Pass list instead of single string

    embedder = EmbeddingService.instance()
    q_emb = embedder.embed_query(question)
    store = VectorStore()
    results = store.query(q_emb, top_k=payload.top_k, doc_id=doc_id_filter)

    # Build context
    documents: List[str] = results.get("documents", [[]])[0]
    metadatas: List[dict] = results.get("metadatas", [[]])[0]
    distances: List[float] = results.get("distances", [[]])[0]

    retrieved: List[RetrievedChunk] = []
    for idx, (text, meta, dist) in enumerate(zip(documents, metadatas, distances)):
        # Detect section headers in chunk (simple heuristic)
        section = None
        lines = text.split('\n')
        for line in lines[:3]:  # Check first 3 lines
            if line.strip().endswith(':') and len(line.strip()) < 100:
                section = line.strip()
                break
        
        # Convert distance to similarity score (higher = better)
        # ChromaDB returns L2 distance where lower = more similar
        # Convert to similarity: 1 / (1 + distance) so higher = more relevant
        similarity_score = 1 / (1 + float(dist))
        
        retrieved.append(RetrievedChunk(
            text=text,
            score=similarity_score,  # Now higher score = more relevant
            doc_id=str(meta.get("doc_id", "")),
            chunk_index=int(meta.get("chunk_index", 0)),
            page_number=meta.get("page_number"),  # Get page number from metadata
            section=section,
            position=idx
        ))

    # Enhanced context formatting with clear chunk boundaries
    context_parts = []
    for i, chunk in enumerate(retrieved, 1):
        page_info = f" (Page {chunk.page_number})" if chunk.page_number else ""
        section_info = f" | Section: {chunk.section}" if chunk.section else ""
        header = f"[Source {i}{page_info}{section_info}]"
        # Use actual newlines, not escaped strings
        context_parts.append(f"{header}\n{chunk.text}")
    
    # Join with separator - using actual newlines, not escape sequences
    context_text = "\n\n---\n\n".join(context_parts)

    # Enhanced prompt for financial documents - request plain text answers
    prompt_parts = [
        "You are an expert financial analyst assistant. Answer the user's question based on the provided context from financial documents.",
        "",
        "INSTRUCTIONS:",
        "- Provide accurate, detailed answers in PLAIN TEXT format",
        "- For financial data (numbers, percentages, currency), cite the exact figures from the context",
        "- Write answers in clear, direct sentences",
        "- DO NOT mention source numbers (e.g., 'Source 1', 'Source 2') as they are already shown separately",
        "- If the answer requires multiple pieces of information, synthesize them into a coherent response",
        "- If the context doesn't contain enough information, state what's missing",
        "- Preserve numerical accuracy - do not round or approximate financial figures",
        "- Write in plain text without any special formatting",
        "",
        "CONTEXT:",
        context_text,
        "",
        f"QUESTION: {question}",
        "",
        "ANSWER (write directly without mentioning sources):"
    ]
    
    # Join with actual newlines, not escaped sequences
    prompt = "\n".join(prompt_parts)

    try:
        gemini_model = get_gemini_model()
        response = gemini_model.generate_content(prompt)
        answer = getattr(response, "text", None) or (response.candidates[0].content.parts[0].text if response.candidates else "")
        if not answer:
            answer = "No answer generated."
        
        # Strip any remaining markdown formatting that Gemini might have added
        import re
        
        # Remove markdown headers
        answer = re.sub(r'^#{1,6}\s+', '', answer, flags=re.MULTILINE)
        
        # Remove bold/italic markers (but preserve the content)
        answer = re.sub(r'\*\*([^*]+)\*\*', r'\1', answer)  # Bold
        answer = re.sub(r'__([^_]+)__', r'\1', answer)      # Bold alternative
        answer = re.sub(r'\*([^*\n]+)\*', r'\1', answer)    # Italic (avoid matching list bullets)
        answer = re.sub(r'_([^_\n]+)_', r'\1', answer)      # Italic alternative
        
        # Remove code blocks and inline code
        answer = re.sub(r'```[^`]*```', '', answer, flags=re.DOTALL)
        answer = re.sub(r'`([^`]+)`', r'\1', answer)
        
        # Convert bullet points to clean format
        # Handle various bullet formats: *, -, •, numbered lists
        answer = re.sub(r'^\s*[\*\-•]\s+', '- ', answer, flags=re.MULTILINE)
        answer = re.sub(r'^\s*\d+\.\s+', lambda m: f"{m.group(0).strip()} ", answer, flags=re.MULTILINE)
        
        # Clean up excessive newlines - convert multiple newlines to double newline for paragraphs
        answer = re.sub(r'\n{3,}', '\n\n', answer)
        
        # Remove leading/trailing whitespace from each line
        lines = [line.rstrip() for line in answer.split('\n')]
        answer = '\n'.join(lines)
        
        # Convert to single paragraph format for clean display in Swagger
        # Replace all newlines with spaces to create one continuous text
        answer = answer.replace('\n', ' ')
        # Clean up multiple spaces
        answer = re.sub(r'\s{2,}', ' ', answer)
        
        # Final cleanup
        answer = answer.strip()
        
    except Exception as e:
        logger.exception("Gemini API error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to generate answer from Gemini")

    return AskResponse(answer=answer.strip(), context=retrieved)