"""
Crime Detection using YOLO — Raspberry Pi TFLite Edge Inference
----------------------------------------------------------------
Lightweight, low-latency inference loop designed for edge deployment on
Raspberry Pi (3B+/4/5) or edge accelerators using TensorFlow Lite.

Requirements on Raspberry Pi:
    pip install tflite-runtime opencv-python numpy

Usage:
    python src/detect_tflite.py --model models/best_int8.tflite --source 0
    python src/detect_tflite.py --model models/best_float32.tflite --source video.mp4 --conf 0.40
"""

import argparse
import time
from pathlib import Path
import cv2
import numpy as np

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    try:
        import tensorflow.lite as tflite
    except ImportError:
        tflite = None

from alerting.alert import AlertManager

# Threat labels monitored for security alert triggers
THREAT_CLASSES = {"gun", "pistol", "rifle", "knife", "weapon", "heavy-weapon"}
DEFAULT_CLASSES = ["gun", "heavy-weapon", "knife"]


class TFLiteYOLO:
    def __init__(self, model_path: str, conf_thres: float = 0.45, iou_thres: float = 0.45):
        if tflite is None:
            raise ImportError(
                "Neither 'tflite_runtime' nor 'tensorflow' is installed. "
                "Please run: pip install tflite-runtime or pip install tensorflow"
            )

        self.interpreter = tflite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()

        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        self.input_shape = self.input_details[0]['shape']  # [1, height, width, 3]
        self.height = self.input_shape[1]
        self.width = self.input_shape[2]
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres

    def preprocess(self, img_bgr):
        """Resize and normalize BGR frame for TFLite model."""
        h_orig, w_orig = img_bgr.shape[:2]
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, (self.width, self.height))
        
        # Check input scale/type (float32 vs int8)
        if self.input_details[0]['dtype'] == np.uint8 or self.input_details[0]['dtype'] == np.int8:
            scale, zero_point = self.input_details[0]['quantization']
            img_input = (img_resized / scale + zero_point).astype(self.input_details[0]['dtype'])
        else:
            img_input = (img_resized / 255.0).astype(np.float32)

        img_input = np.expand_dims(img_input, axis=0)
        return img_input, w_orig, h_orig

    def predict(self, frame):
        """Run TFLite model inference on a frame."""
        t0 = time.perf_counter()
        img_input, w_orig, h_orig = self.preprocess(frame)

        self.interpreter.set_tensor(self.input_details[0]['index'], img_input)
        self.interpreter.invoke()

        output = self.interpreter.get_tensor(self.output_details[0]['index'])
        inference_time_ms = (time.perf_counter() - t0) * 1000.0

        detections = []
        # Handle standard YOLO TFLite output layout [1, num_boxes, 5 + num_classes]
        if len(output.shape) == 3:
            raw_boxes = output[0]
            for box in raw_boxes:
                conf = box[4]
                if conf < self.conf_thres:
                    continue
                class_scores = box[5:]
                class_id = int(np.argmax(class_scores))
                score = conf * class_scores[class_id]

                if score >= self.conf_thres:
                    xc, yc, w, h = box[:4]
                    x1 = int((xc - w / 2) * w_orig / self.width)
                    y1 = int((yc - h / 2) * h_orig / self.height)
                    x2 = int((xc + w / 2) * w_orig / self.width)
                    y2 = int((yc + h / 2) * h_orig / self.height)
                    
                    label_name = DEFAULT_CLASSES[class_id] if class_id < len(DEFAULT_CLASSES) else f"class_{class_id}"
                    detections.append({
                        "bbox": [x1, y1, x2, y2],
                        "confidence": float(score),
                        "class_id": class_id,
                        "label": label_name
                    })

        return detections, inference_time_ms


def run_edge_surveillance(model_path, source, conf_thres, save_dir):
    print(f"⚡ Initializing Edge TFLite Surveillance on model: {model_path}")
    detector = TFLiteYOLO(model_path, conf_thres=conf_thres)
    alert_mgr = AlertManager(cooldown_seconds=5)

    cap = cv2.VideoCapture(int(source) if str(source).isdigit() else source)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video source: {source}")

    Path(save_dir).mkdir(parents=True, exist_ok=True)
    frame_count = 0
    t_start = time.time()

    print("🟢 Edge Surveillance Loop Active. Press 'q' to stop.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        detections, latency_ms = detector.predict(frame)
        threat_detected = False

        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            label = det["label"].lower()
            conf = det["confidence"]
            is_threat = label in THREAT_CLASSES

            color = (0, 0, 255) if is_threat else (0, 255, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame,
                f"[RPi Edge] {label} {conf:.2f}",
                (x1, max(y1 - 10, 0)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )

            if is_threat:
                threat_detected = True

        fps = 1000.0 / max(latency_ms, 1.0)
        cv2.putText(frame, f"Pi Latency: {latency_ms:.1f}ms | FPS: {fps:.1f}", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        if threat_detected:
            cv2.putText(frame, "🚨 EDGE THREAT ALERT", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
            snap_path = str(Path(save_dir) / f"rpi_threat_{frame_count:06d}.jpg")
            cv2.imwrite(snap_path, frame)
            alert_mgr.trigger(snap_path)

        cv2.imshow("Raspberry Pi Edge Surveillance", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("🔴 Edge Surveillance Stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Raspberry Pi TFLite Edge Crime Detector")
    parser.add_argument("--model", type=str, default="models/best.tflite", help="Path to TFLite model weights")
    parser.add_argument("--source", type=str, default="0", help="Webcam 0 or video filepath/RTSP stream")
    parser.add_argument("--conf", type=float, default=0.45, help="Confidence threshold")
    parser.add_argument("--save-dir", type=str, default="outputs", help="Directory for threat snapshots")
    args = parser.parse_args()

    run_edge_surveillance(args.model, args.source, args.conf, args.save_dir)
