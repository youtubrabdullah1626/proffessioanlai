from .logging_utils import setup_logging
from .comms_ai import CommsAI
from .config import load_settings
from .intent_parser import parse_intent
from .executor import execute_command
from .tts import init_tts, speak_mixed

logger = setup_logging()


def run_once_with_voice() -> None:
    settings = load_settings()
    ai = CommsAI(settings)
    engine = init_tts(settings.tts)
    text = ai.stt.listen_once()
    if not text:
        speak_mixed(engine, "Kuch sunai nahi diya. Dobara bolo please.")
        return
    res = parse_intent(text)
    out = execute_command(text)
    if out.get("ok"):
        speak_mixed(engine, "Done ho gaya.")
    else:
        speak_mixed(engine, "Kuch masla aaya. Try kar raha hoon fallback." )
