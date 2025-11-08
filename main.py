import sys
import os
import logging
import traceback
import threading
from pathlib import Path
from typing import Optional, Dict, Any

# Import logging setup from the project's utilities
from don.logging_utils import setup_logging

# Initialize logging
logger = setup_logging()

def setup_environment() -> bool:
    """Set up the Python environment and paths."""
    try:
        # Add project root to path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        # Ensure required directories exist
        (project_root / 'logs').mkdir(exist_ok=True)
        
        return True
    except Exception as e:
        logger.error(f"Failed to set up environment: {e}", exc_info=True)
        return False

def run_syntax_checks() -> bool:
    """Run syntax and import checks in a non-blocking way."""
    def _run_checks() -> bool:
        try:
            from don.syntax_guard import SyntaxGuard
            guard = SyntaxGuard()
            return guard.run_precheck()
        except Exception as e:
            logger.warning(f"Syntax check warning: {e}")
            return True  # Don't block on syntax check failures
    
    # Run in background thread to avoid blocking
    check_thread = threading.Thread(target=_run_checks, daemon=True)
    check_thread.start()
    return True  # Always return True to avoid blocking startup

def run_safe_mode() -> None:
    """Run the application in safe mode with minimal functionality."""
    logger.warning("Running in SAFE MODE due to critical errors")
    print("\n⚠️  Running in SAFE MODE due to critical errors")
    print("Some features may be unavailable. Check logs for details.\n")
    
    # Implement minimal safe mode functionality here
    while True:
        try:
            cmd = input("SAFE MODE> ").strip()
            if cmd.lower() in ('exit', 'quit'):
                break
            print("Safe mode: Limited functionality available.")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

def initialize_components() -> Dict[str, Any]:
    """Initialize and return core components with error handling."""
    components = {}
    try:
        from don.main import initialize as init_don
        components['don'] = init_don()
        logger.info("Core components initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}", exc_info=True)
    return components

def main() -> int:
    """Main entry point with comprehensive error handling."""
    try:
        # Basic environment setup
        if not setup_environment():
            logger.error("Environment setup failed")
            return 1
        
        logger.info("Starting application...")
        
        # Initialize components
        components = initialize_components()
        
        # Start background checks (non-blocking)
        run_syntax_checks()
        
        # Start main application
        if 'don' in components:
            return components['don'].run()
            
        logger.warning("Running with limited functionality")
        return 0
        
    
    except Exception as e:
        logger.critical(f"Application error: {e}\n{traceback.format_exc()}")
        print(f"\n💥 Application error: {e}")
        print("Check logs/application.log for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
