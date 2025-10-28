import os
from don.file_control import create_file, move_path, rename_path, delete_path, search_files, read_small_file, summarize_text


def test_file_ops_simulation(tmp_path, monkeypatch):
	monkeypatch.setenv("SIMULATION_MODE", "true")
	p = str(tmp_path / "a.txt")
	assert create_file(p, "hello")
	assert move_path(p, str(tmp_path / "b.txt"))
	assert rename_path(str(tmp_path / "b.txt"), "c.txt")
	assert delete_path(str(tmp_path / "c.txt"))


def test_search_and_read(tmp_path):
	# real FS ops for search/read
	p = tmp_path / "note.txt"
	p.write_text("This is a small file for summary.", encoding="utf-8")
	found = search_files(str(tmp_path), "note")
	assert str(p) in found
	content = read_small_file(str(p))
	assert content and "small file" in content
	summary = summarize_text(content, 20)
	assert len(summary) <= 40
