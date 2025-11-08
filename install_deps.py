"""
Dependency Installation Script

This script ensures all required dependencies are installed and the project is properly set up.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(cmd: list, cwd: str = None) -> bool:
    """Run a shell command and return True if successful."""
    try:
        logger.info(f"Running: {' '.join(cmd)}")
        subprocess.check_call(cmd, cwd=cwd, shell=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with error {e.returncode}")
        return False

def ensure_virtualenv() -> bool:
    """Ensure a virtual environment is set up and activated."""
    venv_dir = os.path.join(os.path.dirname(__file__), 'venv')
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists(venv_dir):
        logger.info("Creating virtual environment...")
        if not run_command([sys.executable, '-m', 'venv', 'venv']):
            return False
    
    # Determine the correct pip executable
    pip_executable = os.path.join(venv_dir, 'Scripts', 'pip')
    if os.name == 'nt':  # Windows
        pip_executable += '.exe'
    
    if not os.path.exists(pip_executable):
        logger.error(f"Could not find pip at {pip_executable}")
        return False
    
    return True

def install_dependencies() -> bool:
    """Install required dependencies from requirements.txt."""
    requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    
    if not os.path.exists(requirements_file):
        logger.error("requirements.txt not found!")
        return False
    
    # Use the virtual environment's pip to install dependencies
    pip_executable = os.path.join('venv', 'Scripts', 'pip')
    if os.name == 'nt':  # Windows
        pip_executable += '.exe'
    
    logger.info("Installing dependencies...")
    return run_command([pip_executable, 'install', '-r', requirements_file])

def main() -> int:
    """Main entry point for the installation script."""
    logger.info("Setting up the project...")
    
    # Ensure virtual environment exists
    if not ensure_virtualenv():
        logger.error("Failed to set up virtual environment")
        return 1
    
    # Install dependencies
    if not install_dependencies():
        logger.error("Failed to install dependencies")
        return 1
    
    logger.info("\nSetup completed successfully!")
    logger.info("To activate the virtual environment, run:")
    logger.info("  On Windows: .\\venv\\Scripts\\activate")
    logger.info("  On Unix/Mac: source venv/bin/activate")
    logger.info("\nThen run: python -m don.main")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
