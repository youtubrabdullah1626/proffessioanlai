from typing import Dict, Any

from .logging_utils import setup_logging
from .intent_parser import parse_intent
from .browser_control import google_search
from .app_control import open_app, close_app_by_name
from .system_control import shutdown, restart, sleep, lock, take_screenshot
from .whatsapp_automation import WhatsAppAutomation
from .config import load_settings
from .scheduler import Scheduler
from .dev_api import optimize_system as optimize_api

logger = setup_logging()


def execute_command(raw_text: str) -> Dict[str, Any]:
    res = parse_intent(raw_text)
    intent = res.get("intent")
    settings = load_settings()
    wa = WhatsAppAutomation(settings)
    try:
        if intent == "send_whatsapp":
            ok = wa.send_text(res.get("contact", ""), res.get("message", ""), prefer_web=(res.get("channel") == "web"))
            return {"ok": ok, "handler": "whatsapp"}
        if intent == "open_app":
            ok = open_app(res.get("app") or "")
            return {"ok": ok, "handler": "open_app"}
        if intent == "close_app":
            ok = close_app_by_name((res.get("app") or "") + ".exe") > 0
            return {"ok": ok, "handler": "close_app"}
        if intent == "search_web":
            ok = google_search(settings, res.get("raw") or "")
            return {"ok": ok, "handler": "search_web"}
        if intent == "system_action":
            action = res.get("action")
            if action == "shutdown":
                return {"ok": shutdown(), "handler": "shutdown"}
            if action == "restart":
                return {"ok": restart(), "handler": "restart"}
            if action == "sleep":
                return {"ok": sleep(), "handler": "sleep"}
            if action == "lock":
                return {"ok": lock(), "handler": "lock"}
        if intent == "optimize_system":
            res_o = optimize_api()
            return res_o
        if intent == "screenshot":
            ok = take_screenshot("screenshot.png")
            return {"ok": ok, "handler": "screenshot", "path": "screenshot.png"}
        if intent == "error_analysis":
            return {"ok": True, "handler": "error_analysis"}
        if intent == "schedule":
            sch = Scheduler()
            ok = sch.schedule_from_text(res.get("raw") or "", "Reminder")
            return {"ok": ok, "handler": "schedule"}
        return {"ok": False, "handler": "unknown"}
    except Exception as e:
        logger.error(f"execute_command failed: {e}")
        return {"ok": False, "handler": "error", "error": str(e)}
