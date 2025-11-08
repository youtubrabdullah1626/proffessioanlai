from typing import Optional, Callable, Dict, Any, List
import os
import time
import threading
import queue
import traceback
from dataclasses import dataclass, field
from enum import Enum, auto

import speech_recognition as sr

from .logging_utils import setup_logging
from .tts import init_tts, speak_mixed
from .config import Settings, load_settings
from .performance_optimizer import PerformanceOptimizer

logger = setup_logging()

class ListeningState(Enum):
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    ERROR = auto()

@dataclass
class CommandResult:
    success: bool
    message: str
    data: Dict[str, Any] = None

class STTEngine:
    """Enhanced Speech-to-text with better error handling and continuous listening."""
    def __init__(self, energy_threshold: int = 300, pause_threshold: float = 0.5, 
                 dynamic_energy_threshold: bool = True) -> None:
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.pause_threshold = pause_threshold  # Reduced for faster response
        self.recognizer.dynamic_energy_threshold = dynamic_energy_threshold
        self.microphone = None
        self.is_listening = False
        self.last_heard = 0
        self._stop_listening = None
        self._audio_queue = queue.Queue()
        self._processing_thread = None
        self._init_microphone()
        self._optimizer = PerformanceOptimizer()

    def _init_microphone(self) -> None:
        """Initialize microphone with error handling."""
        try:
            if self.microphone is None:
                self.microphone = sr.Microphone()
                logger.info("Microphone initialized successfully")
                # Quick calibration in background
                self._background_calibrate()
        except Exception as e:
            logger.error(f"Failed to initialize microphone: {e}")
            self.microphone = None
            raise RuntimeError(f"Microphone initialization failed: {e}")

    def calibrate_microphone(self, duration: float = 0.5) -> bool:
        """Calibrate for ambient noise with shorter default duration."""
        if not self.microphone:
            self._init_microphone()
        with self.microphone as source:
            logger.info("Calibrating for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=duration)
            logger.info(f"Energy threshold set to {self.recognizer.energy_threshold}")
        return True

    def _background_calibrate(self, duration: float = 0.5) -> None:
        """Calibrate microphone in background with shorter duration."""
        def calibrate():
            try:
                if self.microphone:
                    with self.microphone as source:
                        logger.debug("Calibrating for ambient noise (background)...")
                        self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                        logger.info(f"Energy threshold set to {self.recognizer.energy_threshold}")
            except Exception as e:
                logger.warning(f"Background calibration failed: {e}")
        
        # Run in a separate thread to avoid blocking
        threading.Thread(target=calibrate, daemon=True).start()

    def _process_audio_queue(self, callback: Callable[[str], None]) -> None:
        """Process audio from the queue in a separate thread."""
        while self.is_listening or not self._audio_queue.empty():
            try:
                audio = self._audio_queue.get(timeout=1.0)
                if audio is None:  # Sentinel value
                    continue
                    
                try:
                    start_time = time.time()
                    text = self.recognizer.recognize_google(audio)
                    process_time = time.time() - start_time
                    
                    if text:
                        self.last_heard = time.time()
                        logger.info(f"Recognized in {process_time:.2f}s: {text}")
                        self._optimizer.track_command("speech_recognition", process_time)
                        callback(text)
                except sr.UnknownValueError:
                    logger.debug("Could not understand audio")
                    callback("")
                except sr.RequestError as e:
                    logger.error(f"Could not request results; {e}")
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in audio processor: {e}")
                time.sleep(0.1)

    def listen_continuous(self, callback: Callable[[str], None], 
                                 timeout: float = 3.0, 
                                 phrase_time_limit: float = 10.0) -> None:
        """Continuously listen for speech and call callback with recognized text."""
        if self.is_listening:
            logger.warning("Already listening")
            return
            
        self.is_listening = True
        
        # Start audio processing thread
        self._processing_thread = threading.Thread(
            target=self._process_audio_queue,
            args=(callback,),
            daemon=True
        )
        self._processing_thread.start()
        
        def listen_loop():
            while self.is_listening:
                try:
                    with self.microphone as source:
                        logger.debug("Listening...")
                        try:
                            audio = self.recognizer.listen(
                                source, 
                                timeout=timeout,
                                phrase_time_limit=phrase_time_limit
                            )
                            self._audio_queue.put(audio)
                        except sr.WaitTimeoutError:
                            continue
                            

                except Exception as e:
                    logger.error(f"Error in listen_loop: {e}")
                    time.sleep(0.1)
        
        # Start listening in a separate thread
        self._listen_thread = threading.Thread(target=listen_loop, daemon=True)
        self._listen_thread.start()
        logger.info("Started continuous listening")

    def stop_listening(self) -> None:
        """Stop the continuous listening loop."""
        self.is_listening = False
        
        # Signal audio processor to exit
        self._audio_queue.put(None)
        
        # Wait for threads to finish
        if hasattr(self, '_listen_thread') and self._listen_thread.is_alive():
            self._listen_thread.join(timeout=1.0)
        if hasattr(self, '_processing_thread') and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=1.0)
            
        # Clear the queue
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break
        logger.info("Stopped continuous listening")

    def listen_once(self, timeout: float = 5.0, phrase_time_limit: float = 8.0) -> Optional[str]:
        """Listen for a single utterance with fallback to Google STT."""
        if self.microphone is None and not self._init_microphone():
            logger.error("No microphone available")
            return None
            
        try:
            with self.microphone as source:
                logger.debug("Listening for a single command...")
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
                
            try:
                text = self.recognizer.recognize_google(audio)
                logger.info(f"Recognized: {text}")
                return text
            except sr.UnknownValueError:
                logger.warning("Could not understand audio")
            except sr.RequestError as e:
                logger.error(f"Could not request results from Google Speech Recognition service; {e}")
                
        except Exception as e:
            logger.error(f"Error in listen_once: {e}")
            
        return None

