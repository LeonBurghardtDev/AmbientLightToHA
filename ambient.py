import cv2
import numpy as np
import requests
import time
import os
import traceback
import subprocess

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

def start_pipewire_capture(width=1280, height=800):
    cmd = [
        "ffmpeg",
        "-f", "pipewire",
        "-i", "0",
        "-pix_fmt", "bgr0",
        "-vcodec", "rawvideo",
        "-an", "-sn",
        "-f", "rawvideo",
        "-"
    ]
    try:
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL), width, height
    except Exception:
        return None, width, height

def grab_grim():
    try:
        result = subprocess.run(["grim", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
        img_data = np.frombuffer(result.stdout, np.uint8)
        frame = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
        return frame
    except Exception:
        log("Error using grim:\n" + traceback.format_exc())
        return None

ffmpeg_proc, frame_width, frame_height = start_pipewire_capture()
use_grim = False

last_sent = 0
while True:
    frame = None

    if not use_grim and ffmpeg_proc:
        raw_frame = ffmpeg_proc.stdout.read(frame_width * frame_height * 4)
        if raw_frame:
            try:
                frame = np.frombuffer(raw_frame, np.uint8).reshape((frame_height, frame_width, 4))
                frame = frame[:, :, :3]
            except Exception:
                log("Error reshaping pipewire frame:\n" + traceback.format_exc())
        else:
            log("No frame received from pipewire, switching to grim fallback")
            use_grim = True

    if use_grim:
        frame = grab_grim()

    if frame is None:
        time.sleep(1)
        continue

    b, g, r = get_average_color(frame)

    if time.time() - last_sent > 1:
        send_to_ha(r, g, b)
        last_sent = time.time()
        log(f"Send: R={r}, G={g}, B={b}")
