import os
from typing import Dict, List

try:
    import winreg  # type: ignore
    has_winreg = True
except Exception:
    has_winreg = False

from .logging_utils import setup_logging

logger = setup_logging()


def _expand(paths: List[str]) -> List[str]:
    out: List[str] = []
    for p in paths:
        try:
            out.append(os.path.expandvars(p).replace("/", os.sep))
        except Exception:
            out.append(p)
    return out


def _dedupe_abs(paths: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for p in paths:
        try:
            q = os.path.abspath(os.path.expandvars(p))
            if q not in seen:
                seen.add(q)
                out.append(q)
        except Exception:
            continue
    return out


def scan_app_paths() -> Dict[str, List[str]]:
    """Scan common locations and (optionally) Windows registry to discover app executables."""
    apps: Dict[str, List[str]] = {
        "whatsapp": _expand([
            "%LOCALAPPDATA%/WhatsApp/WhatsApp.exe",
            "C:/Program Files/WhatsApp/WhatsApp.exe",
            "C:/Program Files (x86)/WhatsApp/WhatsApp.exe",
        ]),
        "chrome": _expand([
            "C:/Program Files/Google/Chrome/Application/chrome.exe",
            "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
            "%LOCALAPPDATA%/Google/Chrome/Application/chrome.exe",
        ]),
        "edge": _expand([
            "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
            "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
        ]),
    }

    # Best-effort registry scan for additional paths
    if has_winreg:
        try:
            for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                base = r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
                try:
                    with winreg.OpenKey(root, base) as key:
                        try:
                            count = winreg.QueryInfoKey(key)[0]
                        except Exception:
                            count = 0
                        for i in range(count):
                            try:
                                sub = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, sub) as sk:
                                    try:
                                        disp, _ = winreg.QueryValueEx(sk, "DisplayName")
                                        dicon, _ = winreg.QueryValueEx(sk, "DisplayIcon")
                                        name = str(disp).lower() if isinstance(disp, str) else ""
                                        path_val = str(dicon) if isinstance(dicon, str) else ""
                                        if name:
                                            if "whatsapp" in name:
                                                apps.setdefault("whatsapp", []).append(path_val)
                                            if "chrome" in name:
                                                apps.setdefault("chrome", []).append(path_val)
                                            if "edge" in name:
                                                apps.setdefault("edge", []).append(path_val)
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                except Exception:
                    pass
        except Exception:
            pass

    # Normalize and dedupe
    for k, v in list(apps.items()):
        apps[k] = _dedupe_abs(v)

    logger.info("System app paths scan complete.")
    return apps
