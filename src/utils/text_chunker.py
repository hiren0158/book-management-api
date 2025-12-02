from typing import List
import re


class RecursiveCharacterTextSplitter:
    """
    Recursively splits text using a hierarchy of separators to maintain semantic coherence.
    
    This splitter is optimized for financial documents and structured text, preserving:
    - Table structures
    - Numbered lists and bullet points
    - Headers and sections
    - Paragraph boundaries
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None,
        keep_separator: bool = True
    ):
        """
        Initialize the RecursiveCharacterTextSplitter.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            separators: List of separators in priority order (default: paragraph, newline, sentence, space)
            keep_separator: Whether to keep separators in the output chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.keep_separator = keep_separator
        
        # Default separators in priority order
        self.separators = separators or [
            "\n\n\n",  # Section breaks (triple newline)
            "\n\n",    # Paragraph breaks (double newline)
            "\n",      # Line breaks
            ". ",      # Sentence ends
            "; ",      # Semicolon breaks
            ", ",      # Comma breaks
            " ",       # Word breaks
            ""         # Character splits (last resort)
        ]
    
    def split_text(self, text: str) -> List[str]:
        """Split text into chunks using recursive strategy."""
        if not text or not text.strip():
            return []
        
        return self._split_text_recursive(text, self.separators)
    
    def _split_text_recursive(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text using separators in priority order."""
        chunks = []
        
        if not separators:
            # No more separators, split by character
            return self._split_by_character(text)
        
        separator = separators[0]
        remaining_separators = separators[1:]
        
        # Split by the current separator
        if separator:
            splits = self._split_with_separator(text, separator)
        else:
            splits = list(text)
        
        # Merge splits into chunks
        current_chunk = []
        current_length = 0
        
        for split in splits:
            split_len = len(split)
            
            # If this split alone exceeds chunk_size, we need to split it further
            if split_len > self.chunk_size:
                if current_chunk:
                    # Save current chunk
                    chunks.append(self._join_chunks(current_chunk, separator))
                    current_chunk = []
                    current_length = 0
                
                # Recursively split the oversized piece
                sub_chunks = self._split_text_recursive(split, remaining_separators)
                chunks.extend(sub_chunks)
                continue
            
            # If adding this split would exceed chunk_size, start new chunk
            if current_length + split_len > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = self._join_chunks(current_chunk, separator)
                chunks.append(chunk_text)
                
                # Handle overlap
                current_chunk = self._create_overlap_chunk(current_chunk, separator)
                current_length = sum(len(s) for s in current_chunk)
                if separator and self.keep_separator:
                    current_length += len(separator) * (len(current_chunk) - 1)
            
            current_chunk.append(split)
            current_length += split_len
            if separator and self.keep_separator and len(current_chunk) > 1:
                current_length += len(separator)
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(self._join_chunks(current_chunk, separator))
        
        return chunks
    
    def _split_with_separator(self, text: str, separator: str) -> List[str]:
        """Split text by separator, optionally keeping the separator."""
        if self.keep_separator:
            # Split but keep separator with the preceding text
            parts = text.split(separator)
            result = []
            for i, part in enumerate(parts):
                if i < len(parts) - 1:
                    result.append(part + separator)
                elif part:  # Last part, only add if non-empty
                    result.append(part)
            return [p for p in result if p]
        else:
            return [p for p in text.split(separator) if p]
    
    def _join_chunks(self, chunks: List[str], separator: str) -> str:
        """Join chunks, handling separator appropriately."""
        if not chunks:
            return ""
        
        # If separator was kept in chunks, just concatenate
        if self.keep_separator:
            return "".join(chunks)
        else:
            return separator.join(chunks)
    
    def _create_overlap_chunk(self, chunks: List[str], separator: str) -> List[str]:
        """Create overlap from the end of current chunks."""
        if not chunks or self.chunk_overlap <= 0:
            return []
        
        overlap_chunks = []
        overlap_length = 0
        
        # Take chunks from the end until we reach overlap size
        for chunk in reversed(chunks):
            chunk_len = len(chunk)
            if overlap_length + chunk_len > self.chunk_overlap:
                break
            overlap_chunks.insert(0, chunk)
            overlap_length += chunk_len
            if separator and self.keep_separator:
                overlap_length += len(separator)
        
        return overlap_chunks
    
    def _split_by_character(self, text: str) -> List[str]:
        """Split text by character when no other separators work."""
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            end = min(i + self.chunk_size, len(text))
            chunks.append(text[i:end])
        return chunks


def chunk_text(text: str, max_chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks using recursive character splitting strategy.
    
    This function uses a RecursiveCharacterTextSplitter that:
    - Preserves semantic boundaries (paragraphs, sentences, etc.)
    - Maintains document structure (tables, lists, headers)
    - Creates intelligent overlaps for context continuity
    
    Args:
        text: Input text to chunk
        max_chunk_size: Maximum size of each chunk in characters (default: 1000)
        overlap: Number of characters to overlap between chunks (default: 200)
    
    Returns:
        List of text chunks with semantic boundaries preserved
    """
    text = text or ""
    if not text.strip():
        return []
    
    # Use RecursiveCharacterTextSplitter for better semantic chunking
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chunk_size,
        chunk_overlap=overlap,
        keep_separator=True
    )
    
    chunks = splitter.split_text(text)
    
    # Final cleanup: remove extra whitespace while preserving structure
    cleaned_chunks = []
    for chunk in chunks:
        # Normalize excessive whitespace but preserve single newlines and paragraph breaks
        chunk = re.sub(r' +', ' ', chunk)  # Multiple spaces to single space
        chunk = re.sub(r'\n{4,}', '\n\n', chunk)  # Reduce excessive newlines (changed from 3 to 2)
        
        # Clean up spaces around newlines
        chunk = re.sub(r' +\n', '\n', chunk)  # Remove trailing spaces before newlines
        chunk = re.sub(r'\n +', '\n', chunk)  # Remove leading spaces after newlines
        
        chunk = chunk.strip()
        if chunk:
            cleaned_chunks.append(chunk)
    
    return cleaned_chunks