# Nexhan Nova (Don)

Windows 10 desktop AI assistant with voice control, automation, and WhatsApp integration.

## Quick start
```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python main.py
```

## Structure (target)
- main.py, run_jarvis.py
- config/ (settings.json, paths.json)
- commands/ (whatsapp_handlers, system_control, app_control, file_manager, browser_tasks)
- core/ (listener, speaker, intent_engine, memory, executor)
- utils/ (scanner, logger, helpers)
- data/ (memory.json, memory.db at runtime)
- logs/ (assistant.log at runtime)
- assets/sounds/

## Notes
- SIMULATION_MODE defaults to true; set CONFIRM=yes for destructive ops.
- WhatsApp Desktop preferred; Chrome Web fallback uses user profile.
