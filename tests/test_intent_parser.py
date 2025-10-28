from don.intent_parser import parse_intent


def test_examples_whatsapp_desktop():
	res = parse_intent('jao Ali ko whatsapp me msg kro "aj mujhe bukhar hai"')
	assert res["intent"] == "send_whatsapp"
	assert res["channel"] == "desktop"
	assert "bukhar" in res["message"].lower()


def test_examples_whatsapp_web():
	res = parse_intent('jao whatsapp web me ja ke Ali ko bolo "aj main Sialkot me miloonga"')
	assert res["intent"] == "send_whatsapp"
	assert res["channel"] == "web"


def test_system_shutdown():
	res = parse_intent("shutdown kr do mera pc")
	assert res["intent"] == "system_action"
	assert res["action"] == "shutdown"


def test_open_and_search():
	res = parse_intent("chrome kholo aur youtube pe coke studio search karo")
	assert res["intent"] in ("open_app", "search_web")
