import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the don directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'don'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from don.whatsapp_automation import WhatsAppAutomation
from don.config import Settings, TTSSettings
from commands.whatsapp_handlers import fuzzy_match_contact, log_send, ocr_fallback_needed, get_contact_phone


def test_whatsapp_automation_initialization():
    """Test WhatsApp automation initialization."""
    settings = Settings(
        whatsapp_desktop_paths=[],
        chrome_profile_path="",
        similarity_threshold=0.8,
        language="en",
        wake_words=[],
        tts=TTSSettings()
    )
    wa = WhatsAppAutomation(settings)
    assert wa is not None
    assert hasattr(wa, 'settings')
    assert hasattr(wa, 'auto_reply_enabled')
    assert hasattr(wa, 'send_logs')


def test_fuzzy_match_contact():
    """Test fuzzy contact matching."""
    # Test with no matches
    result = fuzzy_match_contact("unknown_contact")
    assert result == "unknown_contact"


def test_log_send():
    """Test logging send operations."""
    # This should not raise an exception
    log_send("test_contact", "text", "Hello +1234567890 world")
    # Test with no phone number
    log_send("test_contact", "text", "Hello world")


def test_ocr_fallback_needed():
    """Test OCR fallback detection."""
    result = ocr_fallback_needed()
    assert isinstance(result, bool)


def test_get_contact_phone():
    """Test getting contact phone number."""
    result = get_contact_phone("unknown_contact")
    assert result is None


if __name__ == "__main__":
    pytest.main([__file__])