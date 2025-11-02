import os
import json
from typing import Dict, List

try:
    import winreg  # type: ignore
    HAS_WINREG = True
except Exception:
    HAS_WINREG = False
    winreg = None

from don.logging_utils import setup_logging

logger = setup_logging()


def _expand(paths: List[str]) -> List[str]:
    """Expand environment variables in paths."""
    out: List[str] = []
    for p in paths:
        try:
            out.append(os.path.expandvars(p).replace("/", os.sep))
        except Exception:
            out.append(p)
    return out


def _dedupe_abs(paths: List[str]) -> List[str]:
    """Remove duplicate absolute paths."""
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


def scan_program_files() -> Dict[str, List[str]]:
    """Scan Program Files directories for common applications."""
    apps: Dict[str, List[str]] = {}
    
    # Common Program Files locations
    program_files_paths = [
        os.environ.get("ProgramFiles", "C:\\Program Files"),
        os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", "C:\\Users\\%USERNAME%\\AppData\\Local")
    ]
    
    # Application-specific paths to look for
    app_search_paths = {
        "whatsapp": ["WhatsApp", "WhatsApp Desktop"],
        "chrome": ["Google\\Chrome", "Chrome"],
        "edge": ["Microsoft\\Edge", "Edge"],
        "firefox": ["Mozilla Firefox", "Firefox"],
        "vscode": ["Microsoft VS Code", "VS Code"],
        "notepad++": ["Notepad++"],
        "spotify": ["Spotify"],
        "steam": ["Steam"]
    }
    
    for app_name, search_paths in app_search_paths.items():
        app_paths = []
        for base_path in program_files_paths:
            for search_path in search_paths:
                # Check for executable files
                exe_paths = [
                    os.path.join(base_path, search_path, f"{app_name}.exe"),
                    os.path.join(base_path, search_path, "Application", f"{app_name}.exe"),
                    os.path.join(base_path, search_path, f"{app_name.capitalize()}.exe"),
                    os.path.join(base_path, search_path, "bin", f"{app_name}.exe")
                ]
                
                for exe_path in exe_paths:
                    expanded_path = os.path.expandvars(exe_path)
                    if os.path.isfile(expanded_path):
                        app_paths.append(expanded_path)
        
        if app_paths:
            apps[app_name] = _dedupe_abs(app_paths)
    
    return apps


def scan_appdata() -> Dict[str, List[str]]:
    """Scan AppData directories for common applications."""
    apps: Dict[str, List[str]] = {}
    
    # AppData locations
    appdata_paths = [
        os.environ.get("LOCALAPPDATA", "C:\\Users\\%USERNAME%\\AppData\\Local"),
        os.environ.get("APPDATA", "C:\\Users\\%USERNAME%\\AppData\\Roaming")
    ]
    
    # Application-specific AppData paths
    appdata_search_paths = {
        "whatsapp": ["WhatsApp"],
        "chrome": ["Google\\Chrome"],
        "edge": ["Microsoft\\Edge"],
        "vscode": ["Code"],
        "spotify": ["Spotify"]
    }
    
    for app_name, search_paths in appdata_search_paths.items():
        app_paths = []
        for base_path in appdata_paths:
            for search_path in search_paths:
                # Check for executable files
                exe_paths = [
                    os.path.join(base_path, search_path, f"{app_name}.exe"),
                    os.path.join(base_path, search_path, "Application", f"{app_name}.exe"),
                    os.path.join(base_path, search_path, "app", f"{app_name}.exe")
                ]
                
                for exe_path in exe_paths:
                    expanded_path = os.path.expandvars(exe_path)
                    if os.path.isfile(expanded_path):
                        app_paths.append(expanded_path)
        
        if app_paths:
            apps[app_name] = _dedupe_abs(app_paths)
    
    return apps


