import pytest
import os
import sys

# Add the don directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'don'))

def test_env_file_exists():
    """Test that .env file exists"""
    assert os.path.exists('.env'), ".env file should exist"

def test_data_directory_exists():
    """Test that data directory exists"""
    assert os.path.exists('data'), "data directory should exist"

def test_logs_directory_exists():
    """Test that logs directory exists"""
    assert os.path.exists('logs'), "logs directory should exist"

def test_memory_json_exists():
    """Test that memory.json exists"""
    assert os.path.exists('data/memory.json'), "data/memory.json file should exist"

def test_config_files_exist():
    """Test that config files exist"""
    assert os.path.exists('config/paths.json'), "config/paths.json file should exist"
    assert os.path.exists('config/settings.json'), "config/settings.json file should exist"

if __name__ == "__main__":
    pytest.main([__file__])