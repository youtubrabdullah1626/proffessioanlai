import logging

try:
	import pyttsx3  # type: ignore
	has_pyttsx3 = True
except Exception:
	has_pyttsx3 = False

_engine = None


def get_tts_engine():
	global _engine
	if _engine is None and has_pyttsx3:
		try:
			_engine = pyttsx3.init()
			_engine.setProperty('rate', 150)
			_engine.setProperty('volume', 0.9)
			voices = _engine.getProperty('voices')
			if voices:
				_engine.setProperty('voice', voices[0].id)
			logging.info("TTS engine initialized (pyttsx3)")
		except Exception as e:
			logging.exception("Failed to initialize pyttsx3: %s", e)
			_engine = None
	return _engine


def speak(text: str):
	engine = get_tts_engine()
	if engine:
		engine.say(text)
		engine.runAndWait()
	else:
		logging.warning("No TTS engine available. Text was: %s", text)
