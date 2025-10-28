from don.comms_ai import CommsAI
from don.config import load_settings


def listen_once_text() -> str:
	ai = CommsAI(load_settings())
	res = ai.stt.listen_once()
	return res or ""
