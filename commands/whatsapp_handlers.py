from don.whatsapp_automation import WhatsAppAutomation
from don.config import load_settings


def send_text(contact: str, message: str, prefer_web: bool = False) -> bool:
	settings = load_settings()
	wa = WhatsAppAutomation(settings)
	return wa.send_text(contact, message, prefer_web)
