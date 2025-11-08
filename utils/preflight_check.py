"""
Pre-run validation and syntax checking for the project.
"""
import os
import sys
import importlib
import ast
from pathlib import Path
from typing import List, Dict, Tuple

class PreflightCheck:
    """Static class for pre-run validations."""
    
    @staticmethod
    def check_syntax(filepath: str) -> Tuple[bool, str]:
        """Check Python file syntax without importing it."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
            return True, ""
        except SyntaxError as e:
            return False, f"Syntax error in {filepath}: {e}"
    
    @staticmethod
    def check_imports() -> List[str]:
        """Check if all required imports are available."""
        required_imports = [
            'speech_recognition',
            'pyaudio',
            'pyttsx3',
            'python-dotenv',
            'google.generativeai',
        ]
        
        missing = []
        for package in required_imports:
            try:
                importlib.import_module(package.split('.')[0])
            except ImportError:
                missing.append(package)
        return missing
    
    @classmethod
    def run_checks(cls) -> bool:
        """Run all preflight checks."""
        print("\n🔍 Running preflight checks...")
        
        # Check Python files syntax
        print("\n🔎 Checking Python files syntax...")
        root_dir = Path(__file__).parent.parent
        python_files = list(root_dir.rglob('*.py'))
        
        has_errors = False
        for py_file in python_files:
            if 'venv' in str(py_file) or 'build' in str(py_file):
                continue
                
            is_valid, error = cls.check_syntax(py_file)
            if not is_valid:
                print(f"❌ {error}")
                has_errors = True
            else:
                print(f"✅ {py_file.relative_to(root_dir)}: Syntax OK")
        
        # Check imports
        print("\n📦 Checking required packages...")
        missing_imports = cls.check_imports()
        if missing_imports:
            print("❌ Missing required packages:")
            for imp in missing_imports:
                print(f"   - {imp}")
            print("\nInstall missing packages with:")
            print(f"pip install {' '.join(missing_imports)}")
            has_errors = True
        else:
            print("✅ All required packages are installed")
        
        if has_errors:
            print("\n❌ Preflight checks failed. Please fix the issues above.")
            return False
        
        print("\n✨ All preflight checks passed!")
        return True


def setup_pre_commit_hook():
    """Set up git pre-commit hook to run preflight checks."""
    hook_content = '''#!/bin/sh
    echo "🚀 Running pre-commit checks..."
    python utils/preflight_check.py || exit 1
    '''
    
    hook_path = Path('.git/hooks/pre-commit')
    if not hook_path.parent.exists():
        print("ℹ️  .git/hooks directory not found. Is this a git repository?")
        return False
    
    with open(hook_path, 'w') as f:
        f.write(hook_content)
    
    # Make the hook executable (Unix-like systems)
    if hasattr(os, 'chmod'):
        os.chmod(hook_path, 0o755)
    
    print("✅ Pre-commit hook installed successfully")
    return True


if __name__ == "__main__":
    if not PreflightCheck.run_checks():
        sys.exit(1)
