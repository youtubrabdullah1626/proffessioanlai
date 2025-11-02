from typing import Optional, List
import re
from rapidfuzz import fuzz

from don.whatsapp_automation import WhatsAppAutomation
from don.config import load_settings
from don.memory_manager import load_m1
from don.logging_utils import setup_logging

logger = setup_logging()


def send_text(contact: str, message: str, prefer_web: bool = False) -> bool:
    """
    Send a text message to a contact via WhatsApp.
    
    Args:
        contact: Contact name or phone number
        message: Message to send
        prefer_web: Whether to prefer web mode over desktop
        
    Returns:
        bool: True if successful
    """
    settings = load_settings()
    wa = WhatsAppAutomation(settings)
    return wa.send_text(contact, message, prefer_web)


def send_media(contact: str, path: str, kind: str = "image", prefer_web: bool = False) -> bool:
    """
    Send media to a contact via WhatsApp.
    
    Args:
        contact: Contact name or phone number
        path: Path to media file
        kind: Type of media (image, video, document)
        prefer_web: Whether to prefer web mode over desktop
        
    Returns:
        bool: True if successful
    """
    settings = load_settings()
    wa = WhatsAppAutomation(settings)
    return wa.send_media(contact, path, kind, prefer_web)


def fuzzy_match_contact(contact: str) -> str:
    """
    Fuzzy match contact name with known contacts.
    
    Args:
        contact: Contact name to match
        
    Returns:
        str: Best matching contact name or original if no match
    """
    try:
        # Load known contacts from memory
        memory = load_m1()
        nicknames = memory.get("nicknames", {})
        
        # Get all known contact names
        known_contacts = list(nicknames.keys())
        
        # If contact is already a known nickname, return it
        if contact.lower() in nicknames:
            return contact
        
        # Try fuzzy matching
        best_match = None
        best_score = 0
        
        for known_contact in known_contacts:
            score = fuzz.ratio(contact.lower(), known_contact.lower())
            if score > best_score and score > 70:  # Threshold for matching
                best_score = score
                best_match = known_contact
                
        if best_match:
            logger.info(f"Fuzzy matched '{contact}' to '{best_match}' (score: {best_score})")
            return best_match
            
        # No good match found, return original
        return contact
    except Exception as e:
        logger.error(f"Fuzzy contact matching failed: {e}")
        return contact


def log_send(contact: str, kind: str, snippet: str) -> None:
    """
    Log a WhatsApp send operation (masking phone numbers).
    
    Args:
        contact: Contact name
        kind: Type of message (text, image, etc.)
        snippet: Message snippet (will be masked)
    """
    try:
        # Mask phone numbers in snippet
        masked_snippet = re.sub(r'\+?\d[\d\s\-()]{8,}', '***-***-****', snippet)
        logger.info(f"WhatsApp send logged: {contact} [{kind}] -> {masked_snippet}")
    except Exception as e:
        logger.error(f"Failed to log send operation: {e}")


def ocr_fallback_needed() -> bool:
    """
    Determine if OCR fallback is needed.
    
    Returns:
        bool: True if OCR fallback should be used
    """
    # This would check system conditions to determine if OCR is needed
    # For now, we'll return False as a default
    return False


def get_contact_phone(contact: str) -> Optional[str]:
    """
    Get phone number for a contact.
    
    Args:
        contact: Contact name
        
    Returns:
        Optional[str]: Phone number or None if not found
    """
    try:
        memory = load_m1()
        nicknames = memory.get("nicknames", {})
        return nicknames.get(contact.lower())
    except Exception as e:
        logger.error(f"Failed to get contact phone: {e}")
        return None