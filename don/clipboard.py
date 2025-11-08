from typing import List, Optional

try:
    import win32clipboard  # type: ignore
    exists_win32 = True
except Exception:
    exists_win32 = False

from .logging_utils import setup_logging

logger = setup_logging()


class ClipboardHistory:
    """Simple clipboard history in RAM with optional file mini-log."""
    def __init__(self, max_items: int = 50, mini_log_path: Optional[str] = None) -> None:
        self.items: List[str] = []
        self.max_items = max_items
        self.mini_log_path = mini_log_path

    def add(self, text: str) -> None:
        try:
            self.items.append(text)
            if len(self.items) > self.max_items:
                self.items.pop(0)
            if self.mini_log_path:
                with open(self.mini_log_path, "a", encoding="utf-8") as f:
                    f.write(text.replace("\n", " ")[:500] + "\n")
        except Exception as e:
            logger.error(f"ClipboardHistory add failed: {e}")

    def last(self) -> Optional[str]:
        return self.items[-1] if self.items else None


def get_clipboard_text() -> Optional[str]:
    """Get text from Windows clipboard if available, else None."""
    try:
        if not exists_win32:
            logger.warning("pywin32 not available; clipboard text unavailable")
            return None
        win32clipboard.OpenClipboard()
        try:
            data = win32clipboard.GetClipboardData()
        finally:
            win32clipboard.CloseClipboard()
        if isinstance(data, str):
            return data
        return None
    except Exception as e:
        logger.error(f"get_clipboard_text failed: {e}")
        return None


def set_clipboard_text(text: str) -> bool:
    """Set text to Windows clipboard. Returns True if success."""
    try:
        if not exists_win32:
            logger.warning("pywin32 not available; cannot set clipboard")
            return False
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text)
            return True
        finally:
            win32clipboard.CloseClipboard()
    except Exception as e:
        logger.error(f"set_clipboard_text failed: {e}")
        return False
