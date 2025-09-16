import cv2
import numpy as np
import requests
import time
import mss
import os
import traceback

HA_URL = os.environ.get("HA_URL")
HA_TOKEN = os.environ.get("HA_TOKEN")

if not HA_URL or not HA_TOKEN:
    raise ValueError("Bitte HA_URL und HA_TOKEN als Umgebungsvariablen setzen.")

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
        log("Fehler beim Senden:\n" + traceback.format_exc())

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

def get_screen():
    while True:
        try:
            sct = mss.mss()
            monitor = sct.monitors[1] 
            log("Display gefunden")
            return sct, monitor
        except Exception:
            log("Kein Display:\n" + traceback.format_exc())
            time.sleep(5)

sct, monitor = get_screen()

last_sent = 0
while True:
    try:
        screenshot = np.array(sct.grab(monitor))
        frame = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
    except Exception:
        log("Fehler beim Grabben:\n" + traceback.format_exc())
        sct, monitor = get_screen()
        continue

    b, g, r = get_average_color(frame)

    if time.time() - last_sent > 1:
        send_to_ha(r, g, b)
        last_sent = time.time()
        log(f"Gesendet: R={r}, G={g}, B={b}")
