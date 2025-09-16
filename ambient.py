import cv2
import numpy as np
import requests
import time
import os
import traceback
from PIL import ImageGrab  

HA_URL = os.environ.get("HA_URL")
HA_TOKEN = os.environ.get("HA_TOKEN")

if not HA_URL or not HA_TOKEN:
    raise ValueError("HA_URL or HA_TOKEN not set.")

headers = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "content-type": "application/json",
}

LOGFILE = "ambient.log"

def log(msg):
    with open(LOGFILE, "a") as f:
        f.write(time.strftime("[%Y-%m-%d %H:%M:%S] ") + str(msg) + "\n")

def send_to_ha(r, g, b):
    data = {
        "state": f"{r},{g},{b}",
        "attributes": {
            "friendly_name": "Ambilight Color",
            "r": r,
            "g": g,
            "b": b
        }
    }
    try:
        requests.post(HA_URL, headers=headers, json=data, timeout=2)
    except Exception:
        log("Error sending data:\n" + traceback.format_exc())

def get_average_color(frame, min_saturation=40, boost=1.2):
    small = cv2.resize(frame, (160, 90))
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)

    mask = hsv[:, :, 1] > min_saturation
    if not np.any(mask):
        return (0, 0, 0)

    valid = small[mask]
    avg = valid.mean(axis=0)
    avg = np.clip(avg * boost, 0, 255)

    return tuple(map(int, avg)) 

def grab_frame():
    try:
        img = ImageGrab.grab() 
        frame = np.array(img)[:, :, ::-1] 
        return frame
    except Exception:
        log("Error creating Screenshot:\n" + traceback.format_exc())
        return None

last_sent = 0
while True:
    frame = grab_frame()
    if frame is None:
        time.sleep(2)
        continue

    b, g, r = get_average_color(frame)

    if time.time() - last_sent > 1:
        send_to_ha(r, g, b)
        last_sent = time.time()
        log(f"Send: R={r}, G={g}, B={b}")
