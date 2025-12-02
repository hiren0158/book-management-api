from __future__ import annotations
from typing import List, Optional
import threading


class EmbeddingService:
    """Singleton-style embedding service using BAAI/bge-small-en-v1.5."""

    _instance: Optional[EmbeddingService] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        # Lazy import to avoid loading heavy ML model during application startup
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")

    @classmethod
    def instance(cls) -> "EmbeddingService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = EmbeddingService()
        return cls._instance

    def embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        """Embed document chunks; L2-normalized for cosine similarity."""
        return self.model.encode(chunks, normalize_embeddings=True).tolist()

    def embed_query(self, query: str) -> List[float]:
        """Embed a query with BGE recommended prefix and normalization."""
        text = f"query: {query.strip()}"
        return self.model.encode([text], normalize_embeddings=True)[0].tolist()