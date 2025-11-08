"""
Error Guard - Advanced error detection and self-healing system.

This module provides intelligent error handling, automatic fixes for common issues,
and ensures system stability with minimal user intervention.
"""
import os
import sys
import importlib
import subprocess
import logging
import traceback
import inspect
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Set, Callable

# Configure logging
def setup_logging():
    """Configure logging for the error guard."""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger('error_guard')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler
    file_handler = logging.FileHandler(log_dir / 'error_guard.log')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

class ErrorGuard:
    """Advanced error detection and self-healing system."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_file = self.project_root / '.error_guard_config.json'
        self.issue_history: Dict[str, int] = self._load_issue_history()
        self.fixed_issues: List[str] = []
        
        # Core packages required for basic functionality
        self.required_packages = [
            'python-dotenv>=1.0.0',
            'colorama>=0.4.6',
            'watchdog>=2.1.6',
            'pyaudio>=0.2.13',
            'SpeechRecognition>=3.10.0',
            'pyttsx3>=2.90',
            'psutil>=5.9.0',
            'comtypes>=1.1.7',
            'pywin32>=300;platform_system=="Windows"'
        ]
        
        # Known issues and their fixes
        self.known_issues = {
            'import_error': self._fix_import_error,
            'missing_package': self._install_missing_package,
            'syntax_error': self._fix_syntax_error,
            'file_not_found': self._handle_missing_file
        }
        
    def _load_issue_history(self) -> Dict[str, int]:
        """Load issue history from config file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load issue history: {e}")
        return {}
        
    def _save_issue_history(self) -> None:
        """Save current issue history to config file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.issue_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save issue history: {e}")
            
    def track_issue(self, issue_type: str) -> None:
        """Track occurrence of an issue type."""
        self.issue_history[issue_type] = self.issue_history.get(issue_type, 0) + 1
        self._save_issue_history()
        
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        dirs = [
            self.project_root / 'logs',
            self.project_root / 'data',
            self.project_root / 'cache'
        ]
        for directory in dirs:
            try:
                directory.mkdir(exist_ok=True, parents=True)
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {e}")
    
    def _install_missing_package(self, package: str) -> bool:
        """Install a missing Python package."""
        try:
            logger.info(f"Attempting to install missing package: {package}")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully installed {package}")
                self.fixed_issues.append(f"Installed package: {package}")
                return True
            else:
                error_msg = result.stderr or result.stdout
                logger.error(f"Failed to install {package}: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"Error installing {package}: {e}")
            return False
            
    def _fix_import_error(self, error: ImportError) -> bool:
        """Attempt to fix import errors by installing missing packages."""
        error_msg = str(error).lower()
        
        # Extract package name from common error messages
        if "no module named" in error_msg:
            module_name = error_msg.split("'")[1]
            # Map common import names to package names
            package_map = {
                'pyaudio': 'PyAudio',
                'speech_recognition': 'SpeechRecognition',
                'dotenv': 'python-dotenv',
                'win32api': 'pywin32',
                'win32com': 'pywin32',
                'win32gui': 'pywin32'
            }
            package = package_map.get(module_name, module_name)
            return self._install_missing_package(package)
            
        return False
        
    def _fix_syntax_error(self, error: SyntaxError) -> bool:
        """Attempt to fix common syntax errors."""
        try:
            file_path = Path(error.filename).resolve()
            if not file_path.exists():
                return False
                
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Fix common issues
            fixed = False
            for i, line in enumerate(lines):
                # Fix unterminated strings
                if '"""' in line and line.count('"""') % 2 != 0:
                    lines[i] = line.replace('"""', '""""')
                    fixed = True
                # Fix missing colons
                elif line.strip().endswith(')'):
                    lines[i] = line.rstrip() + ':\n'
            if fixed:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                logger.info(f"Fixed syntax error in {file_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error fixing syntax: {e}")
            
        return False
        
    def _handle_missing_file(self, error: FileNotFoundError) -> bool:
        """Handle missing file errors by creating necessary directories."""
        try:
            file_path = Path(error.filename).resolve()
            if not file_path.parent.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {file_path.parent}")
                return True
        except Exception as e:
            logger.error(f"Error handling missing file: {e}")
        return False
    
    def check_imports(self) -> bool:
        """Check and fix import errors."""
        success = True
        
        # Check for missing packages
        for package in self.required_packages:
            try:
                importlib.import_module(package.split('.')[0])
            except ImportError:
                logger.warning(f"Missing package: {package}")
                success = success and self.install_package(package)
        
        # Ensure logging is properly set up
        try:
            from don.logging_utils import setup_logging
            setup_logging()
        except ImportError as e:
            logger.error(f"Failed to set up logging: {e}")
            success = False
        
        return success
    
    def fix_syntax_errors(self) -> bool:
        """Fix common syntax errors in the codebase."""
        success = True
        
        # Fix comms_ai.py
        comms_ai_path = self.project_root / 'don' / 'comms_ai.py'
        if comms_ai_path.exists():
            try:
                with open(comms_ai_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Fix the raise statement
                if 'raise self.microphone = None' in content:
                    fixed_content = content.replace(
                        'raise self.microphone = None',
                        'self.microphone = None\n            raise RuntimeError("Microphone initialization failed.")'
                    )
                    
                    if fixed_content != content:
                        with open(comms_ai_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                        logger.info("Fixed invalid raise statement in comms_ai.py")
                        self.fixed_issues.append("Fixed invalid raise statement in comms_ai.py")
            except Exception as e:
                logger.error(f"Failed to fix comms_ai.py: {e}")
                success = False
        
        # Fix performance_optimizer.py
        perf_opt_path = self.project_root / 'don' / 'performance_optimizer.py'
        if perf_opt_path.exists():
            try:
                with open(perf_opt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Fix unterminated string in docstring
                if 'Validate the project\'s integrity' in content:
                    # The issue might be in the docstring - we'll ensure it's properly closed
                    fixed_content = content.replace(
                        '"""\n    Validate the project\'s integrity',
                        '"""\n    Validate the project\'s integrity'
                    )
                    
                    if fixed_content != content:
                        with open(perf_opt_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                        logger.info("Fixed docstring in performance_optimizer.py")
                        self.fixed_issues.append("Fixed docstring in performance_optimizer.py")
            except Exception as e:
                logger.error(f"Failed to fix performance_optimizer.py: {e}")
                success = False
        
        return success
    
    def run_checks(self) -> bool:
        """Run all error checks and fixes."""
        self.ensure_logs_dir()
        
        logger.info("Starting error checks...")
        
        # Run all checks
        checks = [
            ("Dependency Checks", self.check_imports),
            ("Syntax Fixes", self.fix_syntax_errors)
        ]
        
        success = True
        for check_name, check_func in checks:
            logger.info(f"Running {check_name}...")


def auto_protect() -> bool:
    """
    Run comprehensive error protection and system checks.
    
    Returns:
        bool: True if system is healthy, False if critical issues were found
    """
    guard = ErrorGuard()
    guard.ensure_directories()
    
    # Track startup
    guard.track_issue('startup')
    
    # Check and install required packages
    for package_spec in guard.required_packages:
        # Handle package specs like 'package>=1.0.0'
        package = package_spec.split(';')[0].split('>')[0].split('<')[0].split('=')[0].strip()
        if not guard._install_missing_package(package_spec):
            logger.warning(f"Failed to install/verify package: {package}")
    
    # Run system health check
    health_check_passed = guard.check_system_health()
    
    if guard.fixed_issues:
        logger.info("Fixed the following issues:" + "\n- " + "\n- ".join(guard.fixed_issues))
    
    return health_check_passed


def handle_error(error: Exception) -> bool:
    """
    Handle an exception using the error guard.
    
    Args:
        error: The exception to handle
        
    Returns:
        bool: True if the error was handled, False otherwise
    """
    guard = ErrorGuard()
    error_type = type(error).__name__
    
    # Track the error
    guard.track_issue(f"error_{error_type}")
    
    # Try to fix the error based on its type
    if isinstance(error, ImportError):
        return guard._fix_import_error(error)
    elif isinstance(error, SyntaxError):
        return guard._fix_syntax_error(error)
    elif isinstance(error, FileNotFoundError):
        return guard._handle_missing_file(error)
    
    return False
    """Run error guard checks and fixes."""
    try:
        guard = ErrorGuard()
        if not guard.run_checks():
            logger.warning("Some issues were detected and fixed. Please restart the application.")
    except Exception as e:
        logger.error(f"Error in auto_protect: {e}")
        # Continue execution in safe mode
        pass


if __name__ == "__main__":
    auto_protect()
