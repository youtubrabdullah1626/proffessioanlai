from typing import Optional

try:
	import pyautogui  # type: ignore
	import pygetwindow as gw  # type: ignore
	has_gui = True
except Exception:
	has_gui = False

try:
	import pytesseract  # type: ignore
	has_ocr = True
except Exception:
	has_ocr = False

from .logging_utils import setup_logging
from .safety import is_simulation_mode

logger = setup_logging()


def focus_whatsapp_window() -> bool:
	if not has_gui:
		logger.warning("GUI automation not available.")
		return False
	wins = [w for w in gw.getAllTitles() if "whatsapp" in w.lower()]
	if not wins:
		return False
	w = gw.getWindowsWithTitle(wins[0])[0]
	if is_simulation_mode():
		logger.info(f"[SIMULATION] Would focus window: {w.title}")
		return True
	w.activate()
	return True


def ocr_region(region) -> str:
	if not has_ocr:
		return ""
	# Placeholder: would grab screenshot of region and do OCR
	return ""
