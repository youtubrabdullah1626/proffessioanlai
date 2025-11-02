import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the don directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'don'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from don.system_control import force_kill_process, get_battery_status, hibernate


def test_force_kill_process():
    """Test force killing process function."""
    # This should not raise an exception
    result = force_kill_process(1234)
    assert isinstance(result, bool)


def test_get_battery_status():
    """Test getting battery status."""
    result = get_battery_status()
    assert isinstance(result, dict)
    assert "percent" in result


def test_hibernate():
    """Test hibernate function."""
    # This should not raise an exception
    result = hibernate()
    assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__])