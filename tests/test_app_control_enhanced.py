import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the don directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'don'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from don.app_control import kill_app_process


def test_kill_app_process():
    """Test killing app process function."""
    # This should not raise an exception
    result = kill_app_process("test_app.exe", force=False)
    assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__])