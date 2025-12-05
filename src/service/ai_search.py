import os
import logging
import google.generativeai as genai
from typing import Optional

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
