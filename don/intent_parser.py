import re
from typing import Dict, Any

from .logging_utils import setup_logging

logger = setup_logging()


INTENTS = {
    "send_whatsapp",
    "open_app",
    "close_app",
    "optimize_system",
    "system_status",
    "system_action",
    "file_action",
    "search_web",
    "schedule",
    "error_analysis",
    "screenshot",
    "unknown",
}

WAKE_WORDS = ("hey don", "don,", "don ", " don")


def parse_intent(text: str) -> Dict[str, Any]:
    """Parse user text into the JSON-like schema.
    Heuristics for Roman Urdu + English keywords.
    """
    raw = text or ""
    lower = raw.lower().strip()
    # Strip wake words
    for w in WAKE_WORDS:
        if lower.startswith(w):
            lower = lower[len(w):].strip()
            break

    intent = "unknown"
    confidence = 0.5
    channel = "auto"
    contact = ""
    message = ""
    app = ""
    path = ""
    action = ""

    # Channel hints
    if "whatsapp web" in lower or re.search(r"\bweb\b", lower):
        channel = "web"
    elif "whatsapp" in lower:
        channel = "desktop"

    # WhatsApp send
    if "whatsapp" in lower and ("msg" in lower or "message" in lower or "bolo" in lower or "kaho" in lower or "karo" in lower or "kro" in lower):
        intent = "send_whatsapp"
        confidence = 0.88
        m = re.search(r"\b(ali|ahmad|bilal|zara|fatima|hassan|usman)\b", lower)
        if m:
            contact = m.group(1)
        else:
            m = re.search(r"\bko\s+([\w\.\-]+)", lower)
            if m:
                contact = m.group(1).strip(" ,.")
        mq = re.search(r"\"([^\"]+)\"|'([^']+)'", raw)
        if mq:
            message = mq.group(1) or mq.group(2) or ""
        else:
            m2 = re.search(r"(?:msg|message|bolo|kaho|kro|karo)\s+(.*)$", raw, re.IGNORECASE)
            if m2:
                message = m2.group(1).strip()

    # Scheduling
    if intent == "unknown":
        if re.search(r"\b(remind|reminder|uthana|yaad\s*rakhna|schedule)\b", lower):
            intent = "schedule"; confidence = 0.85

    # Error analysis
    if intent == "unknown":
        if re.search(r"\berror\b", lower):
            intent = "error_analysis"; confidence = 0.8

    # System actions
    if intent == "unknown":
        if any(k in lower for k in ["shutdown", "band kar", "band kr", "pc band"]):
            intent = "system_action"; action = "shutdown"; confidence = 0.92
        elif "restart" in lower or "dobara start" in lower:
            intent = "system_action"; action = "restart"; confidence = 0.9
        elif "sleep" in lower:
            intent = "system_action"; action = "sleep"; confidence = 0.8
        elif "lock" in lower:
            intent = "system_action"; action = "lock"; confidence = 0.8

    # Open/close app
    if intent == "unknown":
        if any(k in lower for k in ["kholo", "open", "launch"]):
            intent = "open_app"; confidence = 0.8
            m = re.search(r"(chrome|edge|whatsapp|vs\s?code|notepad|spotify)", lower)
            if m:
                app = m.group(1)
        elif any(k in lower for k in ["band karo", "close", "quit"]):
            intent = "close_app"; confidence = 0.8
            m = re.search(r"(chrome|edge|whatsapp|vs\s?code|notepad|spotify)", lower)
            if m:
                app = m.group(1)

    # Web search
    if intent in {"open_app", "unknown"} and ("search" in lower or "talash" in lower):
        intent = "search_web"
        confidence = 0.8

    # File actions
    if intent == "unknown" and any(k in lower for k in ["delete", "remove", "rename", "move", "create"]):
        intent = "file_action"
        confidence = 0.75

    if intent == "unknown" and re.search(r"\b(optimi[zs]e|optimize|system\s*optimize|saaf|clean)\b", lower):
        intent = "optimize_system"; confidence = 0.8

    if intent == "unknown" and re.search(r"\bscreenshot\b|screen\s*shot", lower):
        intent = "screenshot"; confidence = 0.85

    return {
        "intent": intent,
        "confidence": round(confidence, 2),
        "channel": channel,
        "contact": contact,
        "message": message,
        "app": app,
        "path": path,
        "action": action,
        "raw": raw,
    }
