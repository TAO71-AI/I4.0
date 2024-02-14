import cv2
import os
import sys
import time

fgbg = cv2.createBackgroundSubtractorMOG2()
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

def convert_to_binary(images: dict) -> dict:
    global fgbg, kernel
    b_imgs = {}
    
    for i in images:
        img_name = i
        img = images[i]
        
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
        fgmask = fgbg.apply(img)
        fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
        
        b_imgs[img_name] = fgmask
        
        cv2.imshow(img_name, fgmask)
        cv2.waitKey(10)
    
    return b_imgs

imgs = {}

for i, img_name in enumerate(sys.argv):
    if (i == 0 or not os.path.exists(img_name)):
        continue
    
    img = cv2.imread(img_name, cv2.IMREAD_UNCHANGED)
    imgs[img_name] = img

b_imgs = convert_to_binary(imgs)

for b_img in b_imgs:
    img_name: str = b_img
    img = imgs[img_name]
    
    img_l_n = img_name[img_name.rfind("."):len(img_name)]
    img_name = img_name[0:img_name.rfind(".")]
    
    cv2.imwrite(img_name + "_bin" + img_l_n, img)