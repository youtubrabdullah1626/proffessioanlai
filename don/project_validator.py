"""
Project Validator Module

This module provides functionality to validate and fix common Python project issues,
including import errors, indentation, missing dependencies, and code style.
"""

import os
import sys
import subprocess
import importlib
import inspect
import ast
import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set, Any
import pkg_resources

# Set up logging
logger = logging.getLogger(__name__)

class ProjectValidator:
    """Validates and fixes common Python project issues."""
    
    def __init__(self, project_root: str = None):
        """Initialize the validator with project root directory."""
        self.project_root = project_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.requirements_file = os.path.join(self.project_root, 'requirements.txt')
        self.python_files = self._find_python_files()
        self.installed_packages = self._get_installed_packages()
        self.required_packages = self._parse_requirements()
        self.import_errors: List[Dict[str, str]] = []
        self.syntax_errors: List[Dict[str, str]] = []
        self.indentation_issues: List[Dict[str, str]] = []
        self.style_issues: List[Dict[str, str]] = []
    
    def _find_python_files(self) -> List[str]:
        """Find all Python files in the project."""
        python_files = []
        for root, _, files in os.walk(self.project_root):
            # Skip virtual environment directories
            if any(part.startswith(('.', '_', 'venv', 'env')) for part in root.split(os.sep)):
                continue
                
            for file in files:
                if file.endswith('.py') and not file.startswith('.'):
                    python_files.append(os.path.join(root, file))
        return python_files
    
    def _get_installed_packages(self) -> Set[str]:
        """Get set of installed Python packages."""
        return {pkg.key for pkg in pkg_resources.working_set}
    
    def _parse_requirements(self) -> Set[str]:
        """Parse requirements.txt and return set of required packages."""
        if not os.path.exists(self.requirements_file):
            return set()
            
        with open(self.requirements_file, 'r', encoding='utf-8') as f:
            requirements = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Remove version specifiers
                    pkg = re.split(r'[<>=!]', line)[0].strip()
                    requirements.append(pkg.lower())
        return set(requirements)
    
    def check_imports(self) -> None:
        """Check for import errors in all Python files."""
        for file_path in self.python_files:
            try:
                # Try to import the module
                rel_path = os.path.relpath(file_path, self.project_root)
                module_name = rel_path.replace(os.path.sep, '.')[:-3]  # Remove .py
                if module_name.endswith('.__init__'):
                    module_name = module_name[:-9]  # Handle __init__.py
                
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
            except ImportError as e:
                self.import_errors.append({
                    'file': file_path,
                    'error': str(e),
                    'type': 'import_error'
                })
            except SyntaxError as e:
                self.syntax_errors.append({
                    'file': file_path,
                    'error': f"Syntax error: {e.msg} at line {e.lineno}",
                    'type': 'syntax_error'
                })
            except Exception as e:
                logger.warning(f"Unexpected error checking {file_path}: {e}")
    
    def check_indentation(self) -> None:
        """Check for inconsistent indentation in Python files."""
        for file_path in self.python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for i, line in enumerate(lines, 1):
                    if '\t' in line:
                        self.indentation_issues.append({
                            'file': file_path,
                            'line': i,
                            'issue': 'Tab character found, should use spaces',
                            'type': 'indentation'
                        })
                    
                    # Check for mixed indentation
                    if ' ' in line and '\t' in line.expandtabs():
                        self.indentation_issues.append({
                            'file': file_path,
                            'line': i,
                            'issue': 'Mixed tabs and spaces',
                            'type': 'indentation'
                        })
                        
            except Exception as e:
                logger.warning(f"Error checking indentation in {file_path}: {e}")
    
    def fix_indentation(self, file_path: str) -> bool:
        """Fix indentation in a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            fixed_lines = []
            for line in lines:
                # Replace tabs with 4 spaces
                fixed_line = line.expandtabs(4)
                fixed_lines.append(fixed_line)
            
            # Only write if changes were made
            if lines != fixed_lines:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(fixed_lines)
                return True
                
        except Exception as e:
            logger.error(f"Failed to fix indentation in {file_path}: {e}")
            return False
        return False
    
    def check_missing_dependencies(self) -> List[str]:
        """Check for missing dependencies."""
        missing = []
        for pkg in self.required_packages:
            if pkg.lower() not in self.installed_packages:
                missing.append(pkg)
        return missing
    
    def install_dependencies(self, packages: List[str]) -> bool:
        """Install missing dependencies using pip."""
        if not packages:
            return True
            
        try:
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install'] + packages,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
    
    def validate(self) -> bool:
        """Run all validations and return True if everything is OK."""
        logger.info("Running project validation...")
        
        # Check for missing dependencies
        missing_deps = self.check_missing_dependencies()
        if missing_deps:
            logger.warning(f"Missing dependencies: {', '.join(missing_deps)}")
            if self.install_dependencies(missing_deps):
                logger.info("Successfully installed missing dependencies")
                # Refresh installed packages
                self.installed_packages = self._get_installed_packages()
        
        # Run validations
        self.check_imports()
        self.check_indentation()
        
        # Fix issues
        for issue in self.indentation_issues:
            if issue['type'] == 'indentation':
                self.fix_indentation(issue['file'])
        
        # Report results
        has_errors = bool(self.import_errors or self.syntax_errors)
        
        if self.import_errors:
            logger.error(f"Found {len(self.import_errors)} import errors")
        if self.syntax_errors:
            logger.error(f"Found {len(self.syntax_errors)} syntax errors")
        if self.indentation_issues:
            logger.warning(f"Fixed {len(self.indentation_issues)} indentation issues")
        
        return not has_errors


def validate_project_integrity() -> bool:
    """
    Validate the project's integrity by checking for common issues.
    
    Returns:
        bool: True if the project passed all validations, False otherwise.
    """
    try:
        validator = ProjectValidator()
        return validator.validate()
    except Exception as e:
        logger.error(f"Error during project validation: {e}")
        return False


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run validation
    success = validate_project_integrity()
    if success:
        logger.info("Project validation completed successfully")
    else:
        logger.error("Project validation found issues that need attention")
    
    sys.exit(0 if success else 1)
