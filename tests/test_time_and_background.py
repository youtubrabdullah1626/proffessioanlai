from datetime import datetime
from don.time_parse import parse_natural_time
from don.future_scaffold import BackgroundConversation


def test_time_parser_basic():
	now = datetime(2025, 10, 28, 7, 0, 0)
	z = parse_natural_time("kal subah 8 baje", now)
	assert z is not None


def test_background_start_stop():
	bg = BackgroundConversation()
	bg.start()
	bg.stop()
