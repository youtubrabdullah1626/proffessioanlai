import os
from don.first_launch import ensure_first_launch


def test_paths_json_created(tmp_path, monkeypatch):
	monkeypatch.chdir(tmp_path)
	availability = ensure_first_launch()
	assert (tmp_path / "config" / "paths.json").exists()
