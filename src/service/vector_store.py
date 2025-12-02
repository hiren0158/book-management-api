from __future__ import annotations
from typing import List, Dict, Any, Optional
import os
import chromadb
from chromadb.config import Settings


class VectorStore:
    def __init__(self, collection_name: str = "rag_documents") -> None:
        persist_dir = os.getenv("CHROMA_DIR", os.path.join(os.getcwd(), "chroma_db"))
        # Initialize Chroma using the new PersistentClient API and explicitly disable telemetry.
        self.client = chromadb.PersistentClient(path=persist_dir, settings=Settings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(collection_name)

    def upsert(self, doc_id: str, chunks: List[str], embeddings: List[List[float]], page_numbers: Optional[List[int]] = None) -> int:
        ids = [f"{doc_id}:{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "doc_id": doc_id,
                "chunk_index": i,
                "page_number": page_numbers[i] if page_numbers and i < len(page_numbers) else None
            }
            for i in range(len(chunks))
        ]
        self.collection.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=chunks)
        # No explicit persist call needed; PersistentClient handles persistence automatically.
        return len(chunks)

    def query(self, query_embedding: List[float], top_k: int = 5, doc_id: Optional[str | List[str]] = None) -> Dict[str, Any]:
        """Query the vector store.
        
        Args:
            query_embedding: The query vector
            top_k: Number of results to return
            doc_id: Single doc_id string, list of doc_ids, or None for all documents
        """
        # Handle filtering based on doc_id parameter
        if doc_id is None:
            where = None  # Search all documents
        elif isinstance(doc_id, list):
            # Multi-document search: doc_id IN [doc_1, doc_2, doc_3]
            where = {"doc_id": {"$in": doc_id}}
        else:
            # Single document search: doc_id = "doc_1"
            where = {"doc_id": doc_id}
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        return results
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete all chunks for a given document ID from the vector store."""
        try:
            # Get all IDs for this document
            results = self.collection.get(
                where={"doc_id": doc_id},
                include=[]
            )
            
            if results and results.get("ids"):
                ids_to_delete = results["ids"]
                self.collection.delete(ids=ids_to_delete)
                return True
            return False
        except Exception:
            return False