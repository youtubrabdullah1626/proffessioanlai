from typing import Optional

from .browser_control import google_search
from .comms_ai import GeminiClient
from .config import load_settings
from .logging_utils import setup_logging
from .tts import init_tts, speak_mixed

logger = setup_logging()


def web_search(query: str) -> bool:
    settings = load_settings()
    return google_search(settings, query)


def explain_with_gemini(text: str) -> str:
    client = GeminiClient(None)
    return client.analyze_intent(text)


def read_and_explain(text: str) -> bool:
    settings = load_settings()
    tts = init_tts(settings.tts)
    spoken = speak_mixed(tts, text)
    if not spoken:
        return False
    explanation = explain_with_gemini(text)
    return speak_mixed(tts, f"Explanation: {explanation}")
