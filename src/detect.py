"""
Crime Detection using YOLO — Real-time Surveillance
----------------------------------------------------
Real-time detection of weapons, suspicious objects, and unusual activity
from a webcam / video file / RTSP stream using YOLOv5, with OpenCV for capture
and display, and a lightweight alert pipeline.

Usage:
    python src/detect.py --source 0                     # webcam
    python src/detect.py --source path/to/video.mp4      # video file
    python src/detect.py --source rtsp://<camera-url>    # IP camera
    python src/detect.py --weights models/best.pt --conf 0.5
"""

import argparse
import time
from pathlib import Path

import cv2
import torch

from alerting.alert import AlertManager

# Classes we treat as "threats" worth alerting on.
THREAT_CLASSES = {"gun", "pistol", "rifle", "knife", "weapon", "heavy-weapon"}


def load_model(weights: str, device: str = ""):
    """Load a YOLOv5 model (custom-trained or pretrained) via torch.hub."""
    if Path(weights).exists():
        model = torch.hub.load("ultralytics/yolov5", "custom", path=weights, force_reload=False)
    else:
        print(f"⚠️ Custom weights '{weights}' not found. Loading pretrained YOLOv5s as fallback...")
        model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True)
    
    if device:
        model.to(device)
    return model


def annotate_and_check(frame, results, conf_thres: float):
    """Draw boxes on the frame and return whether a threat class was detected."""
    detections = results.pandas().xyxy[0]
    threat_found = False
    threat_details = []

    for _, row in detections.iterrows():
        conf = float(row["confidence"])
        if conf < conf_thres:
            continue

        label = str(row["name"]).lower()
        x1, y1, x2, y2 = int(row["xmin"]), int(row["ymin"]), int(row["xmax"]), int(row["ymax"])
        is_threat = label in THREAT_CLASSES

        color = (0, 0, 255) if is_threat else (0, 200, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            frame,
            f"{label.upper()} {conf:.2f}",
            (x1, max(y1 - 8, 0)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )

        if is_threat:
            threat_found = True
            threat_details.append({"label": label, "confidence": conf, "bbox": [x1, y1, x2, y2]})

    return frame, threat_found, threat_details


def run(source, weights, conf_thres, save_dir, device, camera_id="CAM_01_MAIN"):
    print(f"🎥 Starting Crime Detection Surveillance on source: {source}")
    model = load_model(weights, device)
    model.conf = conf_thres

    cap = cv2.VideoCapture(int(source) if str(source).isdigit() else source)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video source: {source}")

    alert_manager = AlertManager(cooldown_seconds=5)
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    frame_count = 0
    prev_time = time.time()

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        results = model(frame[:, :, ::-1])  # BGR -> RGB for YOLO
        frame, threat_found, threat_details = annotate_and_check(frame, results, conf_thres)

        # FPS calculation & overlay
        now = time.time()
        fps = 1.0 / max(now - prev_time, 1e-6)
        prev_time = now
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        if threat_found:
            top_threat = threat_details[0]
            cv2.putText(frame, "🚨 THREAT DETECTED", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
            snapshot_path = str(Path(save_dir) / f"threat_{frame_count:06d}.jpg")
            cv2.imwrite(snapshot_path, frame)
            
            alert_manager.trigger(
                snapshot_path=snapshot_path,
                threat_class=top_threat["label"],
                confidence=top_threat["confidence"],
                camera_id=camera_id,
            )

        cv2.imshow("Crime Detection - YOLO Surveillance System", frame)
        frame_count += 1

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("🎥 Surveillance loop terminated.")


def parse_args():
    parser = argparse.ArgumentParser(description="Real-time crime/weapon detection with YOLOv5")
    parser.add_argument("--source", type=str, default="0", help="0 for webcam, or path/URL to video stream")
    parser.add_argument("--weights", type=str, default="models/best.pt", help="Path to YOLOv5 weights (.pt)")
    parser.add_argument("--conf", type=float, default=0.45, help="Confidence threshold")
    parser.add_argument("--save-dir", type=str, default="outputs", help="Where to save threat snapshots")
    parser.add_argument("--device", type=str, default="", help="cuda device, e.g. '0', or 'cpu'")
    parser.add_argument("--camera-id", type=str, default="CAM_01_MAIN", help="Identifier for camera stream")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.source, args.weights, args.conf, args.save_dir, args.device, args.camera_id)