def scan_registry() -> Dict[str, List[str]]:
    """Scan Windows registry for installed applications."""
    apps: Dict[str, List[str]] = {}
    
    if not HAS_WINREG or winreg is None:
        logger.warning("Windows registry access not available")
        return apps
    
    # Registry keys to scan
    registry_keys = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
    ]
    
    # Application names to look for
    app_names = {
        "whatsapp": ["whatsapp", "whatsapp desktop"],
        "chrome": ["chrome", "google chrome"],
        "edge": ["edge", "microsoft edge"],
        "firefox": ["firefox", "mozilla firefox"],
        "vscode": ["vscode", "visual studio code"],
        "notepad++": ["notepad++"],
        "spotify": ["spotify"],
        "steam": ["steam"]
    }
    
    for root, base_key in registry_keys:
        try:
            with winreg.OpenKey(root, base_key) as key:
                try:
                    subkey_count = winreg.QueryInfoKey(key)[0]
                except Exception:
                    subkey_count = 0
                
                for i in range(subkey_count):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                # Get display name and install location
                                display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                                install_location, _ = winreg.QueryValueEx(subkey, "InstallLocation")
                                display_icon, _ = winreg.QueryValueEx(subkey, "DisplayIcon")
                                
                                # Check if this is one of our target applications
                                name_lower = str(display_name).lower() if display_name else ""
                                for app_key, keywords in app_names.items():
                                    if any(keyword in name_lower for keyword in keywords):
                                        # Try to find executable path
                                        exe_path = None
                                        if display_icon and ".exe" in display_icon:
                                            # Extract executable path from DisplayIcon
                                            exe_path = display_icon.split(",")[0] if "," in display_icon else display_icon
                                        elif install_location:
                                            # Try common executable names in install location
                                            common_exes = [f"{app_key}.exe", f"{app_key.capitalize()}.exe", "Application.exe"]
                                            for exe in common_exes:
                                                candidate = os.path.join(install_location, exe)
                                                if os.path.isfile(candidate):
                                                    exe_path = candidate
                                                    break
                                        
                                        if exe_path and os.path.isfile(exe_path):
                                            apps.setdefault(app_key, []).append(exe_path)
                            except FileNotFoundError:
                                # Some registry entries might not have these values
                                pass
                            except Exception:
                                # Continue with other registry entries
                                pass
                    except Exception:
                        # Continue with other subkeys
                        pass
        except Exception:
            # Continue with other registry keys
            pass
    
    return apps


def scan_system_apps() -> Dict[str, List[str]]:
    """
    Scan Program Files, AppData, and registry to build SYSTEM_APPS map.
    
    Returns:
        Dict mapping app names to lists of executable paths
    """
    logger.info("Starting system app scan...")
    
    # Start with default paths
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
    
    # Scan Program Files
    try:
        program_files_apps = scan_program_files()
        for app_name, paths in program_files_apps.items():
            if paths:
                apps.setdefault(app_name, []).extend(paths)
    except Exception as e:
        logger.warning(f"Program Files scan failed: {e}")
    
    # Scan AppData
    try:
        appdata_apps = scan_appdata()
        for app_name, paths in appdata_apps.items():
            if paths:
                apps.setdefault(app_name, []).extend(paths)
    except Exception as e:
        logger.warning(f"AppData scan failed: {e}")
    
    # Scan registry (fallback if other methods don't work well)
    try:
        registry_apps = scan_registry()
        for app_name, paths in registry_apps.items():
            if paths:
                apps.setdefault(app_name, []).extend(paths)
    except Exception as e:
        logger.warning(f"Registry scan failed: {e}")
    
    # Normalize and dedupe all paths
    for k, v in list(apps.items()):
        apps[k] = _dedupe_abs(v)
    
    logger.info("System app scan complete.")
    return apps


def save_system_apps_to_config(apps: Dict[str, List[str]], config_path: str = "config/paths.json") -> bool:
    """
    Save the SYSTEM_APPS map to config/paths.json.
    
    Args:
        apps: Dictionary mapping app names to executable paths
        config_path: Path to save the configuration file
        
    Returns:
        bool: True if successful
    """
    try:
        # Ensure config directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Save to JSON file
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(apps, f, indent=2)
        
        logger.info(f"Wrote app paths map: {config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save system apps to {config_path}: {e}")
        return False


def scan_and_save_system_apps(config_path: str = "config/paths.json") -> bool:
    """
    Scan for system apps and save to configuration file.
    
    Args:
        config_path: Path to save the configuration file
        
    Returns:
        bool: True if successful
    """
    try:
        # Scan for system apps
        apps = scan_system_apps()
        
        # Save to configuration file
        return save_system_apps_to_config(apps, config_path)
    except Exception as e:
        logger.error(f"Failed to scan and save system apps: {e}")
        return False