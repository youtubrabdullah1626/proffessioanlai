import json
import os
from typing import Dict, List

from .logging_utils import setup_logging
from .scanner import scan_app_paths
from utils.scanner import scan_and_save_system_apps

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
    # Create default directories
    for d in DEFAULT_DIRS:
        os.makedirs(d, exist_ok=True)
        logger.info(f"Ensured directory: {d}")

    # Create memory files
    if not os.path.exists(MEMORY_JSON):
        with open(MEMORY_JSON, "w", encoding="utf-8") as f:
            json.dump({
                "version": "1.0",
                "created_at": "2025-10-31T00:00:00Z",
                "updated_at": "2025-10-31T00:00:00Z",
                "user_preferences": {},
                "conversation_history": [],
                "known_contacts": {},
                "app_shortcuts": {},
                "file_locations": {}
            }, f, indent=2)
            logger.info("Initialized memory.json")

    if not os.path.exists(MEMORY_DB):
        # Initialize SQLite database
        try:
            import sqlite3
            con = sqlite3.connect(MEMORY_DB)
            cur = con.cursor()
            cur.executescript(
                """
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    when_ts REAL,
                    data TEXT
                );
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    when_ts REAL,
                    kind TEXT,
                    payload TEXT
                );
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    when_ts REAL,
                    title TEXT,
                    status TEXT
                );
                CREATE TABLE IF NOT EXISTS habits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT,
                    value TEXT
                );
                CREATE TABLE IF NOT EXISTS apps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT,
                    path TEXT
                );
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT
                );
                """
            )
            con.commit()
            con.close()
            logger.info("Initialized memory.db")
        except Exception as e:
            logger.error(f"Failed to initialize memory.db: {e}")
            # Create empty file as fallback
            with open(MEMORY_DB, "wb") as f:
                f.write(b"")
                logger.info("Initialized memory.db (placeholder)")

    # Check app availability
    availability: Dict[str, bool] = {}
    for key, cands in APP_CANDIDATES.items():
        found = any(os.path.isfile(p) for p in _expand_paths(cands))
        availability[key] = found

    # Save system apps map
    with open(SYSTEM_APPS_JSON, "w", encoding="utf-8") as f:
        json.dump(availability, f, indent=2)
        logger.info(f"Wrote system apps map: {SYSTEM_APPS_JSON}")

    # Run enhanced scanner to generate paths.json
    try:
        logger.info("Running enhanced system app scanner...")
        if scan_and_save_system_apps(PATHS_JSON):
            logger.info(f"Successfully wrote app paths map: {PATHS_JSON}")
        else:
            logger.warning(f"Failed to write {PATHS_JSON}, using fallback scanner")
            # Fallback to original scanner
            paths_map = scan_app_paths()
            with open(PATHS_JSON, "w", encoding="utf-8") as f:
                json.dump(paths_map, f, indent=2)
                logger.info(f"Wrote app paths map (fallback): {PATHS_JSON}")
    except Exception as e:
        logger.error(f"Failed to run enhanced scanner: {e}")
        try:
            # Fallback to original scanner
            paths_map = scan_app_paths()
            with open(PATHS_JSON, "w", encoding="utf-8") as f:
                json.dump(paths_map, f, indent=2)
                logger.info(f"Wrote app paths map (fallback): {PATHS_JSON}")
        except Exception as e2:
            logger.error(f"Failed to write {PATHS_JSON}: {e2}")

    # Report summary
    logger.info("First launch setup complete.")
    logger.info("Available apps: " + ", ".join([k for k, v in availability.items() if v]))
    
    # If incomplete, log a message (in a real implementation, we would ask user)
    incomplete_apps = [k for k, v in availability.items() if not v]
    if incomplete_apps:
        logger.info(f"Missing apps (manual setup may be required): {', '.join(incomplete_apps)}")
        logger.info("Please install missing applications or update config/paths.json manually.")

    return availability


def is_first_run() -> bool:
    """Check if this is the first run of the application."""
    return not os.path.exists(MEMORY_JSON) or not os.path.exists(MEMORY_DB) or not os.path.exists(PATHS_JSON)


def run_onboarding_if_needed() -> bool:
    """Run onboarding process if needed."""
    if is_first_run():
        logger.info("First run detected. Starting onboarding process...")
        ensure_first_launch()
        return True
    else:
        logger.info("Not first run. Skipping onboarding.")
        return False