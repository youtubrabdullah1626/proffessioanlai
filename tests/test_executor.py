from don.executor import execute_command


def test_exec_whatsapp(monkeypatch):
	monkeypatch.setenv("SIMULATION_MODE", "true")
	res = execute_command('jao Ali ko whatsapp me msg kro "hello"')
	assert res["handler"] == "whatsapp"


def test_exec_open_search(monkeypatch):
	monkeypatch.setenv("SIMULATION_MODE", "true")
	res1 = execute_command("chrome kholo")
	res2 = execute_command("youtube pe Atif Aslam search karo")
	assert res1["handler"] in ("open_app", "unknown")
	assert res2["handler"] == "search_web"
