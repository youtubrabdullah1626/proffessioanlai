import os
from typing import Optional

from .logging_utils import setup_logging

logger = setup_logging()


def is_simulation_mode() -> bool:
	"""Return whether SIMULATION_MODE is enabled (default True)."""
	val = os.getenv("SIMULATION_MODE", "true").strip().lower()
	return val in {"1", "true", "t", "yes", "y"}


def is_confirmed() -> bool:
	"""Return whether destructive actions are confirmed via CONFIRM=yes."""
	val = os.getenv("CONFIRM", "no").strip().lower()
	return val in {"1", "true", "t", "yes", "y", "ok"}


def require_confirmation(action_description: str) -> bool:
	"""Check confirmation gate for destructive actions; log intent.
	Returns True if allowed to proceed.
	"""
	try:
		if is_simulation_mode():
			logger.info(f"[SIMULATION] Would perform: {action_description}")
			return False
		if not is_confirmed():
			logger.warning(
				f"Confirmation required for: {action_description}. Set CONFIRM=yes to proceed."
			)
			return False
		logger.info(f"Confirmed destructive action: {action_description}")
		return True
	except Exception:
		return False
