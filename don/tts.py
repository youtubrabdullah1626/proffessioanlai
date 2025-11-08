import pyttsx3
from typing import Optional

from .logging_utils import setup_logging
from .config import Settings, TTSSettings

logger = setup_logging()


def init_tts(settings: TTSSettings) -> Optional[pyttsx3.Engine]:
    """Initialize pyttsx3 engine with desired voice/rate. Returns engine or None."""
    try:
        engine = pyttsx3.init()
        if settings.rate:
            engine.setProperty("rate", settings.rate)
        # Optional: try to select voice by name if not default
        if settings.voice and settings.voice != "default":
            voices = engine.getProperty("voices")
            for v in voices:
                if settings.voice.lower() in (v.name or "").lower():
                    engine.setProperty("voice", v.id)
                    break
        logger.info("TTS engine initialized (pyttsx3)")
        return engine
    except Exception as e:
        logger.error(f"TTS init failed: {e}")
        return None


def speak_mixed(engine: Optional[pyttsx3.Engine], text: str) -> bool:
    """Speak mixed Roman Urdu + English text. Returns True if spoken or simulated."""
    try:
        if engine is None:
            logger.warning(f"[TTS] Engine not available. Would speak: {text}")
            return False
        logger.info(f"[TTS] Speaking: {text}")
        engine.say(text)
        engine.runAndWait()
        return True
    except Exception as e:
        logger.error(f"TTS speak failed: {e}")
        return False
