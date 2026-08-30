"""
Lightweight alert pipeline for the surveillance system.

Currently logs alerts to a local file and prints to console with a
cooldown so a sustained detection doesn't spam alerts every frame.
Swap `_dispatch` for an email/SMS/webhook call to extend this into a
real notification channel (e.g. Twilio, a Telegram bot, or a webhook
to a security dashboard).
"""

import time
from pathlib import Path


class AlertManager:
    def __init__(self, cooldown_seconds: float = 5.0, log_path: str = "outputs/alerts.log"):
        self.cooldown_seconds = cooldown_seconds
        self._last_alert_time = 0.0
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def trigger(self, snapshot_path: str):
        now = time.time()
        if now - self._last_alert_time < self.cooldown_seconds:
            return  # still in cooldown, skip duplicate alert

        self._last_alert_time = now
        self._dispatch(snapshot_path, now)

    def _dispatch(self, snapshot_path: str, timestamp: float):
        message = f"[ALERT] Threat detected at {time.ctime(timestamp)} — snapshot: {snapshot_path}"
        print(message)
        with open(self.log_path, "a") as f:
            f.write(message + "\n")
