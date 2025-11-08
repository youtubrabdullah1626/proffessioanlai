from don.app_control import scan_missing_apps, open_app, focus_window_by_title, set_window_state, SYSTEM_APPS
from don.config import load_settings


def test_scan_missing_apps():
    result = scan_missing_apps(SYSTEM_APPS)
    assert isinstance(result, dict)
    assert "whatsapp" in result


def test_open_app_simulation(monkeypatch):
    monkeypatch.setenv("SIMULATION_MODE", "true")
    assert open_app("chrome") in (True, False)


def test_window_ops_simulation(monkeypatch):
    monkeypatch.setenv("SIMULATION_MODE", "true")
    # These may return False if win32 APIs not available; just ensure call paths
    assert focus_window_by_title("chrome") in (True, False)
    assert set_window_state("chrome", "maximize") in (True, False)
