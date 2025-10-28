from don.intent_parser import parse_intent
from don.executor import execute_command


def test_optimize_and_screenshot(monkeypatch):
	monkeypatch.setenv("SIMULATION_MODE", "true")
	res1 = parse_intent("Don, system optimize kro")
	assert res1["intent"] == "optimize_system"
	res2 = parse_intent("Don, screenshot le lo aur desktop pe save karo")
	assert res2["intent"] in ("screenshot", "file_action")

	out1 = execute_command("Don, system optimize kro")
	assert "ok" in out1
	out2 = execute_command("Don, set reminder kal 7am study")
	assert "ok" in out2


def test_error_analysis():
	res = parse_intent("Don, ye error aa raha hai chrome cannot start")
	assert res["intent"] == "error_analysis"
