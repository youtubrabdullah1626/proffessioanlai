import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the don directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'don'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from don.file_control import copy_file, get_file_info, list_directory


def test_copy_file():
    """Test copying file function."""
    # This should not raise an exception
    result = copy_file("source.txt", "destination.txt")
    assert isinstance(result, bool)


def test_get_file_info():
    """Test getting file info."""
    result = get_file_info("nonexistent.txt")
    assert isinstance(result, dict)


def test_list_directory():
    """Test listing directory contents."""
    result = list_directory(".", recursive=False)
    assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__])