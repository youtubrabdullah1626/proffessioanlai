from don.tts import init_tts, speak_mixed
from don.config import load_settings

_engine = None

def speak(text: str) -> bool:
	global _engine
	if _engine is None:
		_engine = init_tts(load_settings().tts)
	return speak_mixed(_engine, text)
