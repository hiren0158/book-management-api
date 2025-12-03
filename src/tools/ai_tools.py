import os
import json
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def get_model():
    """Get Gemini model instance (creates new instance per call to avoid event loop issues)."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    
    # Configure API key (idempotent)
    genai.configure(api_key=api_key)
    
    return genai.GenerativeModel('gemini-2.0-flash')

async def recommend_books_ai(
    user_preferences: dict,
    available_books: list[dict],
    genre: Optional[str] = None,
    limit: int = 5
) -> list[int]:
    """Use Gemini AI to recommend books based on user preferences."""
    if not available_books:
        return []
    
    genre_filter = f"Only recommend books in the '{genre}' genre." if genre else ""
    
    prompt = f"""You are a book recommendation assistant. Based on user's reading history, recommend books.

User's reading history:
Borrowed books: {user_preferences.get('borrowed_books', [])}
Reviewed books: {user_preferences.get('reviewed_books', [])}

Available books:
{json.dumps(available_books, indent=2)}

{genre_filter}

Recommend {limit} books from the available books that match user preferences.
Return ONLY a valid JSON array of book IDs (integers). No markdown, no explanations.
Example: [1, 5, 8, 12, 15]
"""

    try:
        model = get_model()
        if not model:
            print("GEMINI_API_KEY not set. Skipping AI recommendation.")
            return []
        
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=200,
            )
        )

        content = response.text.strip()
        
        # Remove markdown formatting if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        recommended_ids = json.loads(content.strip())
        
        if not isinstance(recommended_ids, list):
            return []
        
        valid_ids = [
            int(book_id) for book_id in recommended_ids 
            if isinstance(book_id, (int, str)) and str(book_id).isdigit()
        ]
        
        return valid_ids[:limit]

    except Exception as e:
        print(f"AI recommendation error: {e}")
        return []


async def nl_to_filters(query: str, available_genres: list[str] = None, available_authors: list[str] = None) -> dict:
    """Convert natural language query to structured book filters using Gemini AI."""
    if not query or not query.strip():
        return {
            "author": None,
            "genre": None,
            "published_year": None,
            "search_query": None
        }
    
    # Use database genres if available, otherwise fallback to common genres
    if available_genres:
        genre_list = ", ".join(available_genres)
    else:
        genre_list = "Fiction, Non-Fiction, Mystery, Romance, Sci-Fi, Fantasy, Thriller, Biography, Historical, History, Science, Self-Help, Horror, Adventure, Poetry, Drama"
    
    prompt = f"""You are a filter extraction assistant for a book library API.
Convert this natural language query to structured book search filters.

Query: "{query}"

Extract the following fields:
- author (string or null): Author name if mentioned
- genre (string or null): Genre if mentioned. Use EXACTLY one of these genres from our database: {genre_list}
- published_year (integer or null): Year if mentioned
- search_query (string or null): Extract ONLY the essential keywords (2-5 words) for searching title/description. Remove filler words like "find me", "I want", "maybe", "something about", etc.

CRITICAL RULES for search_query:
- Extract ONLY the core subject matter keywords
- Remove all conversational filler ("find me", "I'm looking for", "maybe", "something about")
- Keep only nouns and key descriptive words (max 2-5 keywords)
- Focus on what the book is ABOUT, not how the user describes wanting it
- Examples of good keywords: "deep-sea expedition", "time travel romance", "medieval kingdom"
- Examples of bad keywords: "Find me a book about deep-sea expedition" (too long!)

