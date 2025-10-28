from typing import Tuple

from .logging_utils import setup_logging

logger = setup_logging()


def compose_message(raw: str, tone: str = "") -> Tuple[str, bool]:
	"""Compose message per rules:
	- If 'send exactly these words' present -> verbatim
	- If tone like 'friendly'/'formal' requested -> softly adapt
	Returns (message, needs_confirmation) where needs_confirmation is True only for rewrites.
	"""
	try:
		text = raw or ""
		lower = text.lower()
		if "send exactly these words" in lower or "bilkul yehi alfaaz" in lower:
			return text, False
		if not tone:
			# Detect common tone hints from text
			if "friendly" in lower or "dostana" in lower:
				tone = "friendly"
			elif "formal" in lower or "mulaeema" in lower:
				tone = "formal"
		if tone == "friendly":
			msg = f"(Friendly) {text} 🙂"
			return msg, True
		if tone == "formal":
			msg = f"(Formal) {text}"
			return msg, True
		return text, False
	except Exception as e:
		logger.error(f"compose_message failed: {e}")
		return raw, False
