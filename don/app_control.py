import os
import subprocess
import time
from typing import Dict, List, Optional

import psutil

try:
	import win32gui  # type: ignore
	import win32con  # type: ignore
	has_win32 = True
except Exception:
	has_win32 = False

from .logging_utils import setup_logging
from .safety import is_simulation_mode, require_confirmation

logger = setup_logging()


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
}


def _expand_candidates(cands: List[str]) -> List[str]:
	return [os.path.expandvars(p).replace("/", os.sep) for p in cands]


def discover_app(app_key: str) -> Optional[str]:
	"""Return the first existing executable path for app_key from SYSTEM_APPS."""
	try:
		cands = _expand_candidates(SYSTEM_APPS.get(app_key.lower(), []))
		for p in cands:
			if os.path.isfile(p):
				return p
		return None
	except Exception:
		return None


def open_app(app_key_or_path: str, args: Optional[List[str]] = None) -> bool:
	"""Open an app by key in SYSTEM_APPS or by absolute path. Respects SIMULATION_MODE."""
	try:
		path = app_key_or_path
		if not os.path.isabs(path):
			found = discover_app(app_key_or_path)
			if not found:
				logger.warning(f"App not found: {app_key_or_path}")
				return False
			path = found
		cmd = [path] + (args or [])
		if is_simulation_mode():
			logger.info(f"[SIMULATION] Would open app: {' '.join(cmd)}")
			return True
		subprocess.Popen(cmd, shell=False)
		return True
	except Exception as e:
		logger.error(f"open_app failed: {e}")
		return False


def close_app_by_name(process_name: str) -> int:
	"""Close (terminate) processes matching name. Returns count terminated. Confirmation required."""
	if not require_confirmation(f"terminate processes named {process_name}"):
		return 0
	count = 0
	for p in psutil.process_iter(["name"]):
		try:
			if p.info.get("name", "").lower() == process_name.lower():
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
	"""Focus first top-level window with title containing keyword (case-insensitive)."""
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
	"""Maximize or minimize window whose title matches keyword."""
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


def kill_app_process(app_name: str, force: bool = False) -> bool:
	"""Kill an application process with confirmation.
	
	Args:
		app_name: Name of the application process to kill
		force: Whether to force kill (dangerous operation)
		
	Returns:
		bool: True if successful
	"""
	action = f"force kill process {app_name}" if force else f"terminate process {app_name}"
	if not require_confirmation(action):
		return False
		
	try:
		terminated = False
		for proc in psutil.process_iter(['pid', 'name']):
			if proc.info['name'].lower() == app_name.lower():
				if is_simulation_mode():
					logger.info(f"[SIMULATION] Would {'force kill' if force else 'terminate'} {app_name} (PID: {proc.info['pid']})")
					terminated = True
				else:
					if force:
						proc.kill()
					else:
						proc.terminate()
					terminated = True
		return terminated
	except Exception as e:
		logger.error(f"kill_app_process failed: {e}")
		return False