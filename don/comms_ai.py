from typing import Optional, Callable
import os
import time
import threading

import speech_recognition as sr

from .logging_utils import setup_logging
from .tts import init_tts, speak_mixed
from .config import Settings, load_settings

logger = setup_logging()


class STTEngine:
	"""Speech-to-text using SpeechRecognition: local first, Google fallback."""
	def __init__(self) -> None:
		self.recognizer = sr.Recognizer()

	def listen_once(self, timeout: float = 5.0, phrase_time_limit: float = 8.0) -> Optional[str]:
		try:
			with sr.Microphone() as source:
				self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
				audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
			try:
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


class GeminiClient:
	"""Placeholder Gemini client for intent parsing/reasoning. Real integration later."""
	def __init__(self, api_key: Optional[str]) -> None:
		self.api_key = api_key

	def analyze_intent(self, text: str) -> str:
		try:
			logger.info("Gemini intent analysis (stub)")
			return text
		except Exception:
			return text


class CommsAI:
	def __init__(self, settings: Optional[Settings] = None) -> None:
		self.settings = settings or load_settings()
		self.tts = init_tts(self.settings.tts)
		self.stt = STTEngine()
		self._stop_flag = False
		self._thread: Optional[threading.Thread] = None

	def listen_and_respond(self) -> None:
		try:
			text = self.stt.listen_once()
			if not text:
				speak_mixed(self.tts, "Kuch sunai nahi diya. Dobara bolo please.")
				return
			logger.info(f"Heard: {text}")
			from .executor import execute_command  # local import to avoid circular
			out = execute_command(text)
			if out.get("ok"):
				speak_mixed(self.tts, "Done ho gaya.")
			else:
				speak_mixed(self.tts, "Kuch masla aaya. Try karo phr se.")
		except Exception as e:
			logger.error(f"listen_and_respond failed: {e}")

	def start_background_listening(self, loop_delay: float = 0.5) -> None:
		"""Start a non-blocking loop that listens continuously and processes commands."""
		if self._thread and self._thread.is_alive():
			return
		self._stop_flag = False
		self._thread = threading.Thread(target=self._loop, args=(loop_delay,), daemon=True)
		self._thread.start()
		logger.info("Background voice listener started.")

	def _loop(self, loop_delay: float) -> None:
		while not self._stop_flag:
			try:
				text = self.stt.listen_once(timeout=3.0, phrase_time_limit=7.0)
				if text:
					logger.info(f"User said: {text}")
					from .executor import execute_command  # local import to avoid circular
					out = execute_command(text)
					logger.info(f"Exec result: {out}")
					if out.get("ok"):
						speak_mixed(self.tts, "Done ho gaya.")
					else:
						speak_mixed(self.tts, "Kuch masla aaya. Try karo phr se.")
			except Exception as e:
				logger.warning(f"Background listen error: {e}")
			time.sleep(loop_delay)

	def stop_background_listening(self) -> None:
		self._stop_flag = True
		logger.info("Background voice listener stopped.")
