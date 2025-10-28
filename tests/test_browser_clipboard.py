from don.browser_control import google_search, youtube_search
from don.config import load_settings
from don.clipboard import ClipboardHistory


def test_google_youtube_simulation(monkeypatch):
	# Force simulation mode during test
	monkeypatch.setenv("SIMULATION_MODE", "true")
	settings = load_settings()
	assert google_search(settings, "don assistant test") is True
	assert youtube_search(settings, "nexhan nova demo") is True


def test_clipboard_history_add_last(tmp_path):
	mini = tmp_path / "clip.log"
	h = ClipboardHistory(max_items=2, mini_log_path=str(mini))
	h.add("first")
	h.add("second")
	h.add("third")
	assert h.last() == "third"
	assert len(h.items) == 2
	assert mini.exists()
