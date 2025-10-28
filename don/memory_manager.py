import json
import os
import sqlite3
from typing import Dict, Any, Optional

from .logging_utils import setup_logging

logger = setup_logging()

MEMORY_JSON = os.path.join("memory", "memory.json")
MEMORY_DB = os.path.join("memory", "memory.db")


def load_m1() -> Dict[str, Any]:
	"""Load memory.json (M1) or return defaults."""
	try:
		if not os.path.exists(MEMORY_JSON):
			return {"nicknames": {}, "preferred_whatsapp_channel": "desktop", "last_tone": "friendly"}
		with open(MEMORY_JSON, "r", encoding="utf-8") as f:
			return json.load(f)
	except Exception as e:
		logger.error(f"load_m1 failed: {e}")
		return {"nicknames": {}, "preferred_whatsapp_channel": "desktop", "last_tone": "friendly"}


def save_m1(data: Dict[str, Any]) -> bool:
	"""Persist memory.json (M1)."""
	try:
		os.makedirs(os.path.dirname(MEMORY_JSON), exist_ok=True)
		with open(MEMORY_JSON, "w", encoding="utf-8") as f:
			json.dump(data, f, indent=2)
		return True
	except Exception as e:
		logger.error(f"save_m1 failed: {e}")
		return False


def init_m2() -> bool:
	"""Initialize sqlite DB schema for scans, history, reminders, logs, habits."""
	try:
		os.makedirs(os.path.dirname(MEMORY_DB), exist_ok=True)
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
		return True
	except Exception as e:
		logger.error(f"init_m2 failed: {e}")
		return False


def remember_nickname(name: str, phone: str) -> bool:
	"""Update M1 nicknames map and save."""
	try:
		m1 = load_m1()
		m1.setdefault("nicknames", {})[name.lower()] = phone
		return save_m1(m1)
	except Exception as e:
		logger.error(f"remember_nickname failed: {e}")
		return False
