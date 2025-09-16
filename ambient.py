import cv2
import numpy as np
import requests
import time
import mss
import os

HA_URL = os.environ.get("HA_URL")
HA_TOKEN = os.environ.get("HA_TOKEN")

if not HA_URL or not HA_TOKEN:
    raise ValueError("Bitte HA_URL und HA_TOKEN als Umgebungsvariablen setzen.")

headers = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "content-type": "application/json",
}

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
    except Exception as e:
        print("Fehler beim Senden:", e)

def get_average_color(frame, min_saturation=40, boost=1.2):
    small = cv2.resize(frame, (160, 90))
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)

    mask = hsv[:, :, 1] > min_saturation
    if not np.any(mask):
        return (0, 0, 0)

    valid = small[mask]
    avg = valid.mean(axis=0)
    avg = np.clip(avg * boost, 0, 255)

    return tuple(map(int, avg))  # (B, G, R)

sct = mss.mss()
monitor = sct.monitors[1]  # 1 = Hauptmonitor

last_sent = 0
while True:
    screenshot = np.array(sct.grab(monitor))
    frame = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

    b, g, r = get_average_color(frame)

    if time.time() - last_sent > 1:
        send_to_ha(r, g, b)
        last_sent = time.time()
        print("Gesendet:", r, g, b)

    cv2.imshow("Frame", cv2.resize(frame, (640, 360)))
    color_preview = np.zeros((100, 100, 3), np.uint8)
    color_preview[:] = (b, g, r)
    cv2.imshow("Ambilight Color", color_preview)

    if cv2.waitKey(1) == 27:
        break

cv2.destroyAllWindows()
