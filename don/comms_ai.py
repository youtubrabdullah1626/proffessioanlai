from typing import Optional, Tuple
import os
import time
import threading
import re
import logging
import speech_recognition as sr

from .logging_utils import setup_logging
from .tts import init_tts, speak_mixed
from .config import Settings, load_settings

logger = setup_logging()

MAP_URDU = {
    "اوپن": "open",
    "واٹس ایپ": "whatsapp",
    "واتساپ": "whatsapp",
    "واٹساپ": "whatsapp",
    "واٹس": "whatsapp",
    "کھولو": "open",
    "کھول": "open",
    "بند": "close",
}


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    for k, v in MAP_URDU.items():
        text = text.replace(k, v)
    text = re.sub(r"[^\w\s']", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _maybe_gemini_reply(text: str) -> Optional[str]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
        prompt = f"User said: {text}. Reply in friendly Roman Urdu + English mix, concise."
        resp = model.generate_content(prompt, request_options={"timeout": 10})
        if hasattr(resp, "text") and resp.text:
            return resp.text
        cand = getattr(resp, "candidates", None)
        if cand and getattr(cand[0], "content", None):
            parts = getattr(cand[0].content, "parts", [])
            if parts and hasattr(parts[0], "text"):
                return parts[0].text
        return None
    except Exception as e:
        logger.warning(f"Gemini reply failed: {e}")
        return None


def _recognize(recognizer: sr.Recognizer, audio) -> Tuple[Optional[str], Optional[str]]:
    try:
        text = recognizer.recognize_google(audio, language="ur-PK")
        return text, "ur-PK"
    except sr.UnknownValueError:
        try:
            text = recognizer.recognize_google(audio, language="en-US")
            return text, "en-US"
        except sr.UnknownValueError:
            return None, None
    except sr.RequestError as e:
        logging.exception("STT RequestError: %s", e)
        return None, None


def _dispatch(text_raw: str):
    if not text_raw:
        return {"ok": False, "reason": "empty"}
    normalized = _normalize_text(text_raw)
    logging.info("User said (raw): %s", text_raw)
    logging.info("User said (normalized): %s", normalized)
    try:
        from don.executor import execute_command
    except Exception:
        from executor import execute_command
    try:
        try:
            from core.intent_engine import parse_intent
            intent = parse_intent(normalized)
            logging.info("Parsed intent: %s", intent)
            exec_res = execute_command(normalized)
            if exec_res.get("ok"):
                return exec_res
        except Exception:
            pass
        reply = _maybe_gemini_reply(text_raw)
        if reply:
            return {"ok": True, "handler": "gemini", "reply": reply}
        return {"ok": False, "handler": "unknown"}
    except Exception as e:
        logging.exception("Dispatch failed: %s", e)
        return {"ok": False, "error": str(e)}


class CommsAI:
    def __init__(self, settings: Optional[Settings] = None, listen_timeout: int = 3, phrase_time_limit: int = 6, language_preference=None) -> None:
        self.settings = settings or load_settings()
        self.tts = init_tts(self.settings.tts)
        self.running = False
        self.listen_timeout = listen_timeout
        self.phrase_time_limit = phrase_time_limit
        self.language_preference = language_preference or ["ur-PK", "en-US"]
        self._thread: Optional[threading.Thread] = None
        self._loop_delay: float = 0.5

    def _listen_loop(self) -> None:
        r = sr.Recognizer()
        r.dynamic_energy_threshold = True
        r.energy_threshold = int(os.getenv("STT_ENERGY_THRESHOLD", "250"))

        # ✅ Safe mic initialization
        if not sr.Microphone.list_microphone_names():
            logger.error("🎤 No microphone devices detected.")
            speak_mixed(self.tts, "Mic detect nahi hua. Check karo mic settings.")
            return

        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=1)
            while self.running:
                try:
                    logging.info("Listening... (timeout=%s, phrase_time_limit=%s)", self.listen_timeout, self.phrase_time_limit)
                    audio = r.listen(source, timeout=self.listen_timeout, phrase_time_limit=self.phrase_time_limit)
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    logging.exception("Microphone read error: %s", e)
                    time.sleep(0.5)
                    continue

                text, lang = _recognize(r, audio)
                if text:
                    logging.info("Recognized (%s): %s", lang, text)
                    result = _dispatch(text)
                    logging.info("Exec result: %s", result)
                    if result.get("ok"):
                        if result.get("handler") == "gemini" and result.get("reply"):
                            speak_mixed(self.tts, result.get("reply") or "")
                        else:
                            speak_mixed(self.tts, "Done ho gaya.")
                    else:
                        speak_mixed(self.tts, "Kuch masla aaya. Try karo phr se.")
                else:
                    logging.info("Could not recognize audio (unknown). Continuing.")
                time.sleep(self._loop_delay)

    def start_background_listening(self, loop_delay: float = 0.5) -> None:
        if self.running:
            return
        self._loop_delay = loop_delay
        self.running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logging.info("Background voice listener started.")

    def stop_background_listening(self) -> None:
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
            logging.info("Background voice listener stopped.")
