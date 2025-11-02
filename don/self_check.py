import os
import sys
import importlib
from typing import Dict, List, Tuple

from .logging_utils import setup_logging
from .config import load_settings
from .intent_parser import parse_intent
from .executor import execute_command

logger = setup_logging()


def check_imports() -> Dict[str, bool]:
    """Check if all required modules can be imported."""
    modules_to_check = [
        "core.listener",
        "core.speaker",
        "core.intent_engine",
        "core.memory",
        "don.comms_ai",
        "don.whatsapp_automation",
        "don.app_control",
        "don.system_control",
        "don.file_control",
        "don.scanner",
        "commands.whatsapp_handlers",
        "commands.app_control",
        "commands.system_control",
        "commands.file_manager",
        "utils.scanner"
    ]
    
    results = {}
    for module in modules_to_check:
        try:
            importlib.import_module(module)
            results[module] = True
        except Exception as e:
            logger.error(f"Failed to import {module}: {e}")
            results[module] = False
    
    return results


def check_paths() -> Dict[str, bool]:
    """Check if required paths exist."""
    required_paths = [
        "config/paths.json",
        "config/settings.json",
        "memory/memory.json",
        "memory/memory.db"
    ]
    
    results = {}
    for path in required_paths:
        results[path] = os.path.exists(path)
        if not results[path]:
            logger.warning(f"Missing path: {path}")
    
    return results


def check_tts_simulation() -> bool:
    """Check if TTS simulation works."""
    try:
        from core.speaker import speak
        # Test in simulation mode
        result = speak("Test message", wait=True)
        return result is not None
    except Exception as e:
        logger.error(f"TTS simulation failed: {e}")
        return False


def check_stt_simulation() -> bool:
    """Check if STT simulation works."""
    try:
        from core.listener import listen_once_text
        # This would normally listen, but in simulation mode it should return a test string
        result = listen_once_text()
        return isinstance(result, str)
    except Exception as e:
        logger.error(f"STT simulation failed: {e}")
        return False


def check_intent_parsing() -> Dict[str, bool]:
    """Check intent parsing with example commands."""
    test_commands = [
        "send whatsapp message to ali saying hello",
        "open chrome browser",
        "close notepad application",
        "search for weather forecast",
        "shutdown the computer",
        "restart system now",
        "take a screenshot please",
        "schedule a reminder for tomorrow",
        "optimize system performance",
        "lock the screen"
    ]
    
    results = {}
    for i, command in enumerate(test_commands):
        try:
            result = parse_intent(command)
            results[f"command_{i+1}"] = isinstance(result, dict) and "intent" in result
            if not results[f"command_{i+1}"]:
                logger.warning(f"Intent parsing failed for: {command}")
        except Exception as e:
            logger.error(f"Intent parsing failed for '{command}': {e}")
            results[f"command_{i+1}"] = False
    
    return results


def check_executor_dry_runs() -> Dict[str, bool]:
    """Check executor with dry runs."""
    test_commands = [
        "send whatsapp message to ali saying hello",
        "open chrome browser",
        "search for weather forecast",
        "take a screenshot please"
    ]
    
    results = {}
    for i, command in enumerate(test_commands):
        try:
            # Executor should work in simulation mode
            result = execute_command(command)
            results[f"executor_{i+1}"] = isinstance(result, dict) and "ok" in result
            if not results[f"executor_{i+1}"]:
                logger.warning(f"Executor dry run failed for: {command}")
        except Exception as e:
            logger.error(f"Executor dry run failed for '{command}': {e}")
            results[f"executor_{i+1}"] = False
    
    return results


def check_memory_operations() -> bool:
    """Check memory read/write operations."""
    try:
        from core.memory import read_memory, write_memory, update_memory
        
        # Read memory
        memory = read_memory()
        if not isinstance(memory, dict):
            logger.warning("Memory read returned non-dict")
            return False
        
        # Write test data
        test_data = {"self_check_test": "test_value"}
        if not write_memory(test_data):
            logger.warning("Memory write failed")
            return False
        
        # Update memory
        if not update_memory("self_check_test_2", "test_value_2"):
            logger.warning("Memory update failed")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Memory operations failed: {e}")
        return False


