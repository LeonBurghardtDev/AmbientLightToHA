# Ambient Light To Home Assistant

This project captures the dominant color of your screen and sends it as a sensor to [Home Assistant](https://www.home-assistant.io/).  
You can then use this sensor to control LED lights (e.g., via `light.turn_on`) and create an Ambilight effect.

It works on any Python-compatible device, such as PCs, Raspberry Pis, or small servers.

---

## 🔧 Requirements

- Python 3.9+
- Install dependencies:
  ```bash
  pip install opencv-python numpy requests mss
  ```

---

## ⚙️ Setup

Before running the script, you need to set the following environment variables:

### Linux / macOS
```bash
export HA_URL="http://192.xxx.xxx.xx:8123/api/states/sensor.dominant_color"
export HA_TOKEN="LONG_LIVED_ACCESS_TOKEN"
```

### Windows (PowerShell)
```powershell
$env:HA_URL="http://192.xxx.xxx.xx:8123/api/states/sensor.dominant_color"
$env:HA_TOKEN="LONG_LIVED_ACCESS_TOKEN"
```

> 📝 To generate a **Long-Lived Access Token**, open your Home Assistant profile (bottom left in the HA UI), scroll down to **Long-Lived Access Tokens**, and create a new one.

---

## ▶️ Usage

Run the script with:

```bash
python ambilight.py
```

The script will:
- Take regular screenshots (~once per second, configurable),
- Calculate the dominant color (gray/black filtered out),
- Send the values to Home Assistant as `sensor.dominant_color`.

---

## 🏠 Home Assistant Integration

After the first run, a new sensor will appear in HA:

```
sensor.dominant_color
```

This sensor contains:
- **state** → `"R,G,B"` of the main color
- **attributes** → `r`, `g`, `b` as separate values

Example automation to control LEDs:

```yaml
alias: Ambilight LEDs
trigger:
  - platform: state
    entity_id: sensor.dominant_color
action:
  - service: light.turn_on
    target:
      entity_id: light.your_led_strip
    data:
      rgb_color: >
        {{ [
          state_attr('sensor.dominant_color', 'r'),
          state_attr('sensor.dominant_color', 'g'),
          state_attr('sensor.dominant_color', 'b')
        ] }}
      transition: 0.5
```

---

## 🔄 Autostart on Linux

To run the script automatically at system startup, you can create a **systemd service**.

1. Create a new service file:
   ```bash
   sudo nano /etc/systemd/system/ambilight.service
   ```

2. Insert the following content (adjust paths accordingly):
   ```ini
   [Unit]
   Description=Ambient Light Python Script
   After=network.target

   [Service]
   ExecStart=/usr/bin/python3 /path/to/your/ambilight.py
   WorkingDirectory=/path/to/your/project
   Environment="HA_URL=http://192.xxx.xxx.xx:8123/api/states/sensor.dominant_color"
   Environment="HA_TOKEN=LONG_LIVED_ACCESS_TOKEN"
   Restart=always
   User=yourusername

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable ambilight.service
   sudo systemctl start ambilight.service
   ```

4. Check the status:
   ```bash
   systemctl status ambilight.service
   ```

---

## 🎉 Example

Start a movie → the script detects the dominant screen color → your LED strips automatically follow the color ✨
