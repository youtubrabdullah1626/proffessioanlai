import os
import subprocess
import urllib.parse
from typing import Optional

from .config import Settings
from .logging_utils import setup_logging
from .safety import is_simulation_mode, require_confirmation

logger = setup_logging()


def _chrome_exe_candidates() -> list:
	return [
		"C:/Program Files/Google/Chrome/Application/chrome.exe",
		"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
		os.path.expandvars("%LOCALAPPDATA%/Google/Chrome/Application/chrome.exe"),
	]


def _edge_exe_candidates() -> list:
	return [
		"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
		"C:/Program Files/Microsoft/Edge/Application/msedge.exe",
	]


def _find_executable(candidates: list) -> Optional[str]:
	for p in candidates:
		if os.path.isfile(p):
			return p
	return None


def _build_browser_cmd(exe: str, profile_path: str, url: str) -> list:
	args = [exe]
	if profile_path:
		args.append(f"--user-data-dir={profile_path}")
	args.append(url)
	return args


def open_url(settings: Settings, url: str, prefer_edge: bool = False) -> bool:
	"""Open a URL in Chrome (default) or Edge using user profile. Respects SIMULATION_MODE."""
	try:
		exe = _find_executable(_edge_exe_candidates() if prefer_edge else _chrome_exe_candidates())
		if not exe:
			logger.warning("No browser executable found.")
			return False
		cmd = _build_browser_cmd(exe, settings.chrome_profile_path, url)
		if is_simulation_mode():
			logger.info(f"[SIMULATION] Would open URL: {url} via {exe}")
			return True
		logger.info(f"Opening URL: {url}")
		subprocess.Popen(cmd, shell=False)
		return True
	except Exception as e:
		logger.error(f"open_url failed: {e}")
		return False


def google_search(settings: Settings, query: str, prefer_edge: bool = False) -> bool:
	try:
		qs = urllib.parse.quote_plus(query)
		url = f"https://www.google.com/search?q={qs}"
		return open_url(settings, url, prefer_edge)
	except Exception as e:
		logger.error(f"google_search failed: {e}")
		return False


def youtube_search(settings: Settings, query: str, prefer_edge: bool = False) -> bool:
	try:
		qs = urllib.parse.quote_plus(query)
		url = f"https://www.youtube.com/results?search_query={qs}"
		return open_url(settings, url, prefer_edge)
	except Exception as e:
		logger.error(f"youtube_search failed: {e}")
		return False


def download_file(url: str, target_path: str) -> bool:
	"""Placeholder safe downloader: requires confirmation; logs intent.
	This will be replaced with robust download in later parts.
	"""
	try:
		action = f"download {url} -> {target_path}"
		if not require_confirmation(action):
			return False
		# Real download intentionally omitted for safety in Part 2 scaffold.
		logger.info(f"[LIVE] (placeholder) Download allowed: {url} -> {target_path}")
		return True
	except Exception as e:
		logger.error(f"download_file failed: {e}")
		return False
