from don.comms_ai import CommsAI
from don.config import load_settings


def test_comms_listen_and_respond(monkeypatch):
	settings = load_settings()
	ai = CommsAI(settings)

	class DummySTT:
		def listen_once(self, *args, **kwargs):
			return "open chrome and search nexhan"

	ai.stt = DummySTT()
	ai.listen_and_respond()
	# No assertion; ensure method runs without exception
