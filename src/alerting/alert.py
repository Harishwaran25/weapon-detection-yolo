"""
Multi-Channel Security Alert Pipeline for Crime Detection Surveillance
-----------------------------------------------------------------------
Handles alert dispatching with cooldown management, local structured JSON
and log auditing, webhook notifications (Slack/Discord/Custom API), and
sound triggers.

On Raspberry Pi edge deployments, this can also drive a physical GPIO
buzzer/siren directly (see GPIO_BUZZER_PIN below). RPi.GPIO is imported
lazily and only on devices that have it, so this module still runs fine
on the CUDA training/dev machine.
"""

import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import RPi.GPIO as GPIO
    _GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    # ImportError: not on a Pi / library not installed.
    # RuntimeError: RPi.GPIO imported on non-Pi hardware.
    GPIO = None
    _GPIO_AVAILABLE = False


class AlertManager:
    def __init__(
        self,
        cooldown_seconds: float = 5.0,
        log_path: str = "outputs/alerts.log",
        json_log_path: str = "outputs/alerts.json",
        webhook_url: Optional[str] = None,
        gpio_buzzer_pin: Optional[int] = None,
        buzzer_duration: float = 1.5,
    ):
        self.cooldown_seconds = cooldown_seconds
        self._last_alert_time = 0.0
        self.log_path = Path(log_path)
        self.json_log_path = Path(json_log_path)
        self.webhook_url = webhook_url or os.getenv("SURVEILLANCE_WEBHOOK_URL")

        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # GPIO buzzer setup (Raspberry Pi edge deployment only).
        # Pin defaults to BCM 17, matching the wiring in docs/hardware-setup.md.
        env_pin = os.getenv("SURVEILLANCE_BUZZER_PIN")
        self.gpio_buzzer_pin = gpio_buzzer_pin if gpio_buzzer_pin is not None else (
            int(env_pin) if env_pin else None
        )
        self.buzzer_duration = buzzer_duration
        self._gpio_ready = False

        if self.gpio_buzzer_pin is not None:
            if _GPIO_AVAILABLE:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.gpio_buzzer_pin, GPIO.OUT)
                GPIO.output(self.gpio_buzzer_pin, GPIO.LOW)
                self._gpio_ready = True
            else:
                print(
                    "⚠️ gpio_buzzer_pin was set but RPi.GPIO is not available "
                    "on this device — buzzer alerts will be skipped."
                )

    def trigger(
        self,
        snapshot_path: str,
        threat_class: str = "weapon",
        confidence: float = 0.92,
        camera_id: str = "CAM_01_ENTRANCE",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Trigger an alert if not within cooldown period."""
        now = time.time()
        if now - self._last_alert_time < self.cooldown_seconds:
            return  # Cooldown active, skip duplicate alert

        self._last_alert_time = now
        self._dispatch(
            snapshot_path=snapshot_path,
            timestamp=now,
            threat_class=threat_class,
            confidence=confidence,
            camera_id=camera_id,
            metadata=metadata or {},
        )

    def _dispatch(
        self,
        snapshot_path: str,
        timestamp: float,
        threat_class: str,
        confidence: float,
        camera_id: str,
        metadata: Dict[str, Any],
    ):
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        alert_payload = {
            "event_id": f"ALT-{int(timestamp*1000)}",
            "timestamp": time_str,
            "epoch": timestamp,
            "camera_id": camera_id,
            "threat_class": threat_class,
            "confidence": round(confidence, 4),
            "snapshot_path": snapshot_path,
            "severity": "CRITICAL" if threat_class in ["gun", "heavy-weapon"] else "HIGH",
            "metadata": metadata,
        }

        # 1. Console Output
        print(f"🚨 [CRITICAL ALERT] [{time_str}] Threat '{threat_class}' ({confidence*100:.1f}%) "
              f"on {camera_id} — Snapshot: {snapshot_path}")

        # 2. Append to plain log file
        log_line = f"[{time_str}] [SEVERITY: {alert_payload['severity']}] Camera: {camera_id} | Class: {threat_class} ({confidence:.2f}) | File: {snapshot_path}\n"
        with open(self.log_path, "a") as f:
            f.write(log_line)

        # 3. Append to JSON log for Dashboard integration
        self._append_json(alert_payload)

        # 4. Optional Webhook Dispatch
        if self.webhook_url:
            self._send_webhook(alert_payload)

        # 5. Optional GPIO Buzzer (Raspberry Pi edge nodes)
        if self._gpio_ready:
            self._trigger_buzzer()

    def _append_json(self, payload: Dict[str, Any]):
        alerts = []
        if self.json_log_path.exists():
            try:
                with open(self.json_log_path, "r") as f:
                    alerts = json.load(f)
            except Exception:
                alerts = []
        alerts.append(payload)
        with open(self.json_log_path, "w") as f:
            json.dump(alerts, f, indent=2)

    def _send_webhook(self, payload: Dict[str, Any]):
        try:
            import urllib.request
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                print(f"📡 Webhook sent to {self.webhook_url} (HTTP {resp.status})")
        except Exception as e:
            print(f"⚠️ Webhook dispatch failed: {e}")

    def _trigger_buzzer(self):
        """Pulse the GPIO buzzer for self.buzzer_duration seconds."""
        try:
            GPIO.output(self.gpio_buzzer_pin, GPIO.HIGH)
            time.sleep(self.buzzer_duration)
            GPIO.output(self.gpio_buzzer_pin, GPIO.LOW)
        except Exception as e:
            print(f"⚠️ GPIO buzzer trigger failed: {e}")

    def cleanup(self):
        """Release GPIO resources. Call on shutdown (e.g. in a finally block)."""
        if self._gpio_ready:
            GPIO.cleanup(self.gpio_buzzer_pin)
