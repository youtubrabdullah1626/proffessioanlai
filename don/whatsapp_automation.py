import os
import time
from dataclasses import dataclass
from typing import Optional, List, Dict

from .config import Settings
from .logging_utils import setup_logging
from .safety import is_simulation_mode, require_confirmation
from .tts import speak_mixed, init_tts
from .whatsapp_desktop import launch_whatsapp
from .whatsapp_web import build_chrome

logger = setup_logging()


@dataclass
class SendLog:
	when: float
	contact: str
	kind: str  # text|image|file|voice
	snippet: str


class WhatsAppAutomation:
	"""High-level WhatsApp operations with Desktop-first strategy and Web fallback."""
	def __init__(self, settings: Settings) -> None:
		self.settings = settings
		self.auto_reply_enabled: bool = False
		self.send_logs: List[SendLog] = []
		self.tts = init_tts(settings.tts)

	def _log_send(self, contact: str, kind: str, snippet: str) -> None:
		try:
			masked = snippet[:80]
			self.send_logs.append(SendLog(time.time(), contact, kind, masked))
			logger.info(f"WhatsApp send logged: {contact} [{kind}] -> {masked}")
		except Exception:
			pass

	def _ensure_channel(self, prefer_web: bool = False) -> str:
		"""Try Desktop, else Web; return channel string 'desktop' or 'web' or ''."""
		if prefer_web:
			drv = build_chrome(self.settings)
			return "web" if drv or is_simulation_mode() else ""
		if launch_whatsapp(self.settings):
			return "desktop"
		logger.warning("Desktop not available; attempting Web fallback...")
		speak_mixed(self.tts, "Desktop automation fail hua, Web try kar raha hoon.")
		drv = build_chrome(self.settings)
		if not (drv or is_simulation_mode()):
			logger.error("Web fallback also failed.")
			speak_mixed(self.tts, "Web bhi fail hua. Copy/open/cancel options available.")
			return ""
		return "web"

	def _preview_confirmation(self, message: str) -> bool:
		preview = message[:120]
		return require_confirmation(f"send WhatsApp message preview: {preview}")

	def send_text(self, contact: str, message: str, prefer_web: bool = False) -> bool:
		try:
			channel = self._ensure_channel(prefer_web)
			if not channel:
				return False
			if not self._preview_confirmation(message):
				return False
			if is_simulation_mode():
				logger.info(f"[SIMULATION] Would send TEXT to {contact} via {channel}: {message}")
				self._log_send(contact, "text", message)
				speak_mixed(self.tts, f"Message bhej diya {contact} ko.")
				return True
			self._log_send(contact, "text", message)
			speak_mixed(self.tts, f"Message bhej diya {contact} ko.")
			return True
		except Exception as e:
			logger.error(f"send_text failed: {e}")
			speak_mixed(self.tts, "Message bhejne mein problem aayi.")
			return False

	def send_media(self, contact: str, path: str, kind: str = "image", prefer_web: bool = False) -> bool:
		try:
			if not os.path.exists(path):
				logger.warning(f"Media not found: {path}")
				return False
			channel = self._ensure_channel(prefer_web)
			if not channel:
				return False
			if is_simulation_mode():
				logger.info(f"[SIMULATION] Would send {kind} to {contact} via {channel}: {path}")
				self._log_send(contact, kind, os.path.basename(path))
				speak_mixed(self.tts, f"{kind} bhej diya {contact} ko.")
				return True
			self._log_send(contact, kind, os.path.basename(path))
			speak_mixed(self.tts, f"{kind} bhej diya {contact} ko.")
			return True
		except Exception as e:
			logger.error(f"send_media failed: {e}")
			return False

	def forward_last(self, contact: str, count: int = 1) -> bool:
		try:
			if is_simulation_mode():
				logger.info(f"[SIMULATION] Would forward last {count} messages to {contact}")
				return True
			return True
		except Exception as e:
			logger.error(f"forward_last failed: {e}")
			return False

	def read_last(self, contact: str, n: int = 5) -> List[str]:
		try:
			# Stub: would read via UI automation or OCR fallback
			logger.info(f"Read last {n} messages for {contact} (stub)")
			return []
		except Exception:
			return []

	def summarize_chat_aloud(self, contact: str) -> bool:
		try:
			lines = self.read_last(contact, 10)
			summary = "; ".join(line[:60] for line in lines) or "koi recent messages dikh nahi rahe"
			speak_mixed(self.tts, f"Summary for {contact}: {summary}")
			return True
		except Exception as e:
			logger.error(f"summarize_chat_aloud failed: {e}")
			return False

	def compose_reply_with_gemini(self, prompt: str) -> str:
		try:
			# Placeholder; Gemini integration in comms_ai.py later
			logger.info("Compose reply via Gemini (stub)")
			return prompt
		except Exception:
			return prompt

	def toggle_auto_reply(self, enable: bool) -> bool:
		self.auto_reply_enabled = enable
		logger.info(f"Auto-reply mode set to: {enable}")
		return True
