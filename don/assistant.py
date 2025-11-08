"""
Main module for the AI Voice Assistant.

This module contains the core functionality for the voice assistant,
including the main Assistant class that orchestrates voice interaction.
"""
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Set up logger
logger = logging.getLogger(__name__)

class Assistant:
    """Main assistant class that manages the voice interaction loop.
    
    This class ties together voice recognition, command processing, and text-to-speech
    to create a seamless voice assistant experience.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the assistant with optional configuration.
        
        Args:
            config: Optional dictionary containing configuration settings.
        """
        self.config = config or {}
        self.voice_engine = None
        self.command_handler = None
        self.is_running = False
        
        # Initialize components
        self._initialize_components()
        
        logger.info("Assistant initialized")
    
    def _initialize_components(self):
        """Initialize all required components."""
        try:
            from .voice import VoiceEngine
            from .commands import CommandHandler
            
            # Initialize voice engine
            self.voice_engine = VoiceEngine(
                energy_threshold=self.config.get('energy_threshold', 300),
                pause_threshold=self.config.get('pause_threshold', 0.8),
                dynamic_energy_threshold=self.config.get('dynamic_energy_threshold', True),
                wake_word=self.config.get('wake_word', 'hey don'),
                wake_word_sensitivity=self.config.get('wake_word_sensitivity', 0.5),
                speech_rate=self.config.get('speech_rate', 180),
                voice_gender=self.config.get('voice_gender', 'female')
            )
            
            # Initialize command handler
            self.command_handler = CommandHandler()
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}", exc_info=True)
            raise
    
    def run(self):
        """Start the main interaction loop."""
        if not self.voice_engine or not self.command_handler:
            logger.error("Cannot start: components not properly initialized")
            return
            
        self.is_running = True
        logger.info("Starting assistant...")
        
        try:
            while self.is_running:
                # Listen for the wake word
                if self.voice_engine.listen_for_wake_word():
                    # Process the command after wake word is detected
                    self._process_command()
                    
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def _process_command(self):
        """Listen for and process a voice command."""
        if not self.voice_engine or not self.command_handler:
            return
            
        # Listen for a command
        command = self.voice_engine.listen_for_command()
        
        if command:
            # Process the command and get a response
            response = self.command_handler.process(command)
            
            # Speak the response
            if response:
                self.voice_engine.speak(response)
    
    def cleanup(self):
        """Clean up resources."""
        self.is_running = False
        if self.voice_engine:
            self.voice_engine.cleanup()
        logger.info("Assistant shutdown complete")

def initialize(config: Optional[Dict[str, Any]] = None) -> Assistant:
    """Initialize and return an Assistant instance.
    
    This is the main entry point for creating an Assistant instance.
    
    Args:
        config: Optional configuration dictionary.
        
    Returns:
        An initialized Assistant instance.
    """
    return Assistant(config)

# For backward compatibility
initialize_assistant = initialize

if __name__ == "__main__":
    # Example usage
    import logging
    logging.basicConfig(level=logging.INFO)
    
    assistant = Assistant()
    assistant.run()
