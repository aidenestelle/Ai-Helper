import mss
import mss.tools
from PIL import Image
import io

def get_monitors():
    """
    Returns a list of available monitors with their info.
    Returns: [(index, name, bounds), ...]
    """
    with mss.mss() as sct:
        monitors = []
        for i, mon in enumerate(sct.monitors):
            if i == 0:  # Skip "all monitors" entry
                continue
            name = f"Screen {i}"
            monitors.append({
                "index": i,
                "name": name,
                "left": mon["left"],
                "top": mon["top"],
                "width": mon["width"],
                "height": mon["height"]
            })
        return monitors

def capture_screen(monitor_index=1):
    """
    Captures the specified screen and returns it as a PIL Image.
    """
    with mss.mss() as sct:
        # Ensure valid monitor index
        if monitor_index < 1 or monitor_index >= len(sct.monitors):
            monitor_index = 1
        
        monitor = sct.monitors[monitor_index]
        sct_img = sct.grab(monitor)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        return img

def capture_screen_bytes(monitor_index=1):
    """
    Captures the screen and returns the image bytes (PNG format).
    """
    img = capture_screen(monitor_index)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

def get_monitor_bounds(monitor_index):
    """Get the bounds of a specific monitor."""
    with mss.mss() as sct:
        if monitor_index < 1 or monitor_index >= len(sct.monitors):
            return None
        mon = sct.monitors[monitor_index]
        return {
            "left": mon["left"],
            "top": mon["top"],
            "width": mon["width"],
            "height": mon["height"]
        }
