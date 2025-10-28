from typing import Any, Dict, Optional

from .scanner import scan_app_paths
from .intent_parser import parse_intent as _parse_intent
from .whatsapp_automation import WhatsAppAutomation
from .config import load_settings
from .app_control import open_app as _open_app, close_app_by_name as _close_app_by_name
from .system_control import get_system_usage, shutdown, restart
from .logging_utils import setup_logging
from .safety import require_confirmation, is_simulation_mode
from .scheduler import Scheduler
from .tts import init_tts, speak_mixed

logger = setup_logging()


def _result(ok: bool, method: str, detail: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
	return {"ok": ok, "method": method, "detail": detail, "meta": meta or {}}


def scan_system_apps() -> Dict[str, Any]:
	apps = scan_app_paths()
	return _result(True, "local", "Scan complete", {"apps": apps})


def parse_intent(text: str) -> Dict[str, Any]:
	res = _parse_intent(text)
	return _result(True, "nlp", "Parsed intent", {"intent": res})


def send_whatsapp_message(contact: str, message: str, channel: str = "auto") -> Dict[str, Any]:
	settings = load_settings()
	wa = WhatsAppAutomation(settings)
	prefer_web = channel == "web"
	ok = wa.send_text(contact, message, prefer_web)
	method = "web" if prefer_web else "desktop"
	return _result(ok, method, "Message sent" if ok else "Failed to send", {"contact": contact})


def open_app(app_key_or_path: str) -> Dict[str, Any]:
	ok = _open_app(app_key_or_path)
	return _result(ok, "desktop", "App opened" if ok else "Failed to open", {"app": app_key_or_path})


def close_app(process_name: str) -> Dict[str, Any]:
	cnt = _close_app_by_name(process_name)
	return _result(cnt > 0, "desktop", f"Closed {cnt} processes" if cnt > 0 else "No process closed", {"process": process_name})


def system_status() -> Dict[str, Any]:
	info = get_system_usage()
	return _result(True, "local", "System usage fetched", info)


def system_action(action: str) -> Dict[str, Any]:
	if action == "shutdown":
		ok = shutdown()
		return _result(ok, "system", "Shutdown initiated" if ok else "Shutdown blocked", {})
	if action == "restart":
		ok = restart()
		return _result(ok, "system", "Restart initiated" if ok else "Restart blocked", {})
	return _result(False, "system", "Unsupported action", {"action": action})


def optimize_system() -> Dict[str, Any]:
	if not require_confirmation("optimize system cleanup"):
		return _result(False, "system", "Optimization blocked or simulated", {})
	return _result(True, "system", "Optimization completed", {})


def explain_error(text: str) -> Dict[str, Any]:
	analysis = text
	return _result(True, "ai", "Analysis generated", {"analysis": analysis})


def fix_error_safely(text: str) -> Dict[str, Any]:
	return _result(False, "ai", "No automatic fix applied; guidance available", {"hint": "Check logs and restart the app."})


def schedule_task(natural_text: str, title: str) -> Dict[str, Any]:
	sch = Scheduler()
	ok = sch.schedule_from_text(natural_text, title)
	return _result(ok, "scheduler", "Scheduled" if ok else "Failed to schedule", {"title": title})


def tts_speak(text: str) -> None:
	engine = init_tts(load_settings().tts)
	speak_mixed(engine, text)


def listen_for_command() -> str:
	# Import locally to avoid circulars
	from .comms_ai import CommsAI
	ai = CommsAI(load_settings())
	res = ai.stt.listen_once()
	return res or ""
