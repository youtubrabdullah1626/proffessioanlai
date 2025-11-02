#!/usr/bin/env python3
"""
Simulation of 5 voice commands for Nexhan Nova (Don) AI Assistant
This script demonstrates the system working in SIMULATION_MODE
"""

import os
import sys
import json

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from don.executor import execute_command
from don.tts import init_tts, speak_mixed
from don.config import load_settings


def simulate_voice_command(command_text):
    """Simulate processing a voice command"""
    print(f"[INFO] Heard: {command_text}")
    
    # Execute the command (in simulation mode)
    result = execute_command(command_text)
    
    print(f"[INFO] Execution result: {result}")
    print("-" * 50)


def main():
    """Run simulation of 5 voice commands"""
    print("Nexhan Nova (Don) - Voice Command Simulation")
    print("=" * 50)
    print("SIMULATION_MODE: True (No actual system changes will be made)")
    print()
    
    # Test commands
    commands = [
        "send whatsapp message to ali saying hello",
        "open chrome browser", 
        "search for weather forecast",
        "take a screenshot please",
        "shutdown the computer"
    ]
    
    for i, command in enumerate(commands, 1):
        print(f"Command {i}: {command}")
        simulate_voice_command(command)


if __name__ == "__main__":
    main()