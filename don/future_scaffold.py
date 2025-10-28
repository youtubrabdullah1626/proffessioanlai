import threading
import time
from typing import Optional

from .logging_utils import setup_logging

logger = setup_logging()


def detect_emotion(text: str) -> str:
	"""Stub emotion detection; returns neutral/friendly/assertive etc."""
	try:
		lower = (text or "").lower()
		if any(k in lower for k in ["sorry", "please"]):
			return "polite"
		return "neutral"
	except Exception:
		return "neutral"


class BackgroundConversation:
	"""Stub background conversation loop; can be wired to hotword/STT later."""
	def __init__(self) -> None:
		self.stop_flag = False
		self.thread: Optional[threading.Thread] = None

	def start(self) -> None:
		if self.thread and self.thread.is_alive():
			return
		self.stop_flag = False
		self.thread = threading.Thread(target=self._run, daemon=True)
		self.thread.start()
		logger.info("Background conversation started.")

	def _run(self) -> None:
		while not self.stop_flag:
			time.sleep(1.0)

	def stop(self) -> None:
		self.stop_flag = True
		logger.info("Background conversation stopped.")


def personalize_preferences(fav_contact: Optional[str] = None, fav_app: Optional[str] = None) -> bool:
	try:
		logger.info(f"Personalization updated: contact={fav_contact}, app={fav_app}")
		return True
	except Exception:
		return False


def integrations_stub() -> bool:
	logger.info("Integrations (email/calendar/Telegram) scaffold ready.")
	return True


def gui_dashboard_stub() -> bool:
	logger.info("GUI dashboard scaffold ready.")
	return True
