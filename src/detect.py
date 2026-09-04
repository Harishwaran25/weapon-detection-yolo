"""
Crime Detection using YOLO — Real-time Surveillance CLI & Inference Engine
---------------------------------------------------------------------------
High-performance surveillance detector supporting:
- Live Webcam streams (source 0)
- RTSP / HTTP IP surveillance cameras
- Video files (MP4, AVI, MKV) with annotated video output
- Single images and directories of images
- Headless server mode (--no-show) and automated snapshot logging

Usage:
    python src/detect.py --source 0                                    # Live webcam
    python src/detect.py --source path/to/video.mp4 --save-video       # Video file
    python src/detect.py --source path/to/image.jpg --save-img         # Single image
    python src/detect.py --source rtsp://admin:pass@192.168.1.50:554   # IP camera
    python src/detect.py --weights models/best.pt --conf 0.40 --no-show
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any

import cv2
import torch
import numpy as np

# Ensure yolov5 is in sys.path
YOLOV5_DIR = Path(__file__).resolve().parent.parent / "yolov5"
if str(YOLOV5_DIR) not in sys.path:
    sys.path.append(str(YOLOV5_DIR))

from alerting.alert import AlertManager

THREAT_CLASSES = {"gun", "pistol", "rifle", "knife", "weapon", "heavy-weapon"}


def load_model(weights: str, device: str = ""):
    """Load YOLO model with automatic GPU selection and fallback handling."""
    device_str = device if device else ("cuda:0" if torch.cuda.is_available() else "cpu")
    weights_path = Path(weights)

    if weights_path.exists():
        print(f"📦 Loading custom weights from: {weights_path} on {device_str}")
        try:
            model = torch.hub.load(
                str(YOLOV5_DIR),
                "custom",
                path=str(weights_path),
                source="local",
                device=device_str,
                force_reload=False
            )
        except Exception as e:
            print(f"⚠️ Local hub load note: {e}. Trying ultralytics hub load...")
            model = torch.hub.load("ultralytics/yolov5", "custom", path=str(weights_path), device=device_str)
    else:
        print(f"⚠️ Weights '{weights}' not found. Loading pretrained yolov5s on {device_str}...")
        model = torch.hub.load(str(YOLOV5_DIR), "yolov5s", source="local", device=device_str)

    return model, device_str


def annotate_frame(frame: np.ndarray, results, conf_thres: float) -> Tuple[np.ndarray, bool, List[Dict[str, Any]]]:
    """Annotate frame with high-tech threat bounding boxes and return detections."""
    detections = results.pandas().xyxy[0]
    threat_found = False
    threat_details = []
    h, w = frame.shape[:2]

    CLASS_MAP = {0: "gun", 1: "heavy-weapon", 2: "knife"}
    for _, row in detections.iterrows():
        conf = float(row["confidence"])
        if conf < conf_thres:
            continue

        cid = int(row["class"]) if "class" in row else 0
        label = CLASS_MAP.get(cid, str(row.get("name", cid)).lower())
        x1, y1 = max(0, int(row["xmin"])), max(0, int(row["ymin"]))
        x2, y2 = min(w, int(row["xmax"])), min(h, int(row["ymax"]))
        is_threat = label in THREAT_CLASSES

        color = (0, 0, 255) if is_threat else (0, 220, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Header tag
        tag = f"{label.upper()} {conf:.2f}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        (tw, th), _ = cv2.getTextSize(tag, font, 0.5, 1)
        cv2.rectangle(frame, (x1, max(0, y1 - th - 6)), (x1 + tw + 4, y1), color, -1)
        cv2.putText(frame, tag, (x1 + 2, y1 - 4), font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        if is_threat:
            threat_found = True
            threat_details.append({"label": label, "confidence": conf, "bbox": [x1, y1, x2, y2]})
            # Draw target crosshair
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            cv2.circle(frame, (cx, cy), 14, (0, 0, 255), 1)
            cv2.circle(frame, (cx, cy), 3, (0, 0, 255), -1)

    return frame, threat_found, threat_details


def run_image(source: str, model, conf_thres: float, save_dir: str, no_show: bool):
    """Run inference on a single image file."""
    frame = cv2.imread(source)
    if frame is None:
        raise RuntimeError(f"Could not read image file: {source}")

    t0 = time.perf_counter()
    results = model(frame[:, :, ::-1])
    inference_ms = (time.perf_counter() - t0) * 1000.0

    frame, threat_found, threat_details = annotate_frame(frame, results, conf_thres)

    out_path = Path(save_dir) / f"detected_{Path(source).name}"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), frame)

    print(f"\n✅ Detection completed in {inference_ms:.1f}ms")
    print(f"📁 Output saved to: {out_path}")
    if threat_found:
        print(f"🚨 THREATS FOUND ({len(threat_details)}):")
        for t in threat_details:
            print(f"   • {t['label'].upper()} (Confidence: {t['confidence']*100:.1f}%) at {t['bbox']}")
    else:
        print("🛡️ No weapons detected.")

    if not no_show:
        try:
            cv2.imshow("Sentinel AI - Image Detection", frame)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        except Exception:
            pass


def run_stream(source: str, model, conf_thres: float, save_dir: str, camera_id: str, no_show: bool, save_video: bool):
    """Run real-time surveillance inference on webcam, RTSP stream, or video file."""
    is_cam = source.isdigit() or source.startswith("rtsp://") or source.startswith("http://")
    cap = cv2.VideoCapture(int(source) if source.isdigit() else source)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video stream or camera: {source}")

    alert_manager = AlertManager(cooldown_seconds=4, log_path=f"{save_dir}/alerts.log", json_log_path=f"{save_dir}/alerts.json")
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    vw = None
    if save_video:
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        video_out_path = str(Path(save_dir) / f"surveillance_output_{int(time.time())}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        vw = cv2.VideoWriter(video_out_path, fourcc, fps, (w, h))
        print(f"📹 Recording output stream to: {video_out_path}")

    print(f"🎥 Surveillance loop active on source: {source} (Press 'q' in window or Ctrl+C to stop)")
    frame_idx = 0
    prev_time = time.time()

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame_idx += 1
            results = model(frame[:, :, ::-1])
            frame, threat_found, threat_details = annotate_frame(frame, results, conf_thres)

            now = time.time()
            fps = 1.0 / max(now - prev_time, 1e-6)
            prev_time = now

            # Overlay HUD
            cv2.putText(frame, f"FPS: {fps:.1f} | CAM: {camera_id}", (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            if threat_found:
                top = threat_details[0]
                cv2.putText(frame, f"🚨 {top['label'].upper()} DETECTED!", (12, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
                snap_path = str(Path(save_dir) / f"threat_{frame_idx:06d}.jpg")
                cv2.imwrite(snap_path, frame)
                alert_manager.trigger(
                    snapshot_path=snap_path,
                    threat_class=top["label"],
                    confidence=top["confidence"],
                    camera_id=camera_id,
                )

            if vw:
                vw.write(frame)

            if not no_show:
                try:
                    cv2.imshow("Sentinel AI - Surveillance System", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                except Exception:
                    no_show = True

    finally:
        cap.release()
        if vw:
            vw.release()
        cv2.destroyAllWindows()
        print("\n🛑 Surveillance session closed.")


def main():
    parser = argparse.ArgumentParser(description="Sentinel AI - Crime & Weapon Detection Surveillance Engine")
    parser.add_argument("--source", type=str, default="0", help="Camera index (0), video path, image path, or RTSP URL")
    parser.add_argument("--weights", type=str, default="models/best.pt", help="Path to YOLO weights (.pt)")
    parser.add_argument("--conf", type=float, default=0.35, help="Confidence threshold")
    parser.add_argument("--save-dir", type=str, default="outputs", help="Directory for snapshots and alerts")
    parser.add_argument("--device", type=str, default="", help="CUDA device ('0') or 'cpu'")
    parser.add_argument("--camera-id", type=str, default="CAM_01_MAIN", help="Camera identifier")
    parser.add_argument("--no-show", action="store_true", help="Disable GUI window display (headless mode)")
    parser.add_argument("--save-video", action="store_true", help="Record annotated video output to file")
    args = parser.parse_args()

    model, device = load_model(args.weights, args.device)
    model.conf = args.conf

    # Check if source is image file
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    if Path(args.source).suffix.lower() in exts and Path(args.source).exists():
        run_image(args.source, model, args.conf, args.save_dir, args.no_show)
    else:
        run_stream(args.source, model, args.conf, args.save_dir, args.camera_id, args.no_show, args.save_video)


if __name__ == "__main__":
    main()
