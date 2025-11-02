from typing import Optional
import threading

import pyttsx3

from don.tts import init_tts, speak_mixed
from don.config import load_settings
from don.logging_utils import setup_logging

logger = setup_logging()

_engine: Optional[pyttsx3.Engine] = None
_speaking_thread: Optional[threading.Thread] = None
_speaking_lock = threading.Lock()


def _get_engine():
    """Get or initialize the TTS engine."""
    global _engine
    if _engine is None:
        settings = load_settings()
        _engine = init_tts(settings.tts)
    return _engine


def speak(text: str, voice: Optional[str] = None, wait: bool = False) -> bool:
    """
    Speak text using TTS engine.
    
    Args:
        text: Text to speak
        voice: Voice to use (optional)
        wait: Whether to wait for speech to complete
        
    Returns:
        bool: True if speech was successful
    """
    global _speaking_thread
    
    try:
        engine = _get_engine()
        if engine is None:
            logger.warning("TTS engine not available")
            return False

        # Set voice if specified
        if voice:
            voices = engine.getProperty("voices")
            for v in voices:
                if voice.lower() in (v.name or "").lower():
                    engine.setProperty("voice", v.id)
                    break

        if wait:
            return speak_mixed(engine, text)
        else:
            # Non-blocking speech
            with _speaking_lock:
                if _speaking_thread and _speaking_thread.is_alive():
                    logger.warning("Already speaking, skipping new speech request")
                    return False
                    
            def _speak_async():
                try:
                    speak_mixed(engine, text)
                except Exception as e:
                    logger.error(f"Async speech failed: {e}")
                    
            _speaking_thread = threading.Thread(target=_speak_async, daemon=True)
            _speaking_thread.start()
            return True
            
    except Exception as e:
        logger.error(f"speak failed: {e}")
        return False


def is_speaking() -> bool:
    """Check if currently speaking."""
    with _speaking_lock:
        return _speaking_thread is not None and _speaking_thread.is_alive()