from typing import Dict, Any, Optional
import re
import os

from don.intent_parser import parse_intent
from don.comms_ai import GeminiClient
from don.config import load_settings, get_env_text
from don.logging_utils import setup_logging
from don.safety import is_simulation_mode

logger = setup_logging()


def parse(text: str) -> Dict[str, Any]:
    """
    Parse user text into intent JSON.
    
    Args:
        text: User input text
        
    Returns:
        Dict containing intent information
    """
    # First try deterministic parser
    intent_data = parse_intent(text)
    
    # If in simulation mode or if confidence is low, use deterministic parser only
    if is_simulation_mode() or intent_data.get("confidence", 0) < 0.7:
        return intent_data
    
    # Try Gemini-based parsing for higher accuracy when not in simulation mode
    try:
        gemini_api_key = get_env_text("GEMINI_API_KEY")
        if gemini_api_key:
            gemini = GeminiClient(gemini_api_key)
            # This would be implemented when Gemini integration is added
            # For now, we'll just return the deterministic result
            logger.info("Gemini-based intent parsing would be used here if configured")
    except Exception as e:
        logger.warning(f"Gemini parsing failed: {e}")
    
    return intent_data


def parse_with_fuzzy_heuristics(text: str) -> Dict[str, Any]:
    """
    Parse intent using regex/fuzzy heuristics for offline mode.
    
    Args:
        text: User input text
        
    Returns:
        Dict containing intent information
    """
    # This is essentially the same as the deterministic parser
    # but we can add additional fuzzy matching logic here
    return parse_intent(text)


def get_intent_schema() -> Dict[str, Any]:
    """
    Return the intent schema for reference.
    
    Returns:
        Dict containing the intent schema
    """
    return {
        "intent": "string",
        "confidence": "float",
        "channel": "string",
        "contact": "string",
        "message": "string",
        "app": "string",
        "path": "string",
        "action": "string",
        "raw": "string"
    }