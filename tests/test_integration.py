import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the don directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'don'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from don.self_check import (
    check_imports, check_paths, check_tts_simulation, check_stt_simulation,
    check_intent_parsing, check_executor_dry_runs, check_memory_operations,
    self_check
)


def test_imports_check():
    """Test import checking functionality."""
    result = check_imports()
    assert isinstance(result, dict)
    # At least core modules should be importable
    assert "core.listener" in result
    assert "core.speaker" in result
    assert "core.intent_engine" in result


def test_paths_check():
    """Test path checking functionality."""
    result = check_paths()
    assert isinstance(result, dict)
    # Should check for required paths
    assert "config/paths.json" in result
    assert "config/settings.json" in result
    assert "memory/memory.json" in result
    assert "memory/memory.db" in result


def test_tts_simulation():
    """Test TTS simulation."""
    result = check_tts_simulation()
    assert isinstance(result, bool)


def test_stt_simulation():
    """Test STT simulation."""
    result = check_stt_simulation()
    assert isinstance(result, bool)


def test_intent_parsing():
    """Test intent parsing with examples."""
    result = check_intent_parsing()
    assert isinstance(result, dict)
    # Should have results for all test commands
    assert len(result) > 0


def test_executor_dry_runs():
    """Test executor dry runs."""
    result = check_executor_dry_runs()
    assert isinstance(result, dict)
    # Should have results for all test commands
    assert len(result) > 0


def test_memory_operations():
    """Test memory operations."""
    result = check_memory_operations()
    assert isinstance(result, bool)


def test_self_check():
    """Test comprehensive self-check."""
    result = self_check()
    assert isinstance(result, dict)
    
    # Should have required keys
    assert "timestamp" in result
    assert "overall_status" in result
    assert "detailed_results" in result
    assert "auto_fix_recommendations" in result
    assert "summary" in result
    
    # Detailed results should contain all check categories
    detailed = result["detailed_results"]
    assert "imports" in detailed
    assert "paths" in detailed
    assert "tts_simulation" in detailed
    assert "stt_simulation" in detailed
    assert "intent_parsing" in detailed
    assert "executor_dry_runs" in detailed
    assert "memory_operations" in detailed
    
    # Summary should have correct structure
    summary = result["summary"]
    assert "total_checks" in summary
    assert "passed_checks" in summary
    assert "failed_checks" in summary


if __name__ == "__main__":
    pytest.main([__file__])