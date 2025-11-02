import pytest
import os
import sys
import threading
import time
from unittest.mock import patch, MagicMock

# Add the don directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'don'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.listener import STTEngine, BackgroundListener, listen_once_text, start_background_listener
from core.speaker import speak, is_speaking
from core.intent_engine import parse, parse_with_fuzzy_heuristics, get_intent_schema
from core.memory import MemoryManager, read_memory, write_memory, update_memory, get_memory_value


def test_stt_engine_initialization():
    """Test STT engine initialization."""
    stt = STTEngine()
    assert stt is not None


def test_speaker_initialization():
    """Test speaker initialization."""
    # This test would require mocking the TTS engine
    pass


def test_intent_parser():
    """Test intent parsing."""
    result = parse("send whatsapp message to ali saying hello")
    assert isinstance(result, dict)
    assert "intent" in result
    assert "confidence" in result


def test_fuzzy_intent_parser():
    """Test fuzzy intent parsing."""
    result = parse_with_fuzzy_heuristics("open chrome browser")
    assert isinstance(result, dict)
    assert "intent" in result


def test_intent_schema():
    """Test intent schema retrieval."""
    schema = get_intent_schema()
    assert isinstance(schema, dict)
    assert "intent" in schema


def test_memory_manager_initialization(tmp_path):
    """Test memory manager initialization."""
    memory_json = tmp_path / "memory.json"
    memory_db = tmp_path / "memory.db"
    manager = MemoryManager(str(memory_json), str(memory_db))
    assert manager is not None


def test_memory_read_write(tmp_path):
    """Test memory read/write operations."""
    memory_json = tmp_path / "memory.json"
    memory_db = tmp_path / "memory.db"
    manager = MemoryManager(str(memory_json), str(memory_db))
    
    # Test write
    test_data = {"test_key": "test_value"}
    assert manager.write_memory(test_data) is True
    
    # Test read
    read_data = manager.read_memory()
    assert read_data == test_data


def test_memory_update(tmp_path):
    """Test memory update operations."""
    memory_json = tmp_path / "memory.json"
    memory_db = tmp_path / "memory.db"
    manager = MemoryManager(str(memory_json), str(memory_db))
    
    # Test update
    assert manager.update_memory("new_key", "new_value") is True
    
    # Test get value
    value = manager.get_memory_value("new_key")
    assert value == "new_value"


def test_global_memory_functions(tmp_path, monkeypatch):
    """Test global memory functions."""
    # Change to temp directory
    monkeypatch.chdir(tmp_path)
    
    # Test read/write through global functions
    test_data = {"global_test": "global_value"}
    assert write_memory(test_data) is True
    
    read_data = read_memory()
    assert read_data == test_data
    
    # Test update through global function
    assert update_memory("global_key", "global_value") is True
    
    # Test get value through global function
    value = get_memory_value("global_key")
    assert value == "global_value"


if __name__ == "__main__":
    pytest.main([__file__])