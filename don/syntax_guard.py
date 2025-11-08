"""
Syntax Guard - Automatic syntax error detection and repair system.
Monitors and fixes Python files in real-time to prevent runtime errors.
"""
import ast
import os
import sys
import logging
import importlib
import traceback
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import inspect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/syntax_guard.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('syntax_guard')

@dataclass
class SyntaxIssue:
    """Represents a syntax or import issue found in code."""
    file_path: str
    line: int
    col: int
    error_type: str
    message: str
    fix_applied: bool = False
    fix_description: str = ""

class CodeFixer:
    """Handles automatic fixing of common code issues."""
    
    @staticmethod
    def fix_invalid_assignment(line: str) -> Optional[str]:
        """Fix invalid assignments like 'raise x = None'."""
        if 'raise' in line and '=' in line:
            # Example: 'raise self.x = None' -> 'self.x = None; raise ValueError(...)'
            var_part = line.split('raise')[-1].split('=')[0].strip()
            return f"{var_part} = None\n    raise RuntimeError(f\"Failed to initialize {var_part}\")"
        return None
    
    @staticmethod
    def fix_unterminated_string(content: str, line_num: int) -> Optional[str]:
        """Attempt to fix unterminated strings by adding missing quotes."""
        lines = content.splitlines()
        if line_num > len(lines):
            return None
            
        line = lines[line_num - 1]
        if '"' in line and line.count('"') % 2 != 0:
            return line + '"'
        elif '\'' in line and line.count("'") % 2 != 0:
            return line + "'"
        return None
    
    @classmethod
    def fix_import_error(cls, error: ImportError, file_path: str) -> Optional[str]:
        """Attempt to fix import errors by adding missing imports."""
        # This is a simplified version - in practice, you'd want to map common imports
        # or use more sophisticated analysis
        error_msg = str(error)
        if "No module named" in error_msg:
            module_name = error_msg.split("'")[1]
            # Add common import fixes here
            fixes = {
                'dotenv': 'from dotenv import load_dotenv',
                'pyaudio': 'import pyaudio',
                'speech_recognition': 'import speech_recognition as sr',
            }
            if module_name in fixes:
                return fixes[module_name]
        return None

