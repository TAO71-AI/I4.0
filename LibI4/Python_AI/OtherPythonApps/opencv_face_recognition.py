import cv2
import sys
import threading
import time

def recognize(delay: int = 10, draw_rectangle: bool = True) -> dict:
    global cascade, vid
    
    (_, im) = vid.read()
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray)
    faces_list = {}
    i = 0
    
    for (x, y, w, h) in faces:
        faces_list["face_" + str(i)] = [x, y, w, h, x + w, y + h]
        
        if (draw_rectangle):
            cv2.rectangle(im, (x, y), (x + w, y + h), (255, 0, 0), 2)
        
        i += 1

    if (draw_rectangle):
        cv2.imshow("OpenCV", im)
        
    faces_list["key"] = cv2.waitKey(delay)
    return faces_list

def wait_and_stop() -> None:
    global time_w, read
    
    time.sleep(time_w)
    read = False

file_name = sys.argv[1]
cascade = cv2.CascadeClassifier(file_name)
vid = cv2.VideoCapture(0)
dr = True
read = True
time_w = 5
data = ""

if (len(sys.argv) > 1):
    if (sys.argv[1] == "-nr"):
        dr = False

t = threading.Thread(target = wait_and_stop)
t.start()

while read:
    data = recognize(10, dr)

try:
    print(str(data["face_0"][0]) + " " + str(data["face_0"][1]) + " " + str(data["face_0"][2]) + " " + str(data["face_0"][3]))
except:
    print(str(data))