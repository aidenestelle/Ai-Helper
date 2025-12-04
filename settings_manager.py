import json
import os
import config
import uuid
import time

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "hotkey": config.HOTKEY,
    "webhook_url": config.WEBHOOK_URL,
    "include_screenshot": True,
    "selected_monitor": 1,
    "voice_mode": "toggle",  # "toggle" or "push_to_talk"
    "voice_hotkey": "ctrl+shift+v",
    "sessions": {}
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    
    try:
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
            # Ensure keys exist
            if "hotkey" not in settings:
                settings["hotkey"] = config.HOTKEY
            if "webhook_url" not in settings:
                settings["webhook_url"] = config.WEBHOOK_URL
            if "include_screenshot" not in settings:
                settings["include_screenshot"] = True
            if "selected_monitor" not in settings:
                settings["selected_monitor"] = 1
            if "voice_mode" not in settings:
                settings["voice_mode"] = "toggle"
            if "voice_hotkey" not in settings:
                settings["voice_hotkey"] = "ctrl+shift+v"
            if "sessions" not in settings:
                settings["sessions"] = {}
            return settings
    except Exception as e:
        print(f"Error loading settings: {e}")
        return DEFAULT_SETTINGS

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")

def create_session():
    session_id = str(uuid.uuid4())
    settings = load_settings()
    settings["sessions"][session_id] = {
        "id": session_id,
        "title": "New Chat",
        "timestamp": time.time(),
        "messages": []
    }
    save_settings(settings)
    return session_id

def save_interaction(session_id, query, response):
    settings = load_settings()
    if session_id not in settings["sessions"]:
        # Should not happen if flow is correct, but safe fallback
        settings["sessions"][session_id] = {
            "id": session_id,
            "title": query[:30] + "...",
            "timestamp": time.time(),
            "messages": []
        }
    
    session = settings["sessions"][session_id]
    
    # Update title if it's the first real message
    if len(session["messages"]) == 0 or session["title"] == "New Chat":
        session["title"] = query[:30] + "..."
        
    session["messages"].append({"role": "user", "content": query})
    session["messages"].append({"role": "assistant", "content": response})
    session["timestamp"] = time.time() # Update timestamp to move to top
    
    save_settings(settings)

def get_sessions():
    settings = load_settings()
    sessions = list(settings["sessions"].values())
    # Sort by timestamp descending
    sessions.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return sessions

def delete_session(session_id):
    settings = load_settings()
    if session_id in settings["sessions"]:
        del settings["sessions"][session_id]
        save_settings(settings)

def get_session_messages(session_id):
    settings = load_settings()
    return settings["sessions"].get(session_id, {}).get("messages", [])

def get_hotkey():
    return load_settings().get("hotkey", config.HOTKEY)

def set_hotkey(hotkey):
    settings = load_settings()
    settings["hotkey"] = hotkey
    save_settings(settings)

def get_webhook_url():
    return load_settings().get("webhook_url", config.WEBHOOK_URL)

def set_webhook_url(url):
    settings = load_settings()
    settings["webhook_url"] = url
    save_settings(settings)

def get_include_screenshot():
    return load_settings().get("include_screenshot", True)

def set_include_screenshot(value):
    settings = load_settings()
    settings["include_screenshot"] = value
    save_settings(settings)

def get_voice_mode():
    return load_settings().get("voice_mode", "toggle")

def set_voice_mode(mode):
    settings = load_settings()
    settings["voice_mode"] = mode
    save_settings(settings)

def get_voice_hotkey():
    return load_settings().get("voice_hotkey", "ctrl+shift+v")

def set_voice_hotkey(hotkey):
    settings = load_settings()
    settings["voice_hotkey"] = hotkey
    save_settings(settings)

def get_selected_monitor():
    return load_settings().get("selected_monitor", 1)

def set_selected_monitor(monitor):
    settings = load_settings()
    settings["selected_monitor"] = monitor
    save_settings(settings)
