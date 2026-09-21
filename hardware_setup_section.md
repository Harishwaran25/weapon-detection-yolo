## 🔌 Raspberry Pi Hardware Setup & Wiring

Edge deployment target: **Raspberry Pi 4** (USB-C power) running `src/detect_tflite.py`.

### Camera Module (CSI ribbon)

1. Power off the Pi.
2. Lift the CSI connector's plastic clip (between the USB and HDMI ports), insert the ribbon cable with the blue side facing the USB/Ethernet ports, and push the clip back down.
3. Enable the interface: `sudo raspi-config` → **Interface Options → Camera → Enable**, then reboot.
4. Verify: `libcamera-hello --timeout 2000` should show a live preview.

### GPIO Buzzer (physical alert siren)

| Buzzer Pin | Pi 4 Physical Pin | BCM GPIO |
| :--- | :---: | :---: |
| Signal / + | Pin 11 | GPIO17 |
| GND / − | Pin 9 | GND |

- Small piezo buzzers (<20mA) can be wired directly to GPIO17 as shown.
- Louder 5V siren modules should **not** be powered directly from the GPIO pin — drive them through an NPN transistor (e.g. 2N2222) switched by GPIO17, with the buzzer itself powered from the Pi's 5V rail (Pin 2).

**Power:** official Pi 4 USB-C supply (5V/3A). Under-powering is the most common cause of camera dropouts / random reboots during inference — avoid sharing the supply with other high-draw USB peripherals.

### Software integration method

The buzzer is wired directly into the existing alert pipeline in `alerting/alert.py` — no separate script needed:

```bash
pip install RPi.GPIO
```

`AlertManager` now accepts a `gpio_buzzer_pin` argument (defaults to `None`, i.e. no-op on non-Pi machines). `src/detect_tflite.py` passes `gpio_buzzer_pin=17`, so every threat alert that fires the console/log/JSON/webhook pipeline also pulses the physical buzzer for ~1.5s. RPi.GPIO is imported lazily, so `alert.py` still runs unmodified on the CUDA training/dev machine — the buzzer step is simply skipped there.

You can override the pin without touching code:
```bash
export SURVEILLANCE_BUZZER_PIN=17
```
