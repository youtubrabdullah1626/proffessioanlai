from don.intent_parser import parse_intent


def test_open_chrome():
	res = parse_intent("Hey Don, chrome kholo")
	assert res["intent"] == "open_app"


def test_whatsapp_desktop():
	res = parse_intent("Don, jao Ali ko whatsapp pe msg karo k aj mujhe bukhar hai")
	assert res["intent"] == "send_whatsapp"
	assert res["channel"] == "desktop"


def test_whatsapp_web():
	res = parse_intent("Don, jao whatsapp web me ja ke Ali ko bolo 'aj main Sialkot me miloonga'")
	assert res["intent"] == "send_whatsapp"
	assert res["channel"] == "web"


def test_error_analysis():
	res = parse_intent("Don, ye error aa raha hai: chrome cannot start")
	assert res["intent"] == "error_analysis"


def test_schedule():
	res = parse_intent("Don, kal subah 8 baje uthana")
	assert res["intent"] in ("schedule", "unknown")
