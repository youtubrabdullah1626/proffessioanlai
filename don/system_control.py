import os
import subprocess
import time
from typing import List, Optional, Tuple

import psutil

try:
	import wmi  # type: ignore
	has_wmi = True
except Exception:
	has_wmi = False

try:
	from mss import mss  # type: ignore
	has_mss = True
except Exception:
	has_mss = False

try:
	from comtypes import CLSCTX_ALL  # type: ignore
	from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # type: ignore
	has_pycaw = True
except Exception:
	has_pycaw = False

from .logging_utils import setup_logging
from .safety import is_simulation_mode, require_confirmation

logger = setup_logging()


# Power controls

def _run_cmd(cmd: List[str]) -> bool:
	try:
		if is_simulation_mode():
			logger.info(f"[SIMULATION] Would run: {' '.join(cmd)}")
			return True
		subprocess.Popen(cmd, shell=False)
		return True
	except Exception as e:
		logger.error(f"Command failed: {e}")
		return False


def shutdown() -> bool:
	return require_confirmation("shutdown") and _run_cmd(["shutdown", "/s", "/t", "0"])


def restart() -> bool:
	return require_confirmation("restart") and _run_cmd(["shutdown", "/r", "/t", "0"])


def sleep() -> bool:
	return require_confirmation("sleep") and _run_cmd(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])


def lock() -> bool:
	return _run_cmd(["rundll32.exe", "user32.dll,LockWorkStation"])


def logoff() -> bool:
	return require_confirmation("log off current user") and _run_cmd(["shutdown", "/l"])


# Network controls (basic stubs)

def toggle_wifi(enable: bool) -> bool:
	action = "enable Wi-Fi" if enable else "disable Wi-Fi"
	if not require_confirmation(action):
		return False
	# For production: use netsh interface set interface name=Wi-Fi admin=enabled/disabled
	cmd = ["netsh", "interface", "set", "interface", "name=Wi-Fi", f"admin={'enabled' if enable else 'disabled'}"]
	return _run_cmd(cmd)


def toggle_airplane_mode(enable: bool) -> bool:
	# Airplane mode programmatic toggle is restricted; log intent.
	logger.warning("Airplane mode toggle is restricted; manual action suggested.")
	return False


def restart_network_adapter() -> bool:
	if not require_confirmation("restart network adapter Wi-Fi"):
		return False
	ok1 = _run_cmd(["netsh", "interface", "set", "interface", "name=Wi-Fi", "admin=disabled"])
	time.sleep(1)
	ok2 = _run_cmd(["netsh", "interface", "set", "interface", "name=Wi-Fi", "admin=enabled"])
	return ok1 and ok2


# Resource usage and temps

def get_system_usage() -> dict:
	"""Return CPU, RAM, disk usage and temperatures (WMI if available)."""
	info = {
		"cpu_percent": psutil.cpu_percent(interval=0.2),
		"ram_percent": psutil.virtual_memory().percent,
		"disk_percent": psutil.disk_usage(os.getenv("SystemDrive", "C:")).percent,
		"temps_c": [],
	}
	try:
		if has_wmi:
			c = wmi.WMI(namespace="root\\OpenHardwareMonitor")
			for sensor in c.Sensor():
				if sensor.SensorType == "Temperature":
					info["temps_c"].append({"name": sensor.Name, "value": sensor.Value})
	except Exception:
		pass
	return info


# Process management

def list_heavy_processes(top_n: int = 5) -> List[Tuple[int, str, float]]:
	try:
		procs: List[Tuple[int, str, float]] = []
		for p in psutil.process_iter(["pid", "name", "cpu_percent"]):
			info = p.info
			procs.append((info.get("pid", 0), info.get("name", ""), info.get("cpu_percent", 0.0)))
		procs.sort(key=lambda x: x[2], reverse=True)
		return procs[:top_n]
	except Exception:
		return []


def kill_process(pid: int) -> bool:
	if not require_confirmation(f"kill process {pid}"):
		return False
	try:
		if is_simulation_mode():
			logger.info(f"[SIMULATION] Would kill PID {pid}")
			return True
		psutil.Process(pid).terminate()
		return True
	except Exception as e:
		logger.error(f"kill_process failed: {e}")
		return False


def force_kill_process(pid: int) -> bool:
	"""Force kill a process (dangerous operation)."""
	if not require_confirmation(f"force kill process {pid}"):
		return False
	try:
		if is_simulation_mode():
			logger.info(f"[SIMULATION] Would force kill PID {pid}")
			return True
		psutil.Process(pid).kill()
		return True
	except Exception as e:
		logger.error(f"force_kill_process failed: {e}")
		return False


# Startup apps (basic listing and enable/disable placeholder)

def list_startup_apps() -> List[str]:
	try:
		# For later: read from HKCU/HKLM Run keys; placeholder list
		return ["Microsoft OneDrive", "Windows Security"]
	except Exception:
		return []


def set_startup_app(app_name: str, enable: bool) -> bool:
	logger.warning("Startup app management requires registry edits; deferred to later part.")
	return False


# Brightness/volume controls

def set_system_volume(percent: int) -> bool:
	try:
		percent = max(0, min(100, percent))
		if not has_pycaw:
			logger.warning("pycaw not available; cannot set system volume.")
			return False
		if is_simulation_mode():
			logger.info(f"[SIMULATION] Would set volume to {percent}%")
			return True
		sessions = AudioUtilities.GetSpeakers()
		interface = sessions.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
		volume = interface.QueryInterface(IAudioEndpointVolume)
		# Convert 0-100 to scalar 0.0-1.0
		scalar = percent / 100.0
		volume.SetMasterVolumeLevelScalar(scalar, None)
		return True
	except Exception as e:
		logger.error(f"set_system_volume failed: {e}")
		return False


def mute_system(mute: bool) -> bool:
	try:
		if not has_pycaw:
			logger.warning("pycaw not available; cannot mute/unmute.")
			return False
		if is_simulation_mode():
			logger.info(f"[SIMULATION] Would {'mute' if mute else 'unmute'} system audio")
			return True
		sessions = AudioUtilities.GetSpeakers()
		interface = sessions.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
		volume = interface.QueryInterface(IAudioEndpointVolume)
		volume.SetMute(mute, None)
		return True
	except Exception as e:
		logger.error(f"mute_system failed: {e}")
		return False


def take_screenshot(path: str) -> bool:
	try:
		if not has_mss:
			logger.warning("mss not available; cannot take screenshot.")
			return False
		if is_simulation_mode():
			logger.info(f"[SIMULATION] Would save screenshot to {path}")
			return True
		with mss() as sct:
			sct.shot(output=path)
		return True
	except Exception as e:
		logger.error(f"take_screenshot failed: {e}")
		return False


def get_battery_status() -> dict:
	"""Get battery status information."""
	try:
		battery = psutil.sensors_battery()
		if battery:
			return {
				"percent": battery.percent,
				"secsleft": battery.secsleft,
				"power_plugged": battery.power_plugged
			}
		return {"percent": 100, "secsleft": -1, "power_plugged": True}  # Desktop
	except Exception as e:
		logger.error(f"get_battery_status failed: {e}")
		return {"percent": 100, "secsleft": -1, "power_plugged": True}


def hibernate() -> bool:
	"""Put the system into hibernation mode."""
	return require_confirmation("hibernate system") and _run_cmd(["shutdown", "/h"])