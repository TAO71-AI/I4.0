import numpy as np
from PIL import ImageGrab
from screeninfo import get_monitors
import pyautogui
import cv2
import os
import time
import subprocess
import keyboard

monitors = get_monitors()
monitors_data: dict[int, dict[str, int]] = {}
monitors_data[-1] = {
    "x": 0,
    "y": 0,
    "width": 0,
    "height": 0
}
__keys_pressed__: list[str] = []

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

def RecognizeTextFromImage(image) -> str:
    if (not os.path.exists("opencv_keys")):
        os.mkdir("opencv_keys")
    
    dir = os.listdir("opencv_keys")
    templates = []
    templates_names = []
    text = ""
    special_characters = {
        "dot": ".",
        "at": "@",
        "hashtag": "#",
        "left click": "[LC]",
        "right click": "[RC]",
        "mouse position": "[POS]",
        "space": " "
    }

    for f in dir:
        if (os.path.isfile("opencv_keys/" + f)):
            templates.append(cv2.imread("opencv_keys/" + f, cv2.IMREAD_GRAYSCALE))
            templates_names.append(f[0:f.index(".")])
    
    for i, template in enumerate(templates):
        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.75
        loc = np.where(result >= threshold)

        for pt in zip(*loc[::-1]):
            try:
                text += special_characters[templates_names[i]]
            except:
                text += templates_names[i]
    
    return text

def PressKey(key: str, delay: int = 0) -> None:
    kd = subprocess.run(["xdotool", "key", "--delay", str(delay), "--repeat", "1", key], capture_output = True).returncode
    
    if (kd == 0):
        return
    
    time.sleep(delay / 1000)
    keyboard.press_and_release(key.lower())

def __on_press_key__(e) -> None:
    __keys_pressed__.append(e.name)

def ShowKeysPressed(available_keys: list[str]):
    for _ in available_keys:
        keyboard.hook(__on_press_key__)

def TrainAIByGameplay(gameplay_path: str, keys_area: tuple[int, int]) -> dict[int, str]:
    gameplay_data = {}
    cap = cv2.VideoCapture(gameplay_path)

    if (not cap.isOpened()):
        raise Exception("Error opening the gameplay.")
    
    frame_count = 0

    while (True):
        ret, frame = cap.read()
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if (not ret):
            break

        gray_frame = gray_frame[0:keys_area[1], 0:keys_area[0]]
        text_recognized = RecognizeTextFromImage(gray_frame)

        gameplay_data[str(cap.get(cv2.CAP_PROP_POS_MSEC))] = text_recognized
        frame_count += 1
    
    cap.release()

def PlayAIFromTrainData(train_data: dict[int, str]) -> None:
    ms = 0

    while (True):
        if (ms > len(train_data)):
            break

        try:
            keys = train_data[ms]

            for key in keys:
                PressKey(key)
        except:
            pass

        ms += 1