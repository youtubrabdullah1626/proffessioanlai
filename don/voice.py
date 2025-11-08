"""
Voice module for the AI Voice Assistant.

This module handles all voice-related functionality including:
- Speech recognition
- Text-to-speech
- Wake word detection
- Audio processing
"""
import queue
import threading
import logging
from typing import Optional, List, Dict, Any

# Third-party imports
try:
    import speech_recognition as sr
    import pyttsx3
    import pyaudio
    from pydub import AudioSegment
    from pydub.playback import play
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Required audio libraries not found. Voice features will be disabled.")

logger = logging.getLogger(__name__)

class VoiceEngine:
    """Handles all voice-related functionality for the assistant."""
    
    def __init__(self, 
                 energy_threshold: int = 300,
                 pause_threshold: float = 0.8,
                 dynamic_energy_threshold: bool = True,
                 wake_word: str = "hey don",
                 wake_word_sensitivity: float = 0.5,
                 speech_rate: int = 180,
                 voice_gender: str = "female"):
        """Initialize the voice engine.
        
        Args:
            energy_threshold: Energy level for considering something as speech.
            pause_threshold: Seconds of non-speaking audio before a phrase is considered complete.
            dynamic_energy_threshold: Whether to adjust energy threshold dynamically.
            wake_word: The wake word to listen for (case-insensitive).
            wake_word_sensitivity: Sensitivity for wake word detection (0.0 to 1.0).
            speech_rate: Speech rate in words per minute.
            voice_gender: Preferred voice gender ('male', 'female', or 'neutral').
        """
        if not TTS_AVAILABLE:
            logger.error("Required audio libraries not available. Voice features disabled.")
            raise ImportError("Required audio libraries not available.")
            
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.pause_threshold = pause_threshold
        self.recognizer.dynamic_energy_threshold = dynamic_energy_threshold
        
        self.wake_word = wake_word.lower()
        self.wake_word_sensitivity = max(0.0, min(1.0, wake_word_sensitivity))  # Clamp to 0-1
        self.speech_rate = speech_rate
        self.voice_gender = voice_gender.lower()
        
        self.microphone = None
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.processing_thread = None
        self.tts_engine = None
        
        # Initialize components
        self._init_microphone()
        self._init_tts()
        
        logger.info("Voice engine initialized")
    
    def _init_microphone(self):
        """Initialize the microphone with error handling."""
        try:
            self.microphone = sr.Microphone()
            logger.info("Microphone initialized successfully")
            
            # Calibrate for ambient noise in the background
            self._calibrate_microphone()
            
        except Exception as e:
            logger.error(f"Failed to initialize microphone: {e}")
            self.microphone = None
            raise RuntimeError("Microphone initialization failed. Please check your audio devices.")
    
    def _init_tts(self):
        """Initialize the text-to-speech engine."""
        try:
            self.tts_engine = pyttsx3.init()
            
            # Set voice properties
            voices = self.tts_engine.getProperty('voices')
            
            # Try to find a voice matching the preferred gender
            preferred_voices = []
            for voice in voices:
                if self.voice_gender in voice.name.lower():
                    preferred_voices.append(voice)
            
            if preferred_voices:
                # Use the first matching voice
                self.tts_engine.setProperty('voice', preferred_voices[0].id)
                logger.debug(f"Using voice: {preferred_voices[0].name}")
            else:
                logger.warning(f"No {self.voice_gender} voice found, using default voice")
            
            # Adjust speech rate (words per minute)
            self.tts_engine.setProperty('rate', self.speech_rate)
            logger.debug(f"Speech rate set to {self.speech_rate} words per minute")
            
            # Set volume to maximum (0.0 to 1.0)
            self.tts_engine.setProperty('volume', 1.0)
            
            logger.info("TTS engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.tts_engine = None
            raise RuntimeError("Text-to-speech initialization failed.")
    
    def _calibrate_microphone(self, duration: float = 1.0):
        """Calibrate the microphone for ambient noise.
        
        Args:
            duration: How long to listen for ambient noise (in seconds).
        """
        if not self.microphone:
            return
            
        def calibrate():
            with self.microphone as source:
                logger.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                logger.info(f"Energy threshold set to: {self.recognizer.energy_threshold}")
        
        # Run in a separate thread to avoid blocking
        threading.Thread(target=calibrate, daemon=True).start()
    
    def listen_for_wake_word(self) -> bool:
        """Listen for the wake word in a loop.
        
        Returns:
            bool: True if wake word was detected, False on error.
        """
        if not self.microphone:
            return False
            
        try:
            with self.microphone as source:
                logger.debug("Listening for wake word...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
                
            # Recognize speech using Google's speech recognition
            text = self.recognizer.recognize_google(audio).lower()
            logger.debug(f"Heard: {text}")
            
            # Check for wake word
            if self.wake_word in text:
                logger.info(f"Wake word '{self.wake_word}' detected!")
                self.speak("Yes? How can I help you?")
                return True
                
        except sr.WaitTimeoutError:
            pass  # No speech detected, continue listening
        except sr.UnknownValueError:
            pass  # Speech was unintelligible
        except Exception as e:
            logger.error(f"Error in wake word detection: {e}")
            
        return False
    
    def listen_for_command(self, timeout: float = 5.0) -> Optional[str]:
        """Listen for a voice command after wake word is detected.
        
        Args:
            timeout: Maximum time to listen for a command (in seconds).
            
        Returns:
            str: The recognized command text, or None if no command was recognized.
        """
        if not self.microphone:
            return None
            
        try:
            self.speak("I'm listening...")
            
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout,
                    phrase_time_limit=10.0  # Max 10 seconds per phrase
                )
                
            # Recognize speech using Google's speech recognition
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Command recognized: {text}")
            return text
            
        except sr.WaitTimeoutError:
            logger.debug("No command detected after wake word.")
            self.speak("I didn't catch that. Please try again.")
        except sr.UnknownValueError:
            logger.debug("Speech was unintelligible.")
            self.speak("I'm sorry, I didn't understand that.")
        except Exception as e:
            logger.error(f"Error in command recognition: {e}")
            self.speak("I encountered an error processing your request.")
            
        return None
    
    def speak(self, text: str, wait: bool = True):
        """Convert text to speech and speak it.
        
        Args:
            text: The text to speak.
            wait: If True, blocks until speech is complete.
        """
        if not self.tts_engine:
            logger.error("TTS engine not initialized.")
            return
            
        try:
            logger.debug(f"Speaking: {text}")
            self.tts_engine.say(text)
            if wait:
                self.tts_engine.runAndWait()
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up voice engine...")
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except:
                pass
        self.is_listening = False
    
    def __del__(self):
        """Destructor to ensure resources are cleaned up."""
        self.cleanup()

# For backward compatibility
class VoiceRecognitionEngine(VoiceEngine):
    """Legacy class name for backward compatibility."""
    pass
