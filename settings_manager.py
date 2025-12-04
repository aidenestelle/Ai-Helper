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
    "sessions": {},
    "setup_complete": False,
    # TTS Settings
    "tts_enabled": False,
    "tts_voice": "jenny",  # Voice name (jenny, guy, aria, etc.)
    "tts_speed": 1.25  # Speech speed multiplier (0.5 to 2.0)
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    
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
            if "setup_complete" not in settings:
                # Existing users who have settings already should not see first-run
                settings["setup_complete"] = True
                save_settings(settings)
            # TTS settings
            if "tts_enabled" not in settings:
                settings["tts_enabled"] = False
            if "tts_voice" not in settings:
                settings["tts_voice"] = "jenny"
            if "tts_speed" not in settings:
                settings["tts_speed"] = 1.25
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

def is_first_run():
    """Check if this is the first time running the app."""
    return not load_settings().get("setup_complete", False)

def set_setup_complete(complete=True):
    """Mark initial setup as complete."""
    settings = load_settings()
    settings["setup_complete"] = complete
    save_settings(settings)

# TTS Settings
def get_tts_enabled():
    return load_settings().get("tts_enabled", False)

def set_tts_enabled(enabled):
    settings = load_settings()
    settings["tts_enabled"] = enabled
    save_settings(settings)

def get_tts_voice():
    return load_settings().get("tts_voice", "jenny")

def set_tts_voice(voice):
    settings = load_settings()
    settings["tts_voice"] = voice
    save_settings(settings)

def get_tts_speed():
    return load_settings().get("tts_speed", 1.25)

def set_tts_speed(speed):
    settings = load_settings()
    settings["tts_speed"] = speed
    save_settings(settings)
