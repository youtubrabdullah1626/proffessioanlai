import pytest
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add the don directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'don'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.scanner import scan_system_apps, save_system_apps_to_config, scan_and_save_system_apps
from don.first_launch import ensure_first_launch, is_first_run, run_onboarding_if_needed


def test_scan_system_apps():
    """Test scanning system apps."""
    result = scan_system_apps()
    assert isinstance(result, dict)
    # Should at least have the default apps
    assert "whatsapp" in result or "chrome" in result or "edge" in result


def test_save_system_apps_to_config(tmp_path):
    """Test saving system apps to config file."""
    config_path = tmp_path / "paths.json"
    apps = {
        "test_app": ["C:\\Program Files\\TestApp\\test.exe"]
    }
    
    result = save_system_apps_to_config(apps, str(config_path))
    assert result is True
    assert config_path.exists()
    
    # Verify content
    with open(config_path, "r") as f:
        saved_apps = json.load(f)
    assert saved_apps == apps


def test_scan_and_save_system_apps(tmp_path):
    """Test scanning and saving system apps."""
    config_path = tmp_path / "paths.json"
    
    result = scan_and_save_system_apps(str(config_path))
    assert isinstance(result, bool)
    # The function should complete without error


def test_is_first_run(tmp_path, monkeypatch):
    """Test checking if it's first run."""
    # Change to temp directory
    monkeypatch.chdir(tmp_path)
    
    # Should be first run in empty directory
    result = is_first_run()
    assert result is True


def test_ensure_first_launch(tmp_path, monkeypatch):
    """Test first launch setup."""
    # Change to temp directory
    monkeypatch.chdir(tmp_path)
    
    result = ensure_first_launch()
    assert isinstance(result, dict)
    
    # Check that required directories were created
    for dir_name in ["logs", "data", "memory", "config"]:
        assert (tmp_path / dir_name).exists()
    
    # Check that memory files were created
    assert (tmp_path / "memory" / "memory.json").exists()
    assert (tmp_path / "memory" / "memory.db").exists()
    
    # Check that config files were created
    assert (tmp_path / "data" / "system_apps.json").exists()
    assert (tmp_path / "config" / "paths.json").exists()


def test_run_onboarding_if_needed(tmp_path, monkeypatch):
    """Test running onboarding if needed."""
    # Change to temp directory
    monkeypatch.chdir(tmp_path)
    
    # Should run onboarding in empty directory
    result = run_onboarding_if_needed()
    assert result is True
    
    # Should not run onboarding again
    result = run_onboarding_if_needed()
    assert result is False


if __name__ == "__main__":
    pytest.main([__file__])