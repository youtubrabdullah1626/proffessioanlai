import json
import os
from typing import Dict, List

from .logging_utils import setup_logging
from .scanner import scan_app_paths

logger = setup_logging()


DEFAULT_DIRS = ["logs", "data", "memory", "config"]
MEMORY_JSON = os.path.join("memory", "memory.json")
MEMORY_DB = os.path.join("memory", "memory.db")
SYSTEM_APPS_JSON = os.path.join("data", "system_apps.json")
PATHS_JSON = os.path.join("config", "paths.json")


APP_CANDIDATES = {
	"whatsapp": [
		"%LOCALAPPDATA%/WhatsApp/WhatsApp.exe",
		"C:/Program Files/WhatsApp/WhatsApp.exe",
		"C:/Program Files (x86)/WhatsApp/WhatsApp.exe",
	],
	"chrome": [
		"C:/Program Files/Google/Chrome/Application/chrome.exe",
		"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
		"%LOCALAPPDATA%/Google/Chrome/Application/chrome.exe",
	],
	"edge": [
		"C:/Program Files/Microsoft/Edge/Application/msedge.exe",
		"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
	],
	"notepad": [
		"C:/Windows/System32/notepad.exe",
	],
}


def _expand_paths(paths: List[str]) -> List[str]:
	return [os.path.expandvars(p).replace("/", os.sep) for p in paths]


def ensure_first_launch() -> Dict[str, bool]:
	"""Create default dirs, memory files, scan apps, and write config/paths.json. Returns availability map."""
	for d in DEFAULT_DIRS:
		os.makedirs(d, exist_ok=True)
		logger.info(f"Ensured directory: {d}")

	if not os.path.exists(MEMORY_JSON):
		with open(MEMORY_JSON, "w", encoding="utf-8") as f:
			json.dump({"short_term": []}, f)
			logger.info("Initialized memory.json")
	if not os.path.exists(MEMORY_DB):
		with open(MEMORY_DB, "wb") as f:
			f.write(b"")
			logger.info("Initialized memory.db (placeholder)")

	availability: Dict[str, bool] = {}
	for key, cands in APP_CANDIDATES.items():
		found = any(os.path.isfile(p) for p in _expand_paths(cands))
		availability[key] = found

	with open(SYSTEM_APPS_JSON, "w", encoding="utf-8") as f:
		json.dump(availability, f, indent=2)
		logger.info(f"Wrote system apps map: {SYSTEM_APPS_JSON}")

	# Scanner-generated paths.json
	try:
		paths_map = scan_app_paths()
		with open(PATHS_JSON, "w", encoding="utf-8") as f:
			json.dump(paths_map, f, indent=2)
			logger.info(f"Wrote app paths map: {PATHS_JSON}")
	except Exception as e:
		logger.error(f"Failed to write {PATHS_JSON}: {e}")

	return availability
