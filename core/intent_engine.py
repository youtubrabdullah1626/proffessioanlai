from don.intent_parser import parse_intent


def preprocess_for_intent(text: str) -> str:
	"""Normalize text (Urdu/English mix) before intent parsing.
	Relies on don.comms_ai._normalize_text when available to keep
	normalization logic in one place and avoid duplication.
	"""
	try:
		from don.comms_ai import _normalize_text  # local to avoid circulars
		return _normalize_text(text)
	except Exception:
		# Fallback minimal normalization
		import re
		clean = (text or "").lower().strip()
		clean = re.sub(r"[^\w\s']", " ", clean)
		clean = re.sub(r"\s+", " ", clean).strip()
		return clean


def parse(text: str):
	"""Parse intent after preprocessing the input text."""
	return parse_intent(preprocess_for_intent(text))
