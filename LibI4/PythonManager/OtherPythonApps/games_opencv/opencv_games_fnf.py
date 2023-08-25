import cv2
import threading
import numpy as np
import os
import subprocess
import sys
import keyboard
import time
import opencv_games_general as games

def press_key(key: str, delay: int = 0) -> None:
    kd = subprocess.run(["xdotool", "key", "--delay", str(delay), "--repeat", "1", key], capture_output = True).returncode
    
    if (kd == 0):
        return
    
    time.sleep(delay / 1000)
    keyboard.press_and_release(key.lower())

def run() -> None:
    global run_loop, arrow_templates, loaded_arrow_templates, loaded_neg_templates, monitor, threshold, scale_factor, h2
    
    w1 = 10
    h1 = 12
    fgbg = cv2.createBackgroundSubtractorMOG2()
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    
    while run_loop:
        screen = games.screenshot(monitor)
        screen = cv2.cvtColor(screen, cv2.COLOR_RGBA2BGRA)
        screen = screen[
            int(games.monitors_data[monitor]["height"] / h1):int(games.monitors_data[monitor]["height"] / h2),
            int(games.monitors_data[monitor]["width"] / 2):int(games.monitors_data[monitor]["width"] - games.monitors_data[monitor]["width"] / w1)
        ]
        gray_screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2GRAY)
        
        arrow_name = ""
        detected_arrows = []
        
        fgmask = fgbg.apply(gray_screen)
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)

        for i, arrow_template in enumerate(loaded_arrow_templates):
            arrow_name = list(arrow_templates.values())[i]
            
            at = cv2.cvtColor(arrow_template, cv2.COLOR_BGRA2GRAY)
            at = cv2.resize(at, None, fx = scale_factor, fy = scale_factor)
            
            result = cv2.matchTemplate(fgmask, at, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= threshold)
            locations = zip(*locations[::-1])

            for loc in locations:
                top_left = loc
                bottom_right = (loc[0] + at.shape[1], loc[1] + at.shape[0])
                
                if (detected_arrows.count(arrow_name) > 15):
                    continue
                
                print("Detected arrow '" + arrow_name + "' at " + str(top_left))
                threading.Thread(target = press_key, args = [arrow_name]).start()
                
                detected_arrows.append(arrow_name)
                cv2.rectangle(screen, top_left, bottom_right, (0, 255, 0), 2)
        
        cv2.imshow("Arrows", fgmask)
        
        if (cv2.waitKey(10) == 27):
            run_loop = False
    
    cv2.destroyAllWindows()

arrows_dir_name = "opencv_fnf_arrows"
pos_dir_name = "p"
neg_dir_name = "n"

arrow_templates = {}
loaded_arrow_templates = []
loaded_neg_templates = []

monitor = -1
threshold = 0.74
h2 = 3
scale_factor = 1

if (len(sys.argv) >= 2):
    try:
        monitor = int(sys.argv[1])
    except:
        monitor = -1
    
if (len(sys.argv) >= 3):
    arrows_dir_name = sys.argv[2]

if (len(sys.argv) >= 4):
    try:
        threshold = float(sys.argv[3])
    except:
        threshold = 0.74

if (len(sys.argv) >= 5):
    try:
        h2 = float(sys.argv[4])
    except:
        h2 = 3

if (len(sys.argv) >= 6):
    try:
        scale_factor = float(sys.argv[5])
    except:
        scale_factor = 1

arrows_dir_name = arrows_dir_name + "/"
pos_dir_name = pos_dir_name + "/"
neg_dir_name = neg_dir_name + "/"

for file in os.listdir(arrows_dir_name + pos_dir_name):
    name = ""
    
    if (file.lower().__contains__("down")):
        name = "Down"
    elif (file.lower().__contains__("up")):
        name = "Up"
    elif (file.lower().__contains__("left")):
        name = "Left"
    elif (file.lower().__contains__("right")):
        name = "Right"
    else:
        print("Unable to identify arrow '" + arrows_dir_name + pos_dir_name + file + "'")
        continue
    
    arrow_templates[arrows_dir_name + pos_dir_name + file] = name

for arrow in arrow_templates:
    loaded_arrow_templates.append(cv2.imread(arrow, cv2.IMREAD_UNCHANGED))

for file in os.listdir(arrows_dir_name + neg_dir_name):
    loaded_neg_templates.append(cv2.imread(arrows_dir_name + neg_dir_name + file, cv2.IMREAD_UNCHANGED))

run_loop = True
threading.Thread(target = run).start()

input()
run_loop = False