class SyntaxGuard:
    """Main class for syntax checking and auto-fixing."""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or os.getcwd()
        self.issues: List[SyntaxIssue] = []
        self.watched_files: Set[str] = set()
        self.observer = None
        self.running = False
        self._ensure_logs_dir()
    
    def _ensure_logs_dir(self) -> None:
        """Ensure logs directory exists."""
        logs_dir = os.path.join(self.project_root, 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir, exist_ok=True)
    
    def scan_file(self, file_path: str) -> List[SyntaxIssue]:
        """Scan a single file for syntax issues."""
        issues = []
        
        # Check file exists and is Python file
        if not os.path.exists(file_path) or not file_path.endswith('.py'):
            return issues
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            logger.warning(f"Could not read file (not UTF-8): {file_path}")
            return issues
        
        # Check syntax with ast
        try:
            ast.parse(content)
            return issues  # No syntax errors found
        except SyntaxError as e:
            issue = SyntaxIssue(
                file_path=file_path,
                line=e.lineno or 0,
                col=e.offset or 0,
                error_type="SyntaxError",
                message=str(e),
                fix_applied=False
            )
            
            # Try to fix common issues
            fixed = False
            
            # Check for unterminated string
            if 'unterminated string literal' in str(e):
                fixed_line = CodeFixer.fix_unterminated_string(content, e.lineno or 0)
                if fixed_line:
                    issue.fix_applied = self._apply_fix(file_path, e.lineno or 0, fixed_line)
                    issue.fix_description = "Fixed unterminated string"
                    fixed = True
            
            # Check for invalid assignment
            elif 'raise' in str(e) and '=' in str(e):
                lines = content.splitlines()
                if e.lineno and e.lineno <= len(lines):
                    line = lines[e.lineno - 1]
                    fixed_line = CodeFixer.fix_invalid_assignment(line)
                    if fixed_line:
                        issue.fix_applied = self._apply_fix(file_path, e.lineno, fixed_line)
                        issue.fix_description = "Fixed invalid raise assignment"
                        fixed = True
            
            if not fixed:
                logger.warning(f"Could not auto-fix syntax error in {file_path}: {e}")
            
            issues.append(issue)
            return issues
        except Exception as e:
            logger.error(f"Error scanning {file_path}: {e}")
            return issues
    
    def _apply_fix(self, file_path: str, line_num: int, new_line: str) -> bool:
        """Apply a fix to a specific line in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if 0 < line_num <= len(lines):
                lines[line_num - 1] = new_line + '\n'
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                logger.info(f"Applied fix to {file_path}:{line_num}")
                return True
        except Exception as e:
            logger.error(f"Failed to apply fix to {file_path}:{line_num} - {e}")
        return False
    
    def scan_project(self) -> List[SyntaxIssue]:
        """Scan all Python files in the project."""
        self.issues = []
        
        for root, _, files in os.walk(self.project_root):
            # Skip virtual environments and other non-source directories
            if any(skip in root for skip in ('venv', '.git', '__pycache__', 'build', 'dist')):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self.issues.extend(self.scan_file(file_path))
        
        return self.issues
    
    def check_imports(self) -> List[SyntaxIssue]:
        """Check for import errors in all Python files."""
        issues = []
        
        # Add project root to Python path for relative imports
        sys.path.insert(0, self.project_root)
        
        for root, _, files in os.walk(self.project_root):
            if any(skip in root for skip in ('venv', '.git', '__pycache__', 'build', 'dist')):
                continue
                
            for file in files:
                if not file.endswith('.py') or file == '__init__.py':
                    continue
                    
                module_path = os.path.join(root, file)
                module_name = os.path.splitext(module_path)[0].replace(os.path.sep, '.')
                
                try:
                    # Try to import the module
                    importlib.import_module(module_name)
                except ImportError as e:
                    # Try to fix common import errors
                    fix = CodeFixer.fix_import_error(e, module_path)
                    
                    issue = SyntaxIssue(
                        file_path=module_path,
                        line=0,
                        col=0,
                        error_type="ImportError",
                        message=str(e),
                        fix_applied=fix is not None,
                        fix_description=f"Added missing import: {fix}" if fix else ""
                    )
                    
                    if fix:
                        try:
                            with open(module_path, 'r+', encoding='utf-8') as f:
                                content = f.read()
                                f.seek(0, 0)
                                f.write(f"{fix}\n\n{content}")
                            logger.info(f"Added import to {module_path}: {fix}")
                        except Exception as fix_error:
                            logger.error(f"Failed to add import to {module_path}: {fix_error}")
                            issue.fix_applied = False
                    
                    issues.append(issue)
        
        return issues
    
    def start_watching(self) -> None:
        """Start watching Python files for changes."""
        if self.running:
            return
            
        class PythonFileHandler(FileSystemEventHandler):
            def __init__(self, callback):
                self.callback = callback
            
            def on_modified(self, event):
                if event.src_path.endswith('.py'):
                    self.callback(event.src_path)
        
        self.observer = Observer()
        self.observer.schedule(
            PythonFileHandler(self._on_file_changed),
            self.project_root,
            recursive=True
        )
        self.running = True
        self.observer.start()
        logger.info("Started watching Python files for changes")
        
        # Run initial scan
        self.scan_project()
    
    def stop_watching(self) -> None:
        """Stop watching for file changes."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.running = False
            logger.info("Stopped watching Python files")
    
    def _on_file_changed(self, file_path: str) -> None:
        """Handle file change events."""
        logger.debug(f"File changed: {file_path}")
        issues = self.scan_file(file_path)
        
        for issue in issues:
            if issue.fix_applied:
                logger.info(f"Auto-fixed issue in {file_path}: {issue.message}")
            else:
                logger.warning(f"Found unfixable issue in {file_path}: {issue.message}")
    
    def run_precheck(self) -> bool:
        """Run all checks and return True if no critical issues found."""
        logger.info("Running pre-execution syntax and import checks...")
        
        # Scan for syntax errors
        syntax_issues = self.scan_project()
        
        # Check for import errors
        import_issues = self.check_imports()
        
        all_issues = syntax_issues + import_issues
        
        # Log summary
        fixed_issues = [i for i in all_issues if i.fix_applied]
        unfixed_issues = [i for i in all_issues if not i.fix_applied]
        
        logger.info(f"Pre-check complete. Fixed: {len(fixed_issues)}, Unfixed: {len(unfixed_issues)}")
        
        for issue in unfixed_issues:
            logger.warning(f"Unfixed {issue.error_type} in {issue.file_path}:{issue.line} - {issue.message}")
        
        # Start watching for changes
        self.start_watching()
        
        # Return True if there are no unfixed critical issues
        return len(unfixed_issues) == 0

def run_safe_mode():
    """Run the application in safe mode with minimal functionality."""
    logger.warning("Running in SAFE MODE due to critical errors")
    # Implement minimal safe mode functionality here
    print("\n⚠️  Running in SAFE MODE due to critical errors")
    print("Some features may be unavailable. Check logs for details.\n")

def main():
    """Main entry point for the syntax guard."""
    guard = SyntaxGuard()
    
    try:
        if not guard.run_precheck():
            logger.warning("Critical issues found during pre-check")
            run_safe_mode()
    except Exception as e:
        logger.error(f"Error during syntax check: {e}")
        run_safe_mode()
    
    return guard

if __name__ == "__main__":
    guard = main()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        guard.stop_watching()
        print("\nStopped syntax guard.")
