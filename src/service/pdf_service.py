import io
from typing import Optional
from fastapi import UploadFile
import fitz  # PyMuPDF


def clean_pdf_text(text: str) -> str:
    """Clean extracted PDF text with enhanced handling for financial documents.
    
    Improvements for financial documents:
    - Preserve table structures and formatting
    - Better handling of numerical data (currency, percentages, negatives in parentheses)
    - Preserve headers and section markers
    - Fix broken words and hyphenation
    - Normalize spacing intelligently around numbers and symbols
    - Better handling of bullet points and numbered lists
    """
    import re

    if not text:
        return ""

    s = text.replace("\r\n", "\n").replace("\r", "\n")
    # Remove soft hyphens
    s = s.replace("\u00AD", "")
    
    # Preserve section headers (lines that are short and end with colon or are all caps)
    header_pattern = r"^([A-Z][A-Za-z\s&]{2,50}:)\s*$"
    s = re.sub(header_pattern, r"###HEADER###\1###HEADER###", s, flags=re.MULTILINE)
    
    # 1) Join hyphenated words across lines: "word-\nnext" -> "wordnext"
    s = re.sub(r"(?<=[a-zA-Z])\s*-\s*\n\s*(?=[a-zA-Z])", "", s)

    # 2) Detect and preserve table-like structures
    lines = s.split('\n')
    processed_lines = []
    for line in lines:
        # Check if this looks like a table row (multiple tab-separated or multi-space separated values)
        if re.search(r'\t{1,}|\s{3,}', line) and re.search(r'\d', line):
            processed_lines.append(f"###TABLE###{line}###TABLE###")
        else:
            processed_lines.append(line)
    s = '\n'.join(processed_lines)

    # 3) Fix broken words and intelligently merge lines
    lines = s.split('\n')
    result_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines (preserve as paragraph breaks)
        if not line:
            result_lines.append('')
            i += 1
            continue
        
        # Check if line is a header, table marker, or list item (preserve newlines)
        if (line.startswith('###') or 
            re.match(r'^\s*[•\-\*\d]+[\.\)]\s', line) or  # List items
            re.match(r'^[A-Z][A-Za-z\s&]{2,50}:$', line)):  # Headers
            result_lines.append(line)
            i += 1
            continue
        
        # For normal text, check if we should merge with next line
        if i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            
            # Merge if:
            # - Current line doesn't end with sentence terminator
            # - Next line exists and starts with lowercase (continuation)
            # - Neither line is empty or a special marker
            if (next_line and 
                not re.search(r'[.!?:;]$', line) and
                next_line[0].islower() and
                not next_line.startswith('###')):
                # Merge lines with a space
                line = line + ' ' + next_line
                i += 2  # Skip the next line since we merged it
                result_lines.append(line)
                continue
        
        result_lines.append(line)
        i += 1
    
    s = '\n'.join(result_lines)

    # Limit excessive paragraph breaks
    s = re.sub(r"\n{4,}", "\n\n\n", s)


    # 4) Fix merged words using wordninja library
    # This handles PDFs where spaces are missing between words
    # Examples: "yearover" -> "year over", "double-digitgrowth" -> "double-digit growth"
    
    import wordninja
    
    def split_merged_words_with_wordninja(text):
        """Split merged words while preserving intentional compound words and proper formatting."""
        lines = text.split('\n')
        result_lines = []
        
        for line in lines:
            # Skip lines that are mostly numbers, tables, or special markers
            if line.startswith('###') or re.match(r'^[\d\s\.,\-\$%]+$', line):
                result_lines.append(line)
                continue
            
            # Split line into words
            words = line.split()
            fixed_words = []
            
            for word in words:
                # Skip short words, numbers, or words with punctuation/special chars
                if (len(word) <= 4 or 
                    any(c.isdigit() for c in word) or 
                    any(c in '.,;:!?()[]{}/$%&@#' for c in word)):
                    fixed_words.append(word)
                    continue
                
                # Check if word looks like it might be merged (all lowercase, long)
                if word.islower() and len(word) > 8:
                    # Use wordninja to split it
                    split_parts = wordninja.split(word)
                    
                    # Only use the split if it actually found multiple words
                    if len(split_parts) > 1:
                        fixed_words.append(' '.join(split_parts))
                    else:
                        fixed_words.append(word)
                else:
                    fixed_words.append(word)
            
            result_lines.append(' '.join(fixed_words))
        
        return '\n'.join(result_lines)
    
    s = split_merged_words_with_wordninja(s)

    # Restore headers but clean up markers
    s = s.replace('###HEADER###', '')
    
    # Clean line spacing
    s = re.sub(r"[ \t]*\n[ \t]*", "\n", s)
    
    # Preserve bullet points and numbered lists
    s = re.sub(r"\n([•\-\*])\s*", r"\n\1 ", s)
    s = re.sub(r"\n(\d+\.)\s*", r"\n\1 ", s)

    return s.strip()


async def extract_text_from_pdf(file: UploadFile) -> tuple[str, list[tuple[str, int]]]:
    """Extract text from an uploaded PDF file asynchronously using PyMuPDF (fitz)
    and apply cleaning to fix spacing and broken words.
    
    Returns:
        tuple: (cleaned_text, page_segments)
            - cleaned_text: The full extracted and cleaned text
            - page_segments: List of (text_segment, page_number) tuples
    """
    data = await file.read()
    page_segments: list[tuple[str, int]] = []
    
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page_num, page in enumerate(doc, start=1):
            import re
            page_height = page.rect.height
            blocks = page.get_text("blocks")
            filtered = []
            for blk in blocks:
                x0, y0, x1, y1, b_text, *_ = blk
                # Skip headers/footers
                if y0 < 50 or (page_height - y1) < 50:
                    continue
                # Remove page-number-only lines
                lines = [ln for ln in str(b_text).splitlines() if not re.fullmatch(r"\s*\d+\s*", ln)]
                bt = "\n\n".join(lines).strip()
                if bt:
                    filtered.append(bt)
            page_text = "\n\n".join(filtered)
            if page_text:
                page_segments.append((page_text, page_num))

    # Combine all text for cleaning
    raw_text = "\n\n".join([text for text, _ in page_segments])
    cleaned_text = clean_pdf_text(raw_text)
    
    return cleaned_text, page_segments