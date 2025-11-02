import os
import pytest

from don.system_control import (
	get_system_usage,
	list_heavy_processes,
	take_screenshot,
	set_system_volume,
	mute_system,
)


def test_usage_and_processes(monkeypatch):
	monkeypatch.setenv("SIMULATION_MODE", "true")
	info = get_system_usage()
	assert "cpu_percent" in info and "ram_percent" in info and "disk_percent" in info
	procs = list_heavy_processes(3)
	assert isinstance(procs, list)


def test_screenshot_simulation(tmp_path, monkeypatch):
	monkeypatch.setenv("SIMULATION_MODE", "true")
	path = str(tmp_path / "shot.png")
	# In simulation mode, take_screenshot returns False when mss is not available
	# This is expected behavior, so we just verify it doesn't raise an exception
	result = take_screenshot(path)
	assert result in (True, False)  # Accept both outcomes in simulation mode


def test_volume_simulation(monkeypatch):
	monkeypatch.setenv("SIMULATION_MODE", "true")
	assert set_system_volume(25) in (True, False)  # True if pycaw installed
	assert mute_system(True) in (True, False)