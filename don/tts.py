import os
from typing import Optional

from .logging_utils import setup_logging
from .config import TTSSettings

logger = setup_logging()

try:
	import edge_tts  # type: ignore
	has_edge_tts = True
except Exception:
	has_edge_tts = False

try:
	import pyttsx3  # type: ignore
	has_pyttsx3 = True
except Exception:
	has_pyttsx3 = False

# Module-level singleton
_TTS_SINGLETON = {
	"provider": None,  # "edge" | "pyttsx3" | None
	"engine": None,
	"voice": None,
}


def _naturalize_text(text: str) -> str:
	"""Lightly adjust text for more natural pacing in pyttsx3."""
	parts = [p.strip() for p in text.split(",") if p.strip()]
	if len(parts) <= 1:
		return text
	# Insert short pauses by adding commas
	return ", ".join(parts)


def init_tts(settings: TTSSettings) -> Optional[object]:
	"""Initialize TTS provider once and cache it.
	Honors DEFAULT_TTS=edge override from environment if available.
	"""
	if _TTS_SINGLETON["engine"] is not None:
		return _TTS_SINGLETON["engine"]

	preferred = os.getenv("DEFAULT_TTS", settings.engine or "pyttsx3").strip().lower()
	if preferred == "edge" and has_edge_tts:
		_TTS_SINGLETON["provider"] = "edge"
		_TTS_SINGLETON["engine"] = object()  # placeholder handle
		_TTS_SINGLETON["voice"] = os.getenv("EDGE_TTS_VOICE", "en-US-JennyNeural")
		logger.info("TTS engine initialized (Edge TTS)")
		return _TTS_SINGLETON["engine"]

	if has_pyttsx3:
		try:
			engine = pyttsx3.init()
			if settings.rate:
				engine.setProperty("rate", max(140, min(220, settings.rate)))
			# Optional voice selection
			if settings.voice and settings.voice != "default":
				voices = engine.getProperty("voices")
				for v in voices:
					if settings.voice.lower() in (v.name or "").lower():
						engine.setProperty("voice", v.id)
						break
			_TTS_SINGLETON["provider"] = "pyttsx3"
			_TTS_SINGLETON["engine"] = engine
			logger.info("TTS engine initialized (pyttsx3)")
			return engine
		except Exception as e:
			logger.error(f"TTS init failed (pyttsx3): {e}")

	logger.warning("No TTS provider available; will simulate speech via logs.")
	_TTS_SINGLETON["provider"] = None
	_TTS_SINGLETON["engine"] = None
	return None


def speak_mixed(engine: Optional[object], text: str) -> bool:
	"""Speak mixed Roman Urdu + English text using the selected TTS provider.
	Returns True if spoken or simulated.
	"""
	try:
		provider = _TTS_SINGLETON.get("provider")
		if provider == "edge" and has_edge_tts:
			ssml = f"""
			<speak version='1.0' xml:lang='en-US'>
				<voice name='{_TTS_SINGLETON.get('voice') or 'en-US-JennyNeural'}'>
					<prosody rate='+5%' pitch='+2%'> {text} </prosody>
				</voice>
			</speak>
			"""
			try:
				# Run edge-tts synchronously for simplicity
				import asyncio

				async def _run():
					communicate = edge_tts.Communicate(ssml=ssml, text=None)
					# Discard audio (simulation mode), but still invoke synth to validate
					async for _ in communicate.stream():
						break
				asyncio.run(_run())
				logger.info(f"[TTS:Edge] {text}")
				return True
			except Exception as e:
				logger.warning(f"Edge TTS speak failed, falling back: {e}")
				# fall through to pyttsx3 if available

		if provider == "pyttsx3" and has_pyttsx3 and engine is not None:
			to_say = _naturalize_text(text)
			engine.say(to_say)
			engine.runAndWait()
			logger.info(f"[TTS:pyttsx3] {to_say}")
			return True

		# No engine: simulate
		logger.info(f"[TTS] Would speak: {text}")
		return False
	except Exception as e:
		logger.error(f"TTS speak failed: {e}")
		return False
