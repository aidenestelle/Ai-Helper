import keyboard
import config
import settings_manager
from overlay_app import OverlayApp

def main():
    # Load initial hotkey
    current_hotkey = settings_manager.get_hotkey()

    def update_hotkey(new_hotkey):
        nonlocal current_hotkey
        try:
            keyboard.remove_hotkey(current_hotkey)
        except Exception:
            pass
        
        try:
            keyboard.add_hotkey(new_hotkey, toggle_overlay)
            current_hotkey = new_hotkey
            print(f"Hotkey updated to: {new_hotkey}")
        except Exception as e:
            print(f"Error updating hotkey: {e}")

    app = OverlayApp(update_hotkey_callback=update_hotkey)

    def toggle_overlay():
        if app.is_visible:
            # Schedule hide on main thread
            app.after(0, app.hide_overlay)
        else:
            # Schedule show on main thread
            app.after(0, app.show_overlay)

    # Register initial hotkey
    try:
        keyboard.add_hotkey(current_hotkey, toggle_overlay)
        print(f"Overlay tool running. Press {current_hotkey} to toggle.")
    except ImportError:
        print("Error: 'keyboard' module requires root/admin privileges on some systems.")
    except Exception as e:
        print(f"Error registering hotkey: {e}")

    # Run the application
    app.mainloop()

if __name__ == "__main__":
    main()
