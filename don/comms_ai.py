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
	# Replace Urdu/Arabic punctuation and latin punctuation
	text = re.sub(r"[^\w\s']", " ", text)
	text = re.sub(r"\s+", " ", text).strip()
	return text


def _recognize(recognizer: sr.Recognizer, audio) -> Tuple[Optional[str], Optional[str]]:
	"""
	Try urdu then english. Returns (text, language) or (None, None)
	"""
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
	# local import to avoid circular imports
	try:
		from don.executor import execute_command
	except Exception:
		from executor import execute_command  # fallback import path
	try:
		# Log parsed intent if available
		try:
			from core.intent_engine import parse_intent
			intent = parse_intent(normalized)
			logging.info("Parsed intent: %s", intent)
		except Exception:
			pass
		# Execute using normalized text to match executor signature
		return execute_command(normalized)
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

	def _listen_loop(self) -> None:
		r = sr.Recognizer()
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
						speak_mixed(self.tts, "Done ho gaya.")
					else:
						speak_mixed(self.tts, "Kuch masla aaya. Try karo phr se.")
				else:
					logging.info("Could not recognize audio (unknown). Continuing.")
				time.sleep(0.1)

	def start_background_listening(self) -> None:
		if self.running:
			return
		self.running = True
		self._thread = threading.Thread(target=self._listen_loop, daemon=True)
		self._thread.start()
		logging.info("Background voice listener started.")

	def stop_background_listening(self) -> None:
		self.running = False
		if self._thread:
			self._thread.join(timeout=2)
			logging.info("Background voice listener stopped.")
