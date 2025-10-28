from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from .config import Settings
from .logging_utils import setup_logging
from .safety import is_simulation_mode

logger = setup_logging()


def build_chrome(settings: Settings) -> Optional[webdriver.Chrome]:
	"""Build a Chrome WebDriver using the provided user profile. Returns driver or None.
	Respects SIMULATION_MODE.
	"""
	try:
		if is_simulation_mode():
			logger.info(
				f"[SIMULATION] Would start Chrome with profile: {settings.chrome_profile_path}"
			)
			return None
		opts = Options()
		opts.add_argument(f"--user-data-dir={settings.chrome_profile_path}")
		drv = webdriver.Chrome(options=opts)
		logger.info("Chrome WebDriver started for WhatsApp Web")
		return drv
	except Exception as e:
		logger.error(f"Failed to start Chrome WebDriver: {e}")
		return None
