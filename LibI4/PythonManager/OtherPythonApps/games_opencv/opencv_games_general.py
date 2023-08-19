import numpy as np
from PIL import ImageGrab
from screeninfo import get_monitors
import pyautogui

monitors = get_monitors()
monitors_data: dict[int, dict[str, int]] = {}
monitors_data[-1] = {
    "x": 0,
    "y": 0,
    "width": 0,
    "height": 0
}

for monitor in monitors:
    mon_info = {
        "x": monitor.x,
        "y": monitor.y,
        "width": monitor.width,
        "height": monitor.height
    }
    monitors_data[monitors.index(monitor)] = mon_info
    
    monitors_data[-1]["width"] += mon_info["width"]
    monitors_data[-1]["height"] += mon_info["height"]

def screenshot(monitor: int = -1, print_used = False):
    data = None
    
    if (monitor < 0 or monitor >= len(monitors_data)):
        try:
            data = ImageGrab.grab()
            
            if (print_used):
                print("Using PIL screenshot.")
        except:
            data = pyautogui.screenshot()
            
            if (print_used):
                print("Using PyAutoGui screenshot.")
    else:
        mon = monitors_data[monitor]
        
        try:
            data = ImageGrab.grab(bbox = (mon["x"], mon["y"], mon["x"] + mon["width"], mon["y"] + mon["height"]))
            
            if (print_used):
                print("Using PIL screenshot.")
        except:
            data = pyautogui.screenshot(region = (mon["x"], mon["y"], mon["x"] + mon["width"], mon["y"] + mon["height"]))
            
            if (print_used):
                print("Using PyAutoGui screenshot.")
    
    data = np.array(data)
    return data