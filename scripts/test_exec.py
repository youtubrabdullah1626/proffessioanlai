import os
os.environ.setdefault("SIMULATION_MODE", "true")

from don.app_control import open_app

print("open chrome:", open_app("chrome"))
print("open whatsapp:", open_app("whatsapp"))
