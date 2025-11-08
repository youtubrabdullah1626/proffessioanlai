import os
from don.first_launch import ensure_first_launch


def test_first_launch_creates_dirs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    availability = ensure_first_launch()
    for d in ["logs", "data", "memory"]:
        assert (tmp_path / d).exists()
    assert (tmp_path / "memory" / "memory.json").exists()
    assert (tmp_path / "memory" / "memory.db").exists()
    assert (tmp_path / "data" / "system_apps.json").exists()
    assert isinstance(availability, dict)
