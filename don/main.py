from dotenv import load_dotenv
from .config import load_settings
from .logging_utils import setup_logging
from .tts import init_tts, speak_mixed
from .first_launch import ensure_first_launch
from .intent_parser import parse_intent
from .message_composer import compose_message
from .comms_ai import CommsAI
import time


def main() -> int:
	"""Entrypoint: initialize, first-launch setup, simple intent demo, and start background listener."""
	load_dotenv()
	logger = setup_logging()
	settings = load_settings()
	ensure_first_launch()
	engine = init_tts(settings.tts)

	speak_mixed(engine, "Don online hoon. Boliye, main sun raha hoon.")

	# Start background continuous listener
	ai = CommsAI(settings)
	ai.start_background_listening(loop_delay=0.5)

	# Keep main process alive; minimal idle loop
	try:
		while True:
			time.sleep(1.0)
	except KeyboardInterrupt:
		logger.info("Shutting down on user request.")
		ai.stop_background_listening()

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
