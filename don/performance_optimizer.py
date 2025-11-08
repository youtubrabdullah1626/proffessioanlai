"""
Performance Optimizer Module

This module provides functionality to optimize runtime performance,
handle fallbacks, and ensure smooth operation of the AI assistant.
"""

import os
import sys
import time
import logging
import threading
import importlib
import subprocess
from typing import Dict, Any, Callable, Optional, List, Set
from dataclasses import dataclass, field
from pathlib import Path

# Import after path setup
from .logging_utils import setup_logging

logger = setup_logging()

@dataclass
class PerformanceMetrics:
    """Track performance metrics for optimization."""
    command_times: Dict[str, List[float]] = field(default_factory=dict)
    failed_commands: Dict[str, int] = field(default_factory=dict)
    module_load_times: Dict[str, float] = field(default_factory=dict)
    last_command_time: float = field(default_factory=time.time)
    command_aliases: Dict[str, str] = field(default_factory=dict)

class PerformanceOptimizer:
    """Handles performance optimization and fallback mechanisms."""
    
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self._init_command_aliases()
        self._background_tasks: List[threading.Thread] = []
        self._should_stop = threading.Event()
        self._module_cache: Dict[str, Any] = {}
        self._optimization_enabled = True
        
        # Start background monitor
        self._monitor_thread = threading.Thread(
            target=self._monitor_performance,
            daemon=True
        )
        self._monitor_thread.start()
    
    def _init_command_aliases(self) -> None:
        """Initialize common command aliases."""
        self.metrics.command_aliases = {
            # Browser commands
            'open chrome': 'open_browser chrome',
            'launch chrome': 'open_browser chrome',
            'start chrome': 'open_browser chrome',
            'open browser': 'open_browser',
            'launch browser': 'open_browser',
            
            # System commands
            'shutdown': 'system_shutdown',
            'restart': 'system_restart',
            'sleep': 'system_sleep',
            
            # Media controls
            'volume up': 'volume_increase',
            'volume down': 'volume_decrease',
            'mute': 'volume_mute',
            'unmute': 'volume_unmute',
        }
    
    def optimize_runtime_performance(self) -> None:
        """Apply all performance optimizations."""
        logger.info("Applying runtime optimizations...")
        
        # Preload commonly used modules in background
        self._run_in_background(self._preload_modules)
        
        # Optimize system settings
        self._optimize_system_settings()
        
        logger.info("Runtime optimizations applied")
    
    def _preload_modules(self) -> None:
        """Preload commonly used modules to reduce latency."""
        modules_to_preload = [
            'speech_recognition',
            'pyttsx3',
            'webbrowser',
            'os',
            'sys',
            'time',
            'threading',
            'subprocess',
            'queue'
        ]
        
        for module_name in modules_to_preload:
            try:
                start_time = time.time()
                module = importlib.import_module(module_name)
                self._module_cache[module_name] = module
                load_time = (time.time() - start_time) * 1000
                self.metrics.module_load_times[module_name] = load_time
                logger.debug(f"Preloaded {module_name} in {load_time:.2f}ms")
            except ImportError as e:
                logger.warning(f"Failed to preload {module_name}: {e}")
    
    def _optimize_system_settings(self) -> None:
        """Optimize system-level settings for better performance."""
        try:
            # Increase thread pool size
            import concurrent.futures
            import multiprocessing
            
            # Set thread pool size based on CPU cores
            num_cores = multiprocessing.cpu_count()
            optimal_threads = max(4, num_cores * 2)
            
            # Set for concurrent futures
            concurrent.futures.ThreadPoolExecutor_original = concurrent.futures.ThreadPoolExecutor
            def patched_thread_pool_executor(max_workers=None, *args, **kwargs):
                if max_workers is None:
                    max_workers = optimal_threads
                return concurrent.futures.ThreadPoolExecutor_original(
                    max_workers, *args, **kwargs
                )
            concurrent.futures.ThreadPoolExecutor = patched_thread_pool_executor
            
            logger.info(f"Optimized thread pool size: {optimal_threads} threads")
            
        except Exception as e:
            logger.warning(f"Could not optimize system settings: {e}")
    
    def _run_in_background(self, func: Callable, *args, **kwargs) -> None:
        """Run a function in a background thread."""
        def wrapper():
            try:
                func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Background task failed: {e}", exc_info=True)
        
        thread = threading.Thread(target=wrapper, daemon=True)
        self._background_tasks.append(thread)
        thread.start()
    
    def _monitor_performance(self) -> None:
        """Monitor system performance and apply optimizations."""
        while not self._should_stop.is_set():
            try:
                # Clean up finished background tasks
                self._background_tasks = [t for t in self._background_tasks if t.is_alive()]
                
                # Log performance metrics periodically
                if logger.isEnabledFor(logging.DEBUG):
                    self._log_performance_metrics()
                
            except Exception as e:
                logger.error(f"Error in performance monitor: {e}")
            
            time.sleep(10)  # Check every 10 seconds
    
    def _log_performance_metrics(self) -> None:
        """Log current performance metrics."""
        if not self.metrics.command_times:
            return
            
        logger.debug("\n=== Performance Metrics ===")
        
        # Command execution times
        for cmd, times in self.metrics.command_times.items():
            if times:
                avg_time = sum(times) / len(times)
                logger.debug(f"{cmd}: {avg_time:.2f}s avg ({len(times)} samples)")
        
        # Module load times
        if self.metrics.module_load_times:
            logger.debug("\nModule load times (ms):")
            for mod, load_time in self.metrics.module_load_times.items():
                logger.debug(f"  {mod}: {load_time:.2f}")
        
        logger.debug("=========================\n")
    
    def normalize_command(self, command: str) -> str:
        """Normalize and resolve command aliases."""
        if not command:
            return ""
            
        # Convert to lowercase and strip whitespace
        normalized = command.lower().strip()
        
        # Check for exact match in aliases
        if normalized in self.metrics.command_aliases:
            return self.metrics.command_aliases[normalized]
        
        # Check for partial matches
        for alias, resolved in self.metrics.command_aliases.items():
            if alias in normalized:
                return resolved
                
        return normalized
    
    def track_command(self, command: str, execution_time: float) -> None:
        """Track command execution time for performance analysis."""
        if command not in self.metrics.command_times:
            self.metrics.command_times[command] = []
        self.metrics.command_times[command].append(execution_time)
        self.metrics.last_command_time = time.time()
        
        # Keep only last 100 samples per command
        if len(self.metrics.command_times[command]) > 100:
            self.metrics.command_times[command] = self.metrics.command_times[command][-100:]
    
    def handle_command_failure(self, command: str, error: Exception) -> None:
        """Handle command failures and implement retry logic."""
        if command not in self.metrics.failed_commands:
            self.metrics.failed_commands[command] = 0
        self.metrics.failed_commands[command] += 1
        
        error_msg = str(error).lower()
        
        # Check for missing module error
        if "no module named" in error_msg:
            module_name = error_msg.split("'")[1]
            logger.warning(f"Missing module detected: {module_name}")
            self._install_missing_module(module_name)
        
        # Log the failure
        logger.error(f"Command failed: {command} - {error}", exc_info=True)
        
        # If this command failed multiple times, log it for review
        if self.metrics.failed_commands[command] >= 2:
            logger.warning(f"Command failed multiple times: {command}")
    
    def _install_missing_module(self, module_name: str) -> bool:
        """Attempt to install a missing Python module."""
        try:
            logger.info(f"Attempting to install missing module: {module_name}")
            
            # Map common module names to their PyPI package names
            package_map = {
                'cv2': 'opencv-python',
                'PIL': 'Pillow',
                'yaml': 'PyYAML',
                'dateutil': 'python-dateutil',
                'serial': 'pyserial'
            }
            
            # Get the package name (use mapping if available, otherwise use module name)
            package_name = package_map.get(module_name, module_name)
            
            # Try to install the package
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                '--disable-pip-version-check',
                '--no-warn-script-location',
                package_name
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            logger.info(f"Successfully installed {package_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install {module_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error installing {module_name}: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up resources and stop background tasks."""
        self._should_stop.set()
        
        # Wait for monitor thread to finish
        if self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        
        # Wait for background tasks to finish (with timeout)
        for task in self._background_tasks:
            if task.is_alive():
                task.join(timeout=1.0)


def validate_project_integrity() -> bool:
    """
    Validate the project's integrity by checking for common issues.
    
    This is a simplified version that's optimized for performance.
    The full implementation is in project_validator.py
    """
    try:
        # Check for required modules
        required_modules = [
            'speech_recognition',
            'pyttsx3',
            'colorama',
            'pyaudio',
            'psutil'
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                importlib.import_module(module)
            except ImportError:
                missing_modules.append(module)
        
        # Install missing modules
        if missing_modules:
            logger.warning(f"Missing modules: {', '.join(missing_modules)}")
            for module in missing_modules:
                PerformanceOptimizer()._install_missing_module(module)
        
        return True
        
    except Exception as e:
        logger.error(f"Project validation failed: {e}")
        return False


def optimize_runtime_performance() -> PerformanceOptimizer:
    """
    Initialize and return a PerformanceOptimizer instance.
    This is the main entry point for performance optimizations.
    """
    # First validate project integrity
    if not validate_project_integrity():
        logger.warning("Project validation found issues, some optimizations may not work")
    
    # Create and initialize the optimizer
    optimizer = PerformanceOptimizer()
    optimizer.optimize_runtime_performance()
    
    # Register cleanup on exit
    import atexit
    atexit.register(optimizer.cleanup)
    
    return optimizer


if __name__ == "__main__":
    # Test the optimizer
    opt = optimize_runtime_performance()
    print("Performance optimizer initialized. Press Ctrl+C to exit.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        opt.cleanup()
        print("\nPerformance optimizer stopped.")
