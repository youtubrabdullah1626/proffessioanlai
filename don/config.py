import json
import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TTSSettings:
	engine: str = "pyttsx3"
	voice: str = "default"
	rate: int = 180


@dataclass
class Settings:
	whatsapp_desktop_paths: List[str]
	chrome_profile_path: str
	similarity_threshold: float
	language: str
	wake_words: List[str]
	tts: TTSSettings


def _expand_env_paths(paths: List[str]) -> List[str]:
	"""Expand environment variables and normalize Windows paths.
	Returns a list of absolute candidate paths.
	"""
	expanded: List[str] = []
	for p in paths:
		try:
			expanded_path = os.path.expandvars(p)
			expanded_path = expanded_path.replace("/", os.sep)
			expanded.append(expanded_path)
		except Exception:
			# Best-effort expansion; ignore invalid entries
			continue
	return expanded


def _read_json_if_exists(path: str) -> dict:
	try:
		if os.path.exists(path):
			with open(path, "r", encoding="utf-8") as f:
				return json.load(f)
	except Exception:
		pass
	return {}


def load_settings(settings_path: str = "settings.json") -> Settings:
	"""Load JSON settings from file with sane defaults if missing.
	Also respects environment overrides.
	"""
	default = {
		"whatsappDesktopPaths": [
			"%LOCALAPPDATA%/WhatsApp/WhatsApp.exe",
			"C:/Program Files/WhatsApp/WhatsApp.exe",
			"C:/Program Files (x86)/WhatsApp/WhatsApp.exe",
		],
		"chromeProfilePath": "C:/Users/New Select Com/AppData/Local/Google/Chrome/User Data/Default",
		"similarityThreshold": 0.82,
		"language": "roman-urdu-english",
		"wakeWords": ["hey don", "don"],
		"tts": {
			"engine": "pyttsx3",
			"voice": "default",
			"rate": 180,
		},
	}

	data = default.copy()
	# Load from root settings.json and config/settings.json (later overrides earlier)
	root_settings = _read_json_if_exists(settings_path)
	cfg_settings = _read_json_if_exists(os.path.join("config", "settings.json"))
	for src in (root_settings, cfg_settings):
		if src:
			data.update(src)

	# Compatibility with sample alternate keys
	if "wake_word" in data and not data.get("wakeWords"):
		data["wakeWords"] = data.get("wake_word", [])
	if "tts_provider" in data:
		data.setdefault("tts", {})["engine"] = data.get("tts_provider")
	if "simulate" in data and os.getenv("SIMULATION_MODE") is None:
		os.environ["SIMULATION_MODE"] = str(bool(data.get("simulate"))).lower()

	paths = _expand_env_paths(data.get("whatsappDesktopPaths", []))
	chrome_profile = os.path.expandvars(data.get("chromeProfilePath", ""))
	chrome_profile = chrome_profile.replace("/", os.sep)
	threshold = float(os.getenv("SIMILARITY_THRESHOLD", data.get("similarityThreshold", 0.82)))
	language = data.get("language", "roman-urdu-english")
	wake_words = data.get("wakeWords", ["hey don", "don"]) or ["hey don", "don"]
	tts_data = data.get("tts", {})
	tts = TTSSettings(
		engine=str(tts_data.get("engine", "pyttsx3")),
		voice=str(tts_data.get("voice", "default")),
		rate=int(tts_data.get("rate", 180)),
	)

	return Settings(
		whatsapp_desktop_paths=paths,
		chrome_profile_path=chrome_profile,
		similarity_threshold=threshold,
		language=language,
		wake_words=wake_words,
		tts=tts,
	)


def get_env_flag(name: str, default: bool) -> bool:
	"""Return a boolean env flag supporting common truthy values."""
	val = os.getenv(name)
	if val is None:
		return default
	return str(val).strip().lower() in {"1", "true", "t", "yes", "y"}


def get_env_text(name: str, default: Optional[str] = None) -> Optional[str]:
	"""Get an environment variable text value with default."""
	return os.getenv(name, default)
