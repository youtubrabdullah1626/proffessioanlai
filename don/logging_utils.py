import logging
import os
import re
from typing import Any

from colorama import Fore, Style, init as colorama_init


def mask_phone(text: str) -> str:
    """Mask phone numbers, leaving last 3 digits visible.
    Example: 923001234567 -> *********567
    """
    try:
        return re.sub(r"(\+?\d{7,})(\d{3})", r"*********\2", text)
    except Exception:
        return text


def mask_pii(obj: Any) -> Any:
    """Mask PII if string-like; passthrough otherwise."""
    try:
        if isinstance(obj, str):
            return mask_phone(obj)
        return obj
    except Exception:
        return obj


def setup_logging() -> logging.Logger:
    """Configure root logger with level from env LOG_LEVEL, color console, and file handler.
    Ensures a file handler for the current working directory on every call.
    """
    colorama_init(autoreset=True)
    logger = logging.getLogger("don")
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(level)

    class Formatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            msg = super().format(record)
            msg = mask_phone(msg)
            levelname = record.levelname
            color = {
                "DEBUG": Fore.BLUE,
                "INFO": Fore.GREEN,
                "WARNING": Fore.YELLOW,
                "ERROR": Fore.RED,
                "CRITICAL": Fore.MAGENTA,
            }.get(levelname, "")
            return f"{color}{msg}{Style.RESET_ALL}"

    # Ensure console handler exists once
    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in logger.handlers):
        console = logging.StreamHandler()
        console.setFormatter(Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s"))
        logger.addHandler(console)

    # Ensure file handler for current CWD exists
    try:
        os.makedirs("logs", exist_ok=True)
        target_path = os.path.abspath(os.path.join("logs", "assistant.log"))
        has_file = False
        for h in logger.handlers:
            if isinstance(h, logging.FileHandler):
                # Compare normalized absolute paths
                try:
                    if os.path.abspath(getattr(h, "baseFilename", "")) == target_path:
                        has_file = True
                        break
                except Exception:
                    continue
        if not has_file:
            fh = logging.FileHandler(target_path, encoding="utf-8")
            fh.setFormatter(logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s"))
            logger.addHandler(fh)
    except Exception:
        pass

    return logger
