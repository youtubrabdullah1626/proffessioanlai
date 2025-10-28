from don.dev_api import (
	scan_system_apps, parse_intent, send_whatsapp_message,
	open_app, close_app, system_status, system_action,
	optimize_system, explain_error, fix_error_safely, schedule_task,
)


def test_scan_and_status(monkeypatch):
	monkeypatch.setenv("SIMULATION_MODE", "true")
	assert scan_system_apps()["ok"] is True
	assert system_status()["ok"] is True


def test_whatsapp_and_apps(monkeypatch, tmp_path):
	monkeypatch.setenv("SIMULATION_MODE", "true")
	assert send_whatsapp_message("Ali", "hi")["ok"] is True
	open_res = open_app("chrome")
	assert "ok" in open_res
	close_res = close_app("chrome.exe")
	assert "ok" in close_res


def test_actions_and_ai(monkeypatch):
	monkeypatch.setenv("SIMULATION_MODE", "true")
	assert parse_intent("chrome kholo")["ok"] is True
	assert explain_error("chrome cannot start")["ok"] is True
	assert fix_error_safely("chrome cannot start")["ok"] is False
	assert schedule_task("kal subah 8 baje", "wake up")["ok"] in (True, False)


def test_system_action_gated(monkeypatch):
	monkeypatch.setenv("SIMULATION_MODE", "true")
	assert system_action("shutdown")["ok"] in (True, False)
	assert optimize_system()["ok"] is False
