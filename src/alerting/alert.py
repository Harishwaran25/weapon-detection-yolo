"""
Multi-Channel Security Alert Pipeline for Crime Detection Surveillance
-----------------------------------------------------------------------
Handles alert dispatching with cooldown management, local structured JSON
and log auditing, webhook notifications (Slack/Discord/Custom API), and
sound triggers.
"""

import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any


class AlertManager:
    def __init__(
        self,
        cooldown_seconds: float = 5.0,
        log_path: str = "outputs/alerts.log",
        json_log_path: str = "outputs/alerts.json",
        webhook_url: Optional[str] = None,
    ):
        self.cooldown_seconds = cooldown_seconds
        self._last_alert_time = 0.0
        self.log_path = Path(log_path)
        self.json_log_path = Path(json_log_path)
        self.webhook_url = webhook_url or os.getenv("SURVEILLANCE_WEBHOOK_URL")

        self.log_path.parent.mkdir(parents=True, exist_ok=True)

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
