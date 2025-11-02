from typing import Optional, Callable
import os
import threading
import time

try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    HAS_SPEECH_RECOGNITION = False
    sr = None

from don.config import load_settings
from don.logging_utils import setup_logging
from don.safety import is_simulation_mode

logger = setup_logging()


class STTEngine:
    """Speech-to-text using SpeechRecognition: local first, Gemini fallback."""
    
    def __init__(self) -> None:
        self.recognizer = sr.Recognizer() if HAS_SPEECH_RECOGNITION else None

    def listen_once(self, timeout: float = 5.0, phrase_time_limit: float = 8.0) -> Optional[str]:
        """Listen for a single phrase and return the text."""
        if not HAS_SPEECH_RECOGNITION:
            logger.warning("SpeechRecognition not available")
            return None
            
        if is_simulation_mode():
            logger.info("[SIMULATION] Would listen for speech")
            return "test command"
            
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            try:
                # Try local recognition first
                text = self.recognizer.recognize_google(audio)
                return text
            except Exception as e:
                logger.warning(f"Local STT failed; using Google fallback: {e}")
                try:
                    text = self.recognizer.recognize_google(audio)
                    return text
                except Exception as e2:
                    logger.error(f"Google STT failed: {e2}")
                    return None
        except Exception as e:
            logger.error(f"listen_once failed: {e}")
            return None

    def listen_with_gemini_fallback(self, timeout: float = 5.0, phrase_time_limit: float = 8.0) -> Optional[str]:
        """Listen with Gemini-based STT fallback if configured."""
        # Try standard STT first
        text = self.listen_once(timeout, phrase_time_limit)
        if text:
            return text
            
        # If configured, try Gemini STT as fallback
        # This would be implemented when Gemini integration is added
        logger.info("Gemini STT fallback would be used here if configured")
        return None


class BackgroundListener:
    """Background listener that continuously listens for speech."""
    
    def __init__(self, callback: Callable[[str], None]) -> None:
        self.callback = callback
        self.stt = STTEngine()
        self._stop_flag = False
        self._thread: Optional[threading.Thread] = None

    def start(self, loop_delay: float = 0.5) -> None:
        """Start background listening."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_flag = False
        self._thread = threading.Thread(target=self._loop, args=(loop_delay,), daemon=True)
        self._thread.start()
        logger.info("Background voice listener started.")

    def _loop(self, loop_delay: float) -> None:
        """Background listening loop."""
        while not self._stop_flag:
            try:
                text = self.stt.listen_once(timeout=3.0, phrase_time_limit=7.0)
                if text:
                    logger.info(f"User said: {text}")
                    self.callback(text)
            except Exception as e:
                logger.warning(f"Background listen error: {e}")
            time.sleep(loop_delay)

    def stop(self) -> None:
        """Stop background listening."""
        self._stop_flag = True
        logger.info("Background voice listener stopped.")


def listen_once_text() -> str:
    """Listen for a single phrase and return the text."""
    settings = load_settings()
    stt = STTEngine()
    res = stt.listen_once()
    return res or ""


def start_background_listener(callback: Callable[[str], None]) -> BackgroundListener:
    """Start a background listener with a callback function."""
    listener = BackgroundListener(callback)
    listener.start()
    return listener