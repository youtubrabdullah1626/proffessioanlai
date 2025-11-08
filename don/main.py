import os
import sys
import logging
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import local modules after path is set
from don.config import load_settings
from don.logging_utils import setup_logging
from don.tts import init_tts, speak_mixed
from don.first_launch import ensure_first_launch
from don.comms_ai import CommsAI
from don.project_validator import validate_project_integrity
import time


def main() -> int:
    """Entrypoint: initialize, first-launch setup, simple intent demo, and start background listener."""
    # Load environment and setup logging
    load_dotenv()
    logger = setup_logging()
    
    # Validate project integrity before proceeding
    logger.info("Validating project integrity...")
    if not validate_project_integrity():
        logger.error("Project validation failed. Please fix the reported issues.")
        return 1
    
    # Load settings and initialize components
    settings = load_settings()
    ensure_first_launch()
    
    try:
        engine = init_tts(settings.tts)
    except Exception as e:
        logger.error(f"Failed to initialize TTS: {e}")
        return 1

    try:
        speak_mixed(engine, "Don online hoon. Boliye, main sun raha hoon.")

        # Start background continuous listener
        ai = CommsAI(settings)
        ai.start_background_listening(loop_delay=0.5)
        logger.info("Voice assistant is now listening. Press Ctrl+C to exit.")

        # Keep main process alive; minimal idle loop
        while True:
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        logger.info("Shutting down on user request.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1
    finally:
        if 'ai' in locals():
            ai.stop_background_listening()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