Important rules for genre:
- Match the genre to the closest one in the list above
- For "historical fiction" or "history books" → use "Historical" if available
- For "science fiction", "sci-fi", "scifi", "sci-fic" → use "Science Fiction" (or "Sci-Fi" if that's what is in the list)
- Keep genres as they appear in the database list

For search_query normalization:
- CRITICAL: If the user uses "developing" or "development", CHANGE it to "developer" if searching for books about careers/people.
- For "coding", "code" is often better.
- Remove "professional" if it's just a descriptor, unless it's part of a specific title.

Return ONLY valid JSON in this exact format. No markdown, no explanations.
{{"author": null, "genre": null, "published_year": null, "search_query": null}}

Examples:
Query: "books by J.K. Rowling" -> {{"author": "J.K. Rowling", "genre": null, "published_year": null, "search_query": null}}
Query: "science fiction from 2020" -> {{"author": null, "genre": "Sci-Fi", "published_year": 2020, "search_query": null}}
Query: "mystery novels about detective" -> {{"author": null, "genre": "Mystery", "published_year": null, "search_query": "detective"}}
Query: "historical fiction medieval" -> {{"author": null, "genre": "Historical", "published_year": null, "search_query": "medieval"}}
Query: "Find me a high-intensity thriller set in dangerous natural environments, maybe something about an expedition gone terribly wrong underwater" -> {{"author": null, "genre": "Thriller", "published_year": null, "search_query": "expedition underwater"}}
Query: "I want a romance book with time travel and unexpected twists" -> {{"author": null, "genre": "Romance", "published_year": null, "search_query": "time travel"}}
"""

    try:
        model = get_model()
        if not model:
            print("GEMINI_API_KEY not set. Falling back to simple search.")
            return {
                "author": None,
                "genre": None,
                "published_year": None,
                "search_query": query
            }
        
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=150,
            )
        )

        content = response.text.strip()
        
        # Remove markdown formatting if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        filters = json.loads(content.strip())
        
        validated_filters = validate_filters(
            filters, 
            available_genres=available_genres,
            available_authors=available_authors
        )
        return validated_filters

    except Exception as e:
        # Check for event loop issues specifically
        if "Event loop is closed" in str(e):
            print(f"NL to filters error: Event loop is closed. This usually happens during tests if the loop is cleaned up too early.")
        else:
            print(f"NL to filters error: {e}")
            
        return {
            "author": None,
            "genre": None,
            "published_year": None,
            "search_query": query
        }


def _calculate_match_score(query: str, candidate: str) -> float:
    """
    Calculate fuzzy match score with enhanced prefix matching.
    
    Combines:
    - Character similarity (SequenceMatcher)
    - Prefix matching bonus
    - Length difference penalty
    
    Returns score between 0.0 and 1.0
    """
    from difflib import SequenceMatcher
    
    # Base similarity score
    similarity = SequenceMatcher(None, query, candidate).ratio()
    
    # Prefix matching bonus (typos are often at the end)
    min_len = min(len(query), len(candidate))
    if min_len >= 3:
        # Check how many characters match from the start
        prefix_match = 0
        for i in range(min_len):
            if query[i] == candidate[i]:
                prefix_match += 1
            else:
                break
        
        # Add bonus based on prefix match percentage
        prefix_ratio = prefix_match / min_len
        similarity += prefix_ratio * 0.15  # Up to 15% bonus
    
    # Length difference penalty (large length differences = less likely match)
    len_diff = abs(len(query) - len(candidate))
    max_len = max(len(query), len(candidate))
    if max_len > 0:
        len_penalty = (len_diff / max_len) * 0.1
        similarity -= len_penalty
    
    return max(0.0, min(1.0, similarity))




async def nl_to_sql_where(query: str) -> dict:
    """Convert natural language query to SQL WHERE clause using Gemini AI with security validation."""
    from src.utils.sql_validator import validate_where_clause
    
    if not query or not query.strip():
        return {
            "where_clause": None,
            "success": False,
            "error": "Query cannot be empty",
            "fallback_reason": "empty_query"
        }
    
    prompt = f"""You are an AI that converts natural language search queries into a SAFE and ACCURATE SQL WHERE clause for a book library system.

USER QUERY: "{query}"

DATABASE SCHEMA:
- Table: books
- Searchable columns: title, author, genre, description, published_date, isbn

CRITICAL RULES:

1. **STOP WORDS - IGNORE THESE:**
   Ignore: book, books, novel, related, releted, show, give, find, search, about, want, looking, for
   Only keep: meaningful topics (technology, python, thriller, history, romance, etc.)

2. **DO NOT HALLUCINATE GENRE VALUES:**
   ❌ NEVER invent genre names (e.g., "Health", "Business", "Fiction")
   ✅ Use the EXACT keywords from the user query
   ✅ Search across ALL fields (title, description, genre, author) with the SAME keyword
   
3. **SEARCH PATTERN (for each meaningful keyword):**
   ```
   (title ILIKE '%keyword%' OR description ILIKE '%keyword%' OR genre ILIKE '%keyword%' OR author ILIKE '%keyword%')
   ```

4. **AND vs OR LOGIC:**
   - Multiple topics → OR (user wants ANY match)
   - Topic + Author → AND
   - Topic + Year → AND

5. **DATES:**
   "from 2020" → EXTRACT(YEAR FROM published_date) = 2020
   
   **IMPORTANT - Year Abbreviations:**
   - "in 25" or "from 25" → means 2025 (current century)
   - "in 20" or "from 20" → means 2020 (current century)
   - Always interpret 2-digit years as 20XX
   
   **Date Ranges:**
   - "after 2020" → EXTRACT(YEAR FROM published_date) > 2020
   - "before 2020" → EXTRACT(YEAR FROM published_date) < 2020
   - "in first half of 2025" → EXTRACT(YEAR FROM published_date) = 2025 AND EXTRACT(MONTH FROM published_date) <= 6
   - "in second half of 2025" → EXTRACT(YEAR FROM published_date) = 2025 AND EXTRACT(MONTH FROM published_date) > 6

6. **OUTPUT:**
   Return ONLY the WHERE clause content (no "WHERE" keyword, no explanations)

EXAMPLES:

Query: "technology books"
Remove: "books" (stop word)
Keep: "technology"
→ title ILIKE '%technology%' OR description ILIKE '%technology%' OR genre ILIKE '%technology%' OR author ILIKE '%technology%'

Query: "thriller by king"  
Keep: "thriller", "king"
→ (title ILIKE '%thriller%' OR description ILIKE '%thriller%' OR genre ILIKE '%thriller%' OR author ILIKE '%thriller%') AND (author ILIKE '%king%')

Query: "python programming"
Keep: "python", "programming"
→ (title ILIKE '%python%' OR description ILIKE '%python%' OR genre ILIKE '%python%' OR author ILIKE '%python%') OR (title ILIKE '%programming%' OR description ILIKE '%programming%' OR genre ILIKE '%programming%' OR author ILIKE '%programming%')

Query: "books published in 25 after second half"
Extract: year = 2025 (25 → 2025), second half (month > 6)
→ EXTRACT(YEAR FROM published_date) = 2025 AND EXTRACT(MONTH FROM published_date) > 6

Query: "fiction from 2020"
→ (title ILIKE '%fiction%' OR description ILIKE '%fiction%' OR genre ILIKE '%fiction%' OR author ILIKE '%fiction%') AND EXTRACT(YEAR FROM published_date) = 2020

NOW GENERATE FOR: "{query}"
Return ONLY the SQL WHERE clause.
"""

    try:
        model = get_model()
        if not model:
            return {
                "where_clause": None,
                "success": False,
                "error": "GEMINI_API_KEY not set",
                "fallback_reason": "api_key_missing"
            }
        
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,  # Lower temperature for more deterministic output
                max_output_tokens=300,
            )
        )

        content = response.text.strip()
        
        # Remove markdown formatting if present
        if content.startswith("```sql"):
            content = content[6:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        where_clause = content.strip()
        
        # Remove 'WHERE' keyword if Gemini included it
        if where_clause.upper().startswith('WHERE '):
            where_clause = where_clause[6:].strip()
        
        # Validate the generated WHERE clause
        is_valid, validation_msg = validate_where_clause(where_clause)
        
        if not is_valid:
            return {
                "where_clause": None,
                "success": False,
                "error": f"Generated WHERE clause failed validation: {validation_msg}",
                "fallback_reason": "validation_failed",
                "attempted_clause": where_clause
            }
        
        # Apply fuzzy matching to author and genre values in the WHERE clause
        # This helps handle typos like "hirenn" → "Hiren Patel"
        corrected_clause = await _apply_fuzzy_matching_to_where_clause(where_clause)
        
        return {
            "where_clause": corrected_clause,
            "success": True,
            "error": None,
            "fallback_reason": None
        }

    except Exception as e:
        error_msg = str(e)
        
        # Determine fallback reason
        if "quota" in error_msg.lower() or "429" in error_msg:
            fallback_reason = "quota_exceeded"
        elif "event loop" in error_msg.lower():
            fallback_reason = "event_loop_error"
        else:
            fallback_reason = "gemini_error"
        
        return {
            "where_clause": None,
            "success": False,
            "error": error_msg,
            "fallback_reason": fallback_reason
        }


async def _apply_fuzzy_matching_to_where_clause(where_clause: str) -> str:
    """
    Apply fuzzy matching to author and genre values in a WHERE clause.
    Handles typos like 'hirenn' → 'Hiren Patel', 'sci-fic' → 'Science Fiction'
    
    Args:
        where_clause: SQL WHERE clause with potential typos
        
    Returns:
        WHERE clause with corrected author/genre names
    """
    import re
    from src.repository.book import BookRepository
    from src.core.database import get_session
    
    # Extract author and genre values from ILIKE patterns
    # Pattern: author ILIKE '%value%' or genre ILIKE '%value%'
    author_pattern = r"author\s+ILIKE\s+'%([^%]+)%'"
    genre_pattern = r"genre\s+ILIKE\s+'%([^%]+)%'"
    
    author_matches = re.findall(author_pattern, where_clause, re.IGNORECASE)
    genre_matches = re.findall(genre_pattern, where_clause, re.IGNORECASE)
    
    # If no author or genre matches, return as is
    if not author_matches and not genre_matches:
        return where_clause
    
    # Get database values for fuzzy matching
    session_gen = get_session()
    session = await anext(session_gen)
    try:
        repo = BookRepository(session)
        available_authors = await repo.get_all_authors()
        available_genres = await repo.get_all_genres()
    finally:
        await session_gen.aclose()
    
    corrected_clause = where_clause
    
    # Apply fuzzy matching to author values
    for author_value in author_matches:
        # Use the same fuzzy matching logic from validate_filters
        corrected_author = _fuzzy_match_author(author_value, available_authors)
        if corrected_author and corrected_author != author_value:
            # Replace the typo with the corrected value
            old_pattern = f"author ILIKE '%{author_value}%'"
            new_pattern = f"author ILIKE '%{corrected_author}%'"
            corrected_clause = corrected_clause.replace(old_pattern, new_pattern)
            print(f"Fuzzy matched author '{author_value}' → '{corrected_author}'")
    
    # Apply fuzzy matching to genre values
    for genre_value in genre_matches:
        corrected_genre = _fuzzy_match_genre(genre_value, available_genres)
        if corrected_genre and corrected_genre != genre_value:
            # Replace the typo with the corrected value
            old_pattern = f"genre ILIKE '%{genre_value}%'"
            new_pattern = f"genre ILIKE '%{corrected_genre}%'"
            corrected_clause = corrected_clause.replace(old_pattern, new_pattern)
            print(f"Fuzzy matched genre '{genre_value}' → '{corrected_genre}'")
    
    return corrected_clause


def _fuzzy_match_author(author: str, available_authors: list[str]) -> str:
    """Fuzzy match author name against database authors"""
    from difflib import SequenceMatcher
    
    # Try exact match first (case-insensitive)
    exact_match = next(
        (a for a in available_authors if a.lower() == author.lower()),
        None
    )
    if exact_match:
        return exact_match
    
    # Smart fuzzy matching
    best_match = None
    best_score = 0
    
    for full_name in available_authors:
        candidates = [full_name] + full_name.split()
        
        for candidate in candidates:
            score = SequenceMatcher(None, author.lower(), candidate.lower()).ratio()
            
            # Bonus for matching first names
            if candidate == full_name.split()[0]:
                score += 0.1
            
            if score > best_score:
                best_score = score
                best_match = full_name
    
    # Accept match if score is good enough
    if best_score >= 0.65:
        return best_match
    
    return author  # Return original if no good match


def _fuzzy_match_genre(genre: str, available_genres: list[str]) -> str:
    """Fuzzy match genre against database genres"""
    from difflib import get_close_matches
    
    # Try exact match first
    exact_match = next(
        (g for g in available_genres if g.lower() == genre.lower()),
        None
    )
    if exact_match:
        return exact_match
    
    # Check for substring matches (e.g., "sci" in "Sci-Fi")
    genre_lower = genre.lower()
    for g in available_genres:
        if genre_lower in g.lower() or g.lower() in genre_lower:
            # Only match if significant overlap
            overlap_len = min(len(genre_lower), len(g.lower()))
            if overlap_len / max(len(genre_lower), len(g.lower())) >= 0.6:
                return g
    
    # Fuzzy matching with STRICT cutoff (0.75 = must be 75% similar)
    # This prevents nonsense matches like "science fiction" → "Education"
    matches = get_close_matches(genre, available_genres, n=1, cutoff=0.75)
    if matches:
        return matches[0]
    
    return genre  # Return original if no good match


def validate_filters(filters: dict, available_genres: list[str] = None, available_authors: list[str] = None) -> dict:

    """
    Validate and sanitize AI-generated filters with fuzzy matching for genres and authors.
    
    Args:
        filters: Raw filters from AI
        available_genres: List of genres from database (dynamic)
        available_authors: List of authors from database (dynamic)
    
    Returns:
        Validated filters dict
    """
    from difflib import get_close_matches
    
    validated = {
        "author": None,
        "genre": None,
        "published_year": None,
        "search_query": None
    }
    
    # Validate and fuzzy match author
    if isinstance(filters.get("author"), str):
        author = filters["author"].strip()
        
        if not author:
            validated["author"] = None
        elif available_authors:
            # Try exact match first (case-insensitive)
            exact_match = next(
                (a for a in available_authors if a.lower() == author.lower()),
                None
            )
            
            if exact_match:
                validated["author"] = exact_match
            else:
                # Smart fuzzy matching with custom scoring
                best_match = None
                best_score = 0
                
                for full_name in available_authors:
                    # Try matching against full name and individual words
                    candidates = [full_name] + full_name.split()
                    
                    for candidate in candidates:
                        score = _calculate_match_score(author.lower(), candidate.lower())
                        
                        # Bonus for matching first names (first word in full name)
                        if candidate == full_name.split()[0]:
                            score += 0.1
                        
                        if score > best_score:
                            best_score = score
                            best_match = full_name
                
                # Accept match if score is good enough
                if best_score >= 0.65:  # 65% threshold
                    validated["author"] = best_match
                    print(f"Fuzzy matched author '{author}' to '{best_match}' (score: {best_score:.2f})")
                elif len(author) <= 200:
                    # Accept any reasonable author name for ILIKE partial match
                    validated["author"] = author
        else:
            # No database authors available, accept if reasonable length
            if len(author) <= 200:
                validated["author"] = author
    
    if isinstance(filters.get("genre"), str):
        genre = filters["genre"].strip()
        
        if not genre:
            validated["genre"] = None
        elif available_genres:
            # Try exact match first (case-insensitive)
            exact_match = next(
                (g for g in available_genres if g.lower() == genre.lower()),
                None
            )
            
            if exact_match:
                validated["genre"] = exact_match
            else:
                # Try fuzzy matching with database genres
                # get_close_matches returns best matches sorted by similarity
                matches = get_close_matches(
                    genre, 
                    available_genres, 
                    n=1,  # Get top 1 match
                    cutoff=0.4  # Lowered threshold to catch "sci-fic" -> "Science Fiction"
                )
                
                if matches:
                    validated["genre"] = matches[0]
                    print(f"Fuzzy matched '{genre}' to '{matches[0]}'")
                elif len(genre) <= 50:
                    # Accept any reasonable genre even if not in DB
                    # (useful for partial matching with ILIKE)
                    validated["genre"] = genre
        else:
            # No database genres available, accept if reasonable length
            if len(genre) <= 50:
                validated["genre"] = genre
    
    if isinstance(filters.get("published_year"), (int, str)):
        try:
            year = int(filters["published_year"])
            if 1000 <= year <= 2100:
                validated["published_year"] = year
        except (ValueError, TypeError):
            pass
    
    if isinstance(filters.get("search_query"), str):
        search = filters["search_query"].strip()
        if search and len(search) <= 500:
            validated["search_query"] = search
    
    return validated
