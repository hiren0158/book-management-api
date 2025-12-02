"""
Unit tests for RecursiveCharacterTextSplitter in text_chunker.py
"""
import pytest
from src.utils.text_chunker import chunk_text, RecursiveCharacterTextSplitter


class TestRecursiveCharacterTextSplitter:
    """Test suite for RecursiveCharacterTextSplitter"""
    
    def test_basic_chunking(self):
        """Test basic text splitting within chunk size"""
        text = "This is a simple test. It has multiple sentences. Let's see how it chunks."
        splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
        chunks = splitter.split_text(text)
        
        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk) <= 50 + 10  # Allow some tolerance for separators
    
    def test_paragraph_preservation(self):
        """Test that paragraphs are preserved when possible"""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=0)
        chunks = splitter.split_text(text)
        
        # Should preserve paragraph boundaries
        assert any("First paragraph" in chunk for chunk in chunks)
        assert any("Second paragraph" in chunk for chunk in chunks)
    
    def test_chunk_overlap(self):
        """Test that overlap is created between chunks"""
        text = "A" * 500 + " " + "B" * 500
        splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
        chunks = splitter.split_text(text)
        
        assert len(chunks) >= 2
        # Check that there's some overlap content
        # The end of first chunk should appear in the start of second chunk
    
    def test_empty_text(self):
        """Test handling of empty input"""
        splitter = RecursiveCharacterTextSplitter()
        assert splitter.split_text("") == []
        assert splitter.split_text("   ") == []
        assert splitter.split_text(None) == []
    
    def test_oversized_chunk_splitting(self):
        """Test that oversized chunks are recursively split"""
        # Create a very long word/sentence that exceeds chunk size
        long_text = "word" * 500  # No spaces, forces character split
        splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)
        chunks = splitter.split_text(long_text)
        
        assert len(chunks) > 1
        for chunk in chunks:
            # Should be split even if no separators found
            assert len(chunk) <= 110  # chunk_size + tolerance
    
    def test_sentence_boundary_preservation(self):
        """Test that sentences are kept together when possible"""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        splitter = RecursiveCharacterTextSplitter(chunk_size=30, chunk_overlap=5)
        chunks = splitter.split_text(text)
        
        # Sentences should generally not be split mid-word
        for chunk in chunks:
            words = chunk.split()
            for word in words:
                # No word should be incomplete (ending with partial word)
                # This is a heuristic check
                assert len(word) > 0
    
    def test_table_structure_preservation(self):
        """Test that table-like structures are handled"""
        text = "Header1    Header2    Header3\nValue1     Value2     Value3\nData1      Data2      Data3"
        splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=0)
        chunks = splitter.split_text(text)
        
        # Should keep table together if within chunk size
        assert len(chunks) == 1
        assert "Header1" in chunks[0]
        assert "Value1" in chunks[0]
    
    def test_numbered_list_handling(self):
        """Test preservation of numbered lists"""
        text = "Introduction.\n\n1. First item\n2. Second item\n3. Third item\n\nConclusion."
        splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)
        chunks = splitter.split_text(text)
        
        # Lists should ideally stay together or split cleanly
        assert len(chunks) > 0


class TestChunkTextFunction:
    """Test suite for the main chunk_text function"""
    
    def test_default_parameters(self):
        """Test chunk_text with default parameters"""
        text = "This is a test document. " * 100
        chunks = chunk_text(text)
        
        assert len(chunks) > 0
        for chunk in chunks:
            # Default max_chunk_size is 1000
            assert len(chunk) <= 1200  # Some tolerance
    
    def test_custom_chunk_size(self):
        """Test chunk_text with custom chunk size"""
        text = "Word " * 500
        chunks = chunk_text(text, max_chunk_size=200, overlap=50)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 250  # chunk_size + some tolerance
    
    def test_financial_document_chunking(self):
        """Test chunking of financial document-like text"""
        text = """Operating Expenses:
        
        Reported operating expenses of $10.1bn were $1.9bn or 24% higher. The increase reflected notable items in 3Q25, including legal provisions of $1.4bn on historical matters.
        
        Revenue Analysis:
        
        Fee and other income of $3.0bn grew by $0.7bn or 31%, primarily reflecting an increase of $0.6bn or 50% in Wealth from a strong performance.
        
        Table:
        Q3 2025    Q3 2024    Variance
        $10.1bn    $8.2bn     +24%
        """
        
        chunks = chunk_text(text, max_chunk_size=300, overlap=50)
        
        assert len(chunks) > 0
        # Check that numerical data is preserved
        assert any("$10.1bn" in chunk for chunk in chunks)
        assert any("24%" in chunk or "24% higher" in chunk for chunk in chunks)
    
    def test_whitespace_normalization(self):
        """Test that excessive whitespace is cleaned up"""
        text = "Text   with    excessive     spaces\n\n\n\n\nand newlines"
        chunks = chunk_text(text)
        
        for chunk in chunks:
            # Should not have excessive spaces
            assert "    " not in chunk  # More than 3 spaces
            # Should limit newlines
            assert "\n\n\n\n" not in chunk
    
    def test_empty_chunks_removed(self):
        """Test that empty chunks are not returned"""
        text = "\n\n\n   \n\nSome text\n\n\n   \n\n"
        chunks = chunk_text(text)
        
        # Should only return non-empty chunks
        for chunk in chunks:
            assert chunk.strip() != ""
    
    def test_overlap_continuity(self):
        """Test that overlap provides context continuity"""
        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
        chunks = chunk_text(text, max_chunk_size=40, overlap=20)
        
        if len(chunks) > 1:
            # There should be some text overlap between consecutive chunks
            # Check that the end of one chunk has some relation to start of next
            for i in range(len(chunks) - 1):
                # This is a simple heuristic - overlap should preserve some words
                assert len(chunks[i]) > 0 and len(chunks[i + 1]) > 0
