import os
import subprocess
import time
from typing import Dict, List, Optional

import psutil
import json

try:
    import win32gui
    import win32con
    import win32com.client
    has_win32 = True
except Exception:
    has_win32 = False

from .logging_utils import setup_logging
from .safety import is_simulation_mode, require_confirmation

logger = setup_logging()

# Expanded list of system apps
SYSTEM_APPS: Dict[str, List[str]] = {
    "whatsapp": [
        "%LOCALAPPDATA%/WhatsApp/WhatsApp.exe",
        "C:/Program Files/WhatsApp/WhatsApp.exe",
        "C:/Program Files (x86)/WhatsApp/WhatsApp.exe",
    ],
    "chrome": [
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    ],
    "edge": [
        "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
        "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
    ],
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "cmd": ["cmd.exe"],
    "explorer": ["explorer.exe"],
    "settings": ["ms-settings:"],
    "control panel": ["control"],
    "paint": ["mspaint.exe"],
    "wordpad": ["write.exe"],
    "vlc": [
        "C:/Program Files/VideoLAN/VLC/vlc.exe",
        "C:/Program Files (x86)/VideoLAN/VLC/vlc.exe",
    ],
    "spotify": [
        "%APPDATA%/Spotify/Spotify.exe",
        "%LOCALAPPDATA%/Microsoft/WindowsApps/Spotify.exe",
    ],
    "discord": [
        "%LOCALAPPDATA%/Discord/Update.exe",
        "%LOCALAPPDATA%/Discord/Discord.exe",
    ],
    "telegram": [
        "%LOCALAPPDATA%/Telegram Desktop/Telegram.exe",
        "C:/Program Files/Telegram Desktop/Telegram.exe",
    ],
}


def _expand_candidates(cands: List[str]) -> List[str]:
    return [os.path.expandvars(p).replace("/", os.sep) for p in cands]


def _read_paths_json() -> Dict[str, str]:
    try:
        with open(os.path.join("config", "paths.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
            return {str(k).lower(): str(v) for k, v in data.items()}
    except Exception:
        return {}


def discover_app(app_key: str) -> Optional[str]:
    """Return the path or shell target for app_key from paths.json or SYSTEM_APPS."""
    key = app_key.lower().strip()
    paths_map = _read_paths_json()

    # 1. Custom user config
    if key in paths_map:
        return paths_map[key]

    # 2. Predefined paths
    for p in _expand_candidates(SYSTEM_APPS.get(key, [])):
        if os.path.isfile(p) or p.endswith(":"):
            return p

    # 3. Try Windows shell (ms-settings:, shell:Appsfolder, etc.)
    shell_targets = {
        "mail": "ms-mail:",
        "calendar": "ms-calendar:",
        "camera": "microsoft.windows.camera:",
        "store": "ms-windows-store:",
        "photos": "ms-photos:",
    }
    if key in shell_targets:
        return shell_targets[key]

    return None


def open_app(app_key_or_path: str, args: Optional[List[str]] = None) -> bool:
    """Open an app by key or absolute path."""
    try:
        path = app_key_or_path.strip()
        if not os.path.isabs(path) and os.sep not in path and ":" not in path:
            found = discover_app(path)
            if not found:
                logger.warning(f"App not found: {path}")
                return False
            path = found

        # Microsoft Store or URI apps
        if path.endswith(":"):
            if is_simulation_mode():
                logger.info(f"[SIMULATION] Would open app: {path}")
                return True
            logger.info(f"Launching URI app: {path}")
            subprocess.run(["start", path], shell=True)
            return True

        # Normal .exe apps
        cmd = [path] + (args or [])
        if is_simulation_mode():
            logger.info(f"[SIMULATION] Would open app: {' '.join(cmd)}")
            return True

        logger.info(f"Opening app: {' '.join(cmd)}")
        subprocess.Popen(cmd, shell=False)
        return True

    except Exception as e:
        logger.error(f"open_app failed: {e}")
        return False


def close_app_by_name(process_name: str) -> int:
    """Close (terminate) processes matching name."""
    if not require_confirmation(f"terminate processes named {process_name}"):
        return 0

    count = 0
    for p in psutil.process_iter(["name"]):
        try:
            if p.info.get("name", "").lower() == process_name.lower() or process_name.lower() in p.info.get("name", "").lower():
                if is_simulation_mode():
                    logger.info(f"[SIMULATION] Would terminate PID {p.pid} ({process_name})")
                    count += 1
                else:
                    p.terminate()
                    count += 1
        except Exception:
            continue
    return count


def focus_window_by_title(keyword: str) -> bool:
    """Focus window by title."""
    if not has_win32:
        logger.warning("win32 APIs not available; cannot focus window.")
        return False

    matches: List[int] = []

    def enum_handler(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if title and keyword.lower() in title.lower() and win32gui.IsWindowVisible(hwnd):
            matches.append(hwnd)

    try:
        win32gui.EnumWindows(enum_handler, None)
        if not matches:
            return False
        hwnd = matches[0]
        if is_simulation_mode():
            logger.info(f"[SIMULATION] Would focus window: {win32gui.GetWindowText(hwnd)}")
            return True
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        return True
    except Exception as e:
        logger.error(f"focus_window_by_title failed: {e}")
        return False


def set_window_state(keyword: str, action: str) -> bool:
    """Maximize or minimize a window."""
    if not has_win32:
        logger.warning("win32 APIs not available; cannot manage window state.")
        return False

    code = win32con.SW_MAXIMIZE if action == "maximize" else win32con.SW_MINIMIZE
    matches: List[int] = []

    def enum_handler(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if title and keyword.lower() in title.lower() and win32gui.IsWindowVisible(hwnd):
            matches.append(hwnd)

    try:
        win32gui.EnumWindows(enum_handler, None)
        if not matches:
            return False
        hwnd = matches[0]
        if is_simulation_mode():
            logger.info(f"[SIMULATION] Would {action} window: {win32gui.GetWindowText(hwnd)}")
            return True
        win32gui.ShowWindow(hwnd, code)
        return True
    except Exception as e:
        logger.error(f"set_window_state failed: {e}")
        return False


def scan_missing_apps(required: Dict[str, List[str]]) -> Dict[str, bool]:
    """Return availability map for app keys (True if found)."""
    out: Dict[str, bool] = {}
    for key, cands in required.items():
        found = any(os.path.isfile(os.path.expandvars(p).replace("/", os.sep)) for p in cands)
        out[key] = found
    return out
