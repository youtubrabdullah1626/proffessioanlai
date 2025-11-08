import os
from don.logging_utils import setup_logging
from don.memory_manager import load_m1, save_m1, init_m2, remember_nickname
from don.knowledge import web_search, explain_with_gemini


def test_logging_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    logger = setup_logging()
    logger.info("test line")
    assert (tmp_path / "logs" / "assistant.log").exists()


def test_memory_m1_m2(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert save_m1({"nicknames": {}, "preferred_whatsapp_channel": "desktop", "last_tone": "friendly"})
    m1 = load_m1()
    assert m1.get("preferred_whatsapp_channel") == "desktop"
    assert init_m2() is True
    assert remember_nickname("ali", "+923001234567") is True


def test_knowledge_helpers(monkeypatch):
    monkeypatch.setenv("SIMULATION_MODE", "true")
    assert web_search("Daska weather") is True
    assert isinstance(explain_with_gemini("extraordinary meaning"), str)
