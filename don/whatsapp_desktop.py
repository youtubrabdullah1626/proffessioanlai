import os
import subprocess
import time
from typing import List, Optional

from .config import Settings
from .logging_utils import setup_logging
from .safety import is_simulation_mode

logger = setup_logging()


def discover_whatsapp_exe(paths: List[str]) -> Optional[str]:
	"""Find the first existing WhatsApp.exe from candidate paths."""
	try:
		for p in paths:
			if os.path.isfile(p):
				return p
		return None
	except Exception:
		return None


def launch_whatsapp(settings: Settings) -> bool:
	"""Launch WhatsApp Desktop using discovered EXE. Returns True if launched.
	Respects SIMULATION_MODE.
	"""
	try:
		exe = discover_whatsapp_exe(settings.whatsapp_desktop_paths)
		if not exe:
			logger.warning("WhatsApp Desktop not found in candidate paths.")
			return False
		if is_simulation_mode():
			logger.info(f"[SIMULATION] Would launch WhatsApp Desktop: {exe}")
			return True
		logger.info(f"Launching WhatsApp Desktop: {exe}")
		subprocess.Popen([exe], shell=False)
		time.sleep(2)
		return True
	except Exception as e:
		logger.error(f"Failed to launch WhatsApp Desktop: {e}")
		return False
