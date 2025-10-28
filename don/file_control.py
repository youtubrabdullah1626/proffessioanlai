import os
import shutil
from typing import List, Optional

from .logging_utils import setup_logging
from .safety import is_simulation_mode, require_confirmation

logger = setup_logging()


def create_file(path: str, content: str = "") -> bool:
	try:
		if is_simulation_mode():
			logger.info(f"[SIMULATION] Would create file: {path}")
			return True
		os.makedirs(os.path.dirname(path), exist_ok=True)
		with open(path, "w", encoding="utf-8") as f:
			f.write(content)
		return True
	except Exception as e:
		logger.error(f"create_file failed: {e}")
		return False


def move_path(src: str, dst: str) -> bool:
	try:
		if is_simulation_mode():
			logger.info(f"[SIMULATION] Would move: {src} -> {dst}")
			return True
		os.makedirs(os.path.dirname(dst), exist_ok=True)
		shutil.move(src, dst)
		return True
	except Exception as e:
		logger.error(f"move_path failed: {e}")
		return False


def rename_path(src: str, new_name: str) -> bool:
	try:
		dirname = os.path.dirname(src)
		dst = os.path.join(dirname, new_name)
		if is_simulation_mode():
			logger.info(f"[SIMULATION] Would rename: {src} -> {dst}")
			return True
		os.rename(src, dst)
		return True
	except Exception as e:
		logger.error(f"rename_path failed: {e}")
		return False


def delete_path(path: str, confirm_threshold: int = 5) -> bool:
	try:
		total = 1
		if os.path.isdir(path):
			count = 0
			for _, _, files in os.walk(path):
				count += len(files)
			total = count
		action = f"delete {path} (approx {total} items)"
		if total > confirm_threshold and not require_confirmation(action):
			return False
		if is_simulation_mode():
			logger.info(f"[SIMULATION] Would delete: {path}")
			return True
		if os.path.isdir(path):
			shutil.rmtree(path)
		else:
			os.remove(path)
		return True
	except Exception as e:
		logger.error(f"delete_path failed: {e}")
		return False


def search_files(root: str, pattern: str) -> List[str]:
	out: List[str] = []
	try:
		for dirpath, _, files in os.walk(root):
			for fn in files:
				if pattern.lower() in fn.lower():
					out.append(os.path.join(dirpath, fn))
		return out
	except Exception:
		return out


def read_small_file(path: str, max_bytes: int = 20000) -> Optional[str]:
	try:
		size = os.path.getsize(path)
		if size > max_bytes:
			logger.warning("File too large to read fully; increase limit if needed.")
		return open(path, "r", encoding="utf-8", errors="ignore").read(max_bytes)
	except Exception as e:
		logger.error(f"read_small_file failed: {e}")
		return None


def summarize_text(text: str, max_len: int = 300) -> str:
	try:
		# Placeholder simple summarization: return head + tail
		text = text.strip()
		if len(text) <= max_len:
			return text
		return text[: max_len // 2] + " ... " + text[-max_len // 2 :]
	except Exception:
		return text
