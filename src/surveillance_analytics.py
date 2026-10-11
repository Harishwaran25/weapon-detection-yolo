"""
Sentinel AI — Advanced Surveillance Analytics & Privacy Protection Suite
-------------------------------------------------------------------------
Expands Crime Detection from naive static weapon boxes to contextual surveillance:
1. Threat Urgency & Motion Heuristics (Severity Score 0-100, Threat State).
2. Temporal centroid velocity tracking across consecutive frames.
3. Privacy-Preserving Face & Bystander Obfuscation (GDPR compliant alert snapshots).
"""

import math
import time
from typing import List, Dict, Any, Tuple, Optional
import cv2
import numpy as np

CLASS_LETHALITY_WEIGHTS = {
    "heavy-weapon": 95.0,
    "gun": 90.0,
    "knife": 80.0,
}

THREAT_LEVEL_THRESHOLDS = [
    (80, "CRITICAL_IMMINENT", "Immediate lethal weapon deployment detected"),
    (60, "ELEVATED_THREAT", "Active weapon detected in camera field"),
    (40, "SUSPICIOUS_ACTIVITY", "Potential weapon signature identified"),
    (0, "LOW_RISK", "Normal surveillance state"),
]


class TemporalThreatTracker:
    """Tracks detected weapon bounding boxes across consecutive frames to compute motion dynamics."""

    def __init__(self, max_history_seconds: float = 3.0):
        self.max_history_seconds = max_history_seconds
        # track_id -> list of (timestamp, centroid_x, centroid_y, bbox_area_norm)
        self.tracks: Dict[str, List[Tuple[float, float, float, float]]] = {}
        self.last_cleanup = time.time()

    def update_and_score(
        self,
        frame_shape: Tuple[int, int],
        detections: List[Dict[str, Any]]
    ) -> Tuple[float, str, str, List[Dict[str, Any]]]:
        """
        Calculates composite Threat Severity Score (0-100) and enriches detections
        with temporal trajectory and velocity metadata.
        """
        now = time.time()
        h, w = frame_shape[:2]
        frame_area = float(h * w)

        if now - self.last_cleanup > 5.0:
            self._cleanup_stale_tracks(now)

        max_threat_score = 0.0
        top_urgency = "LOW_RISK"
        top_summary = "Normal surveillance state"

        enriched_detections = []

        for det in detections:
            label = det.get("label", "").lower()
            conf = float(det.get("confidence", 0.0))
            bbox = det.get("bbox", [0, 0, 0, 0])

            x1, y1, x2, y2 = bbox
            bw = max(1, x2 - x1)
            bh = max(1, y2 - y1)
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            box_area = float(bw * bh)
            area_fraction = min(1.0, box_area / frame_area)

            # 1. Base Lethality & Confidence Score
            base_weight = CLASS_LETHALITY_WEIGHTS.get(label, 70.0)
            conf_factor = conf ** 1.2

            # 2. Proximity Factor (weapons closer to camera represent higher immediate threat)
            proximity_factor = min(1.0, area_fraction * 8.0)  # maxed at 12.5% frame coverage

            # 3. Motion Dynamics / Centroid Velocity
            track_key = f"{label}_{int(cx // 80)}_{int(cy // 80)}"
            if track_key not in self.tracks:
                self.tracks[track_key] = []
            self.tracks[track_key].append((now, cx, cy, area_fraction))

            # Compute velocity (pixels/sec normalized)
            recent_points = [p for p in self.tracks[track_key] if now - p[0] <= 1.0]
            velocity_score = 0.0
            if len(recent_points) >= 2:
                t0, x0, y0, _ = recent_points[0]
                t1, x1_c, y1_c, _ = recent_points[-1]
                dt = max(0.01, t1 - t0)
                dist = math.hypot(x1_c - x0, y1_c - y0)
                norm_speed = (dist / max(w, h)) / dt
                # Rapid brandishing or approaching camera increases urgency
                velocity_score = min(20.0, norm_speed * 15.0)

            composite_score = (base_weight * 0.55 * conf_factor) + (proximity_factor * 25.0) + velocity_score
            composite_score = round(min(100.0, max(0.0, composite_score)), 1)

            urgency_level = "LOW_RISK"
            urgency_msg = "Normal monitoring"
            for threshold, level_code, msg in THREAT_LEVEL_THRESHOLDS:
                if composite_score >= threshold:
                    urgency_level = level_code
                    urgency_msg = msg
                    break

            if composite_score > max_threat_score:
                max_threat_score = composite_score
                top_urgency = urgency_level
                top_summary = f"{urgency_msg} ({label.upper()} - Score: {composite_score}/100)"

            enriched_det = dict(det)
            enriched_det["threatScore"] = composite_score
            enriched_det["urgencyLevel"] = urgency_level
            enriched_det["proximityPct"] = round(area_fraction * 100.0, 1)
            enriched_detections.append(enriched_det)

        return max_threat_score, top_urgency, top_summary, enriched_detections

    def _cleanup_stale_tracks(self, now: float):
        cutoff = now - self.max_history_seconds
        stale_keys = []
        for k, pts in self.tracks.items():
            self.tracks[k] = [p for p in pts if p[0] > cutoff]
            if not self.tracks[k]:
                stale_keys.append(k)
        for k in stale_keys:
            del self.tracks[k]
        self.last_cleanup = now


class PrivacyFilter:
    """Enterprise GDPR-compliant face and bystander blurring filter."""

    def __init__(self):
        # OpenCV built-in Haar cascade for fast, dependency-free face obfuscation
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path) if cv2.os.path.exists(cascade_path) else None

    def apply_privacy_blur(
        self,
        frame: np.ndarray,
        weapon_bboxes: List[List[int]],
        blur_faces: bool = True
    ) -> np.ndarray:
        """
        Blurs detected human faces in the frame while preserving weapon evidence regions.
        """
        if not blur_faces or self.face_cascade is None:
            return frame

        output = frame.copy()
        gray = cv2.cvtColor(output, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=4, minSize=(30, 30))

        for (fx, fy, fw, fh) in faces:
            # Check if face overlaps with weapon box (do not obscure weapon evidence)
            overlaps_weapon = False
            for (wx1, wy1, wx2, wy2) in weapon_bboxes:
                if not (fx + fw < wx1 or fx > wx2 or fy + fh < wy1 or fy > wy2):
                    overlaps_weapon = True
                    break

            if not overlaps_weapon:
                face_roi = output[fy:fy + fh, fx:fx + fw]
                if face_roi.size > 0:
                    # Heavy Gaussian blur for privacy
                    ksize = (max(15, (fw // 3) * 2 + 1), max(15, (fh // 3) * 2 + 1))
                    blurred_face = cv2.GaussianBlur(face_roi, ksize, 30)
                    output[fy:fy + fh, fx:fx + fw] = blurred_face
                    cv2.rectangle(output, (fx, fy), (fx + fw, fy + fh), (100, 100, 100), 1)
                    cv2.putText(output, "PRIVACY MASK", (fx, max(0, fy - 4)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (180, 180, 180), 1)

        return output


temporal_tracker = TemporalThreatTracker()
privacy_filter = PrivacyFilter()
