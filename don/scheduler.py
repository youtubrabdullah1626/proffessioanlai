import threading
import time
import sqlite3
import os
from typing import Optional

from .logging_utils import setup_logging
from .memory_manager import init_m2, MEMORY_DB
from .time_parse import parse_natural_time

logger = setup_logging()


class Scheduler:
	def __init__(self) -> None:
		self._stop = False
		self._thr: Optional[threading.Thread] = None
		init_m2()

	def start(self) -> None:
		if self._thr and self._thr.is_alive():
			return
		self._stop = False
		self._thr = threading.Thread(target=self._run, daemon=True)
		self._thr.start()

	def _run(self) -> None:
		while not self._stop:
			try:
				now = time.time()
				con = sqlite3.connect(MEMORY_DB)
				cur = con.cursor()
				cur.execute("SELECT id, when_ts, title, status FROM reminders WHERE status='pending' AND when_ts<=?", (now,))
				rows = cur.fetchall()
				for rid, when_ts, title, status in rows:
					logger.info(f"Reminder due: {title}")
					cur.execute("UPDATE reminders SET status='done' WHERE id=?", (rid,))
				con.commit(); con.close()
			except Exception:
				pass
			time.sleep(1.0)

	def stop(self) -> None:
		self._stop = True

	def schedule(self, when_ts: float, title: str) -> bool:
		try:
			con = sqlite3.connect(MEMORY_DB)
			cur = con.cursor()
			cur.execute("INSERT INTO reminders (when_ts, title, status) VALUES (?,?,?)", (when_ts, title, 'pending'))
			con.commit(); con.close()
			logger.info(f"Scheduled reminder: {title} at {when_ts}")
			return True
		except Exception as e:
			logger.error(f"schedule failed: {e}")
			return False

	def schedule_from_text(self, text: str, title: str) -> bool:
		try:
			when = parse_natural_time(text)
			if when is None:
				logger.warning("Could not parse time from text.")
				return False
			return self.schedule(when, title)
		except Exception as e:
			logger.error(f"schedule_from_text failed: {e}")
			return False
