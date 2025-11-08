from don.config import load_settings
from don.whatsapp_automation import WhatsAppAutomation


def test_whatsapp_send_simulation(monkeypatch, tmp_path):
    monkeypatch.setenv("SIMULATION_MODE", "true")
    settings = load_settings()
    wa = WhatsAppAutomation(settings)
    assert wa.send_text("Ali", "Test message")
    f = tmp_path / "img.png"
    f.write_bytes(b"fake")
    assert wa.send_media("Ali", str(f), "image")
    assert wa.toggle_auto_reply(True)
    assert wa.summarize_chat_aloud("Ali")
