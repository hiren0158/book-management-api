import os
import json
import logging
import google.generativeai as genai
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Cached model instance
_model_instance: Optional[genai.GenerativeModel] = None
_configured = False

def get_gemini_model() -> genai.GenerativeModel:
    """Lazy initialization of Gemini API and model.
    
    This function is called only when the model is actually needed,
    avoiding initialization overhead during application startup.
    """
    global _model_instance, _configured
    
    if _model_instance is not None:
        return _model_instance
    
    # Load environment variables only when needed
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not _configured:
        if api_key:
            genai.configure(api_key=api_key)
            # Mask the API key for security (show first 8 and last 4 characters)
            masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***MASKED***"
            logger.info(f"✓ Gemini API configured with key: {masked_key}")
        else:
            logger.warning("✗ GEMINI_API_KEY not found in environment variables")
        _configured = True
    
    # Use a lightweight model for speed
    _model_instance = genai.GenerativeModel('gemini-2.0-flash')
    return _model_instance

async def parse_natural_language_query(text: str) -> Dict[str, Any]:
    # Get lazily initialized model
    model = get_gemini_model()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not found.")
        return {}

    prompt = f"""
    You are a smart search parser for a book library API.
    Analyze the user's natural language query and extract structured search filters.

    Target Fields:
    - "q": General keywords, topics, or title fragments.
    - "author": Name of the author.
    - "genre": Book genre (e.g., Fiction, History, Science).
    - "published_year": Publication year (integer).
    - "sort_order": "asc" (for oldest/first) or "desc" (for newest/latest).

    Rules:
    1. Output ONLY a valid JSON object. No markdown, no explanations.
    2. If a field is not mentioned, omit it.
    3. Infer genre if the user mentions a category (e.g., "history books" -> genre: "History").
    4. "books about X" usually means "q": "X" unless X is clearly a genre.

    User Query: "{text}"
    JSON Output:
    """

    try:
        response = await model.generate_content_async(prompt)
        content = response.text.strip()
        
        # Remove markdown formatting if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        return json.loads(content.strip())
    except Exception as e:
        print(f"AI Search Error: {e}")
        # Fallback: treat the whole text as a general query
        return {"q": text}