class GeminiClient:
    """Placeholder Gemini client for intent parsing/reasoning."""
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def analyze_intent(self, text: str) -> Dict[str, Any]:
        """Analyze the intent of the given text."""
        try:
            logger.debug(f"Analyzing intent for: {text}")
            # This is a placeholder - in a real implementation, this would call the Gemini API
            return {"intent": "default", "confidence": 1.0, "entities": {}}
        except Exception as e:
            logger.error(f"Error in analyze_intent: {e}")
            return {"intent": "error", "confidence": 0.0, "entities": {}}

class CommsAI:
    """Main class for handling communication with the AI assistant."""
    
    def __init__(self, settings: Optional[Settings] = None) -> None:
        # Initialize performance optimizer first
        self._optimizer = PerformanceOptimizer()
        
        # Load settings and initialize components
        self.settings = settings or load_settings()
        self.tts = init_tts(self.settings.tts)
        self.stt = STTEngine()
        self.gemini = GeminiClient()
        
        # Thread control
        self._stop_flag = threading.Event()
        self._listen_thread: Optional[threading.Thread] = None
        self._command_queue = queue.Queue()
        self._state = ListeningState.IDLE
        self._command_history: List[Dict[str, Any]] = []
        
        # Performance metrics
        self.metrics = {
            'commands_processed': 0,
            'last_command_time': 0,
            'errors': 0,
            'last_error': None,
            'response_times': []
        }
        
        # Initialize with quick calibration in background
        self.stt.calibrate_microphone(duration=0.5)
        
        # Preload commonly used commands
        self._preload_commands()

    @property
    def state(self) -> ListeningState:
        """Get the current listening state."""
        return self._state

    def _set_state(self, new_state: ListeningState) -> None:
        """Safely update the state with logging."""
        old_state = self._state
        self._state = new_state
        logger.debug(f"State changed: {old_state.name} -> {new_state.name}")

    def _preload_commands(self) -> None:
        """Preload commonly used commands for faster execution."""
        common_commands = [
            "what time is it",
            "what's the weather",
            "open browser",
            "close browser",
            "stop listening"
        ]
        
        # This is just to warm up the recognizer
        for cmd in common_commands:
            self._optimizer.normalize_command(cmd)
    
    def _process_command(self, text: str) -> CommandResult:
        """Process a single command with performance tracking."""
        if not text:
            return CommandResult(False, "No command provided")
            
        start_time = time.time()
        self._set_state(ListeningState.PROCESSING)
        logger.info(f"Processing command: {text}")
        
        try:
            # Normalize and resolve command aliases
            normalized_cmd = self._optimizer.normalize_command(text)
            
            # Add command to history
            self.metrics['commands_processed'] += 1
            self.metrics['last_command_time'] = start_time
            
            # Track command in history
            self._command_history.append({
                'command': text,
                'normalized': normalized_cmd,
                'timestamp': start_time
            })
            
            # Process command here (placeholder)
            # In a real implementation, this would call the appropriate handler
            logger.info(f"Executing command: {normalized_cmd}")
            
            # Simulate command execution with variable time based on command length
            process_time = min(0.1 + (len(text) * 0.001), 0.5)  # Max 500ms
            time.sleep(process_time)
            
            # Track performance
            exec_time = time.time() - start_time
            self.metrics['response_times'].append(exec_time)
            self._optimizer.track_command(normalized_cmd, exec_time)
            
            # Keep only last 100 response times
            if len(self.metrics['response_times']) > 100:
                self.metrics['response_times'] = self.metrics['response_times'][-100:]
            
            return CommandResult(True, f"Executed: {normalized_cmd}")
            
        except Exception as e:
            self.metrics['errors'] += 1
            self.metrics['last_error'] = str(e)
            self._optimizer.handle_command_failure(text, e)
            logger.error(f"Error processing command: {e}", exc_info=True)
            return CommandResult(False, f"Error: {str(e)}")
        finally:
            self._set_state(ListeningState.IDLE)

    def start_background_listening(self, loop_delay: float = 0.1) -> None:
        """Start listening for voice commands in the background with optimized settings."""
        if self._listen_thread and self._listen_thread.is_alive():
            logger.warning("Already listening in background")
            return
            
        self._stop_flag.clear()
        
        def listen_loop():
            # Use a faster loop with smaller sleep for more responsive listening
            while not self._stop_flag.is_set():
                try:
                    # Only process if we're not already processing
                    if self._state != ListeningState.PROCESSING:
                        self.listen_and_respond()
                    time.sleep(loop_delay)
                except Exception as e:
                    logger.error(f"Error in listen_loop: {e}")
                    # Exponential backoff on error
                    time.sleep(min(2 ** self.metrics['errors'], 5))  # Max 5s delay
        
        # Start the listening thread with a higher priority
        self._listen_thread = threading.Thread(
            target=listen_loop, 
            daemon=True,
            name="BackgroundListener"
        )
        self._listen_thread.start()
        logger.info("Started optimized background listening")

    def stop_background_listening(self) -> None:
        """Stop the background listening thread and clean up resources."""
        self._stop_flag.set()
        
        # Stop STT engine
        if hasattr(self, 'stt'):
            self.stt.stop_listening()
        
        # Wait for listening thread to finish
        if hasattr(self, '_listen_thread') and self._listen_thread.is_alive():
            self._listen_thread.join(timeout=1.0)
            
        # Clean up optimizer
        if hasattr(self, '_optimizer'):
            self._optimizer.cleanup()
            
        logger.info("Stopped background listening and cleaned up resources")

    def listen_and_respond(self) -> None:
        """Listen for a single command and respond (blocking)."""
        if self._state == ListeningState.PROCESSING:
            logger.warning("Already processing a command")
            return
            
        self._set_state(ListeningState.LISTENING)
        
        try:
            # Listen for a single command
            text = self.stt.listen_once()
            
            if not text:
                speak_mixed(self.tts, "I didn't catch that. Could you please repeat?")
                return
                
            # Process the command
            result = self._process_command(text)
            
            # Provide feedback
            if result.success:
                speak_mixed(self.tts, result.message or "Done!")
            else:
                speak_mixed(self.tts, f"Sorry, I couldn't complete that. {result.message}")
                
        except Exception as e:
            logger.error(f"Error in listen_and_respond: {e}", exc_info=True)
            speak_mixed(self.tts, "I encountered an error. Please try again.")
        finally:
            self._set_state(ListeningState.IDLE)

    def __del__(self) -> None:
        """Ensure resources are cleaned up."""
        self.stop_background_listening()

    def stop_background_listening(self) -> None:
        """Stop the background listening thread and clean up resources."""
        self._stop_flag.set()
        
        # Stop STT engine
        if hasattr(self, 'stt'):
            self.stt.stop_listening()
        
        # Wait for listening thread to finish
        if hasattr(self, '_listen_thread') and self._listen_thread.is_alive():
            self._listen_thread.join(timeout=1.0)
            
        # Clean up optimizer
        if hasattr(self, '_optimizer'):
            self._optimizer.cleanup()
            
        logger.info("Stopped background listening and cleaned up resources")
