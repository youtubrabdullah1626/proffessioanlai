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
    """
    Main execution router for all parsed intents.
    Handles app, system, browser, WhatsApp, and general utility commands.
    """
    res = parse_intent(raw_text)
    intent = (res.get("intent") or "").lower().strip()
    settings = load_settings()
    wa = WhatsAppAutomation(settings)

    try:
        # --- WhatsApp ---
        if intent in ["send_whatsapp", "whatsapp_message", "send_message"]:
            ok = wa.send_text(
                res.get("contact", ""),
                res.get("message", ""),
                prefer_web=(res.get("channel") == "web")
            )
            return {"ok": ok, "handler": "whatsapp"}

        # --- Open apps ---
        if intent in ["open", "open_app", "launch", "run", "start"]:
            app_name = (res.get("app") or res.get("target") or "").strip().lower()
            if not app_name:
                return {"ok": False, "handler": "open_app", "reason": "no_app"}
            ok = open_app(app_name)
            return {"ok": ok, "handler": "open_app", "app": app_name}

        # --- Close apps ---
        if intent in ["close", "close_app", "exit", "terminate", "shutdown_app"]:
            app_name = (res.get("app") or "").strip().lower()
            if not app_name:
                return {"ok": False, "handler": "close_app", "reason": "no_app"}
            ok = close_app_by_name(app_name + ".exe") > 0
            return {"ok": ok, "handler": "close_app", "app": app_name}

        # --- Web search ---
        if intent in ["search_web", "google", "search"]:
            query = res.get("raw") or res.get("query") or ""
            ok = google_search(settings, query)
            return {"ok": ok, "handler": "search_web", "query": query}

        # --- System actions ---
        if intent in ["system_action", "shutdown", "restart", "sleep", "lock"]:
            action = res.get("action") or intent
            if action == "shutdown":
                return {"ok": shutdown(), "handler": "shutdown"}
            if action == "restart":
                return {"ok": restart(), "handler": "restart"}
            if action == "sleep":
                return {"ok": sleep(), "handler": "sleep"}
            if action == "lock":
                return {"ok": lock(), "handler": "lock"}

        # --- Optimize / Maintenance ---
        if intent in ["optimize_system", "cleanup", "boost"]:
            return optimize_api()

        # --- Screenshot ---
        if intent in ["screenshot", "take_screenshot", "capture"]:
            ok = take_screenshot("screenshot.png")
            return {"ok": ok, "handler": "screenshot", "path": "screenshot.png"}

        # --- Scheduling ---
        if intent in ["schedule", "reminder", "set_alarm"]:
            sch = Scheduler()
            ok = sch.schedule_from_text(res.get("raw") or "", "Reminder")
            return {"ok": ok, "handler": "schedule"}

        # --- Debug / Unknown ---
        if intent == "error_analysis":
            return {"ok": True, "handler": "error_analysis"}

        return {"ok": False, "handler": "unknown", "raw_intent": intent, "parsed": res}

    except Exception as e:
        logger.error(f"execute_command failed: {e}")
        return {"ok": False, "handler": "error", "error": str(e)}