def self_check() -> Dict[str, any]:
    """
    Run a comprehensive self-check of the system.
    
    Returns:
        Dict containing check results and auto-fix recommendations
    """
    logger.info("Starting self-check...")
    
    results = {
        "imports": check_imports(),
        "paths": check_paths(),
        "tts_simulation": check_tts_simulation(),
        "stt_simulation": check_stt_simulation(),
        "intent_parsing": check_intent_parsing(),
        "executor_dry_runs": check_executor_dry_runs(),
        "memory_operations": check_memory_operations()
    }
    
    # Calculate overall status
    all_imports_ok = all(results["imports"].values())
    all_paths_ok = all(results["paths"].values())
    intent_parsing_ok = all(results["intent_parsing"].values())
    executor_dry_runs_ok = all(results["executor_dry_runs"].values())
    
    overall_status = (
        all_imports_ok and 
        all_paths_ok and 
        results["tts_simulation"] and 
        results["stt_simulation"] and 
        intent_parsing_ok and 
        executor_dry_runs_ok and 
        results["memory_operations"]
    )
    
    # Generate auto-fix recommendations
    auto_fix_list = []
    
    # Check for missing imports
    missing_imports = [mod for mod, ok in results["imports"].items() if not ok]
    if missing_imports:
        auto_fix_list.append(f"Install missing modules: {', '.join(missing_imports)}")
    
    # Check for missing paths
    missing_paths = [path for path, ok in results["paths"].items() if not ok]
    if missing_paths:
        auto_fix_list.append(f"Create missing paths: {', '.join(missing_paths)}")
    
    # Check for TTS issues
    if not results["tts_simulation"]:
        auto_fix_list.append("Check TTS engine installation (pyttsx3)")
    
    # Check for STT issues
    if not results["stt_simulation"]:
        auto_fix_list.append("Check STT engine installation (SpeechRecognition, PyAudio)")
    
    # Check for intent parsing issues
    failed_intent_parsing = [cmd for cmd, ok in results["intent_parsing"].items() if not ok]
    if failed_intent_parsing:
        auto_fix_list.append(f"Fix intent parsing for commands: {', '.join(failed_intent_parsing)}")
    
    # Check for executor issues
    failed_executors = [cmd for cmd, ok in results["executor_dry_runs"].items() if not ok]
    if failed_executors:
        auto_fix_list.append(f"Fix executors for commands: {', '.join(failed_executors)}")
    
    # Check for memory issues
    if not results["memory_operations"]:
        auto_fix_list.append("Fix memory operations")
    
    # Add general recommendations
    if not overall_status:
        auto_fix_list.append("Run first_launch setup to initialize missing components")
        auto_fix_list.append("Check .env configuration file")
        auto_fix_list.append("Verify virtual environment is activated")
    
    final_results = {
        "timestamp": "2025-10-31T00:00:00Z",
        "overall_status": overall_status,
        "detailed_results": results,
        "auto_fix_recommendations": auto_fix_list,
        "summary": {
            "total_checks": 7,
            "passed_checks": sum([
                all_imports_ok,
                all_paths_ok,
                results["tts_simulation"],
                results["stt_simulation"],
                intent_parsing_ok,
                executor_dry_runs_ok,
                results["memory_operations"]
            ]),
            "failed_checks": sum([
                not all_imports_ok,
                not all_paths_ok,
                not results["tts_simulation"],
                not results["stt_simulation"],
                not intent_parsing_ok,
                not executor_dry_runs_ok,
                not results["memory_operations"]
            ])
        }
    }
    
    logger.info(f"Self-check complete. Status: {'PASS' if overall_status else 'FAIL'}")
    if auto_fix_list:
        logger.info(f"Auto-fix recommendations: {len(auto_fix_list)} items")
        for i, fix in enumerate(auto_fix_list, 1):
            logger.info(f"  {i}. {fix}")
    
    return final_results


def run_self_check_and_report() -> None:
    """Run self-check and print a detailed report."""
    results = self_check()
    
    print("\n" + "="*60)
    print("NEXHAN NOVA (DON) SELF-CHECK REPORT")
    print("="*60)
    
    print(f"\nOverall Status: {'PASS' if results['overall_status'] else 'FAIL'}")
    
    print(f"\nSummary:")
    print(f"  Total Checks: {results['summary']['total_checks']}")
    print(f"  Passed: {results['summary']['passed_checks']}")
    print(f"  Failed: {results['summary']['failed_checks']}")
    
    print(f"\nDetailed Results:")
    
    # Imports
    print(f"  Imports: {'PASS' if all(results['imports'].values()) else 'FAIL'}")
    failed_imports = [mod for mod, ok in results['imports'].items() if not ok]
    if failed_imports:
        print(f"    Failed: {', '.join(failed_imports)}")
    
    # Paths
    print(f"  Paths: {'PASS' if all(results['paths'].values()) else 'FAIL'}")
    missing_paths = [path for path, ok in results['paths'].items() if not ok]
    if missing_paths:
        print(f"    Missing: {', '.join(missing_paths)}")
    
    # TTS/STT
    print(f"  TTS Simulation: {'PASS' if results['tts_simulation'] else 'FAIL'}")
    print(f"  STT Simulation: {'PASS' if results['stt_simulation'] else 'FAIL'}")
    
    # Intent Parsing
    intent_ok = all(results['intent_parsing'].values())
    print(f"  Intent Parsing: {'PASS' if intent_ok else 'FAIL'}")
    failed_intents = [cmd for cmd, ok in results['intent_parsing'].items() if not ok]
    if failed_intents:
        print(f"    Failed Commands: {len(failed_intents)}")
    
    # Executor
    executor_ok = all(results['executor_dry_runs'].values())
    print(f"  Executor Dry Runs: {'PASS' if executor_ok else 'FAIL'}")
    failed_executors = [cmd for cmd, ok in results['executor_dry_runs'].items() if not ok]
    if failed_executors:
        print(f"    Failed Commands: {len(failed_executors)}")
    
    # Memory
    print(f"  Memory Operations: {'PASS' if results['memory_operations'] else 'FAIL'}")
    
    # Auto-fix recommendations
    if results['auto_fix_recommendations']:
        print(f"\nAuto-fix Recommendations:")
        for i, recommendation in enumerate(results['auto_fix_recommendations'], 1):
            print(f"  {i}. {recommendation}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    run_self_check_and_report()