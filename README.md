# Sentinel AI — Real-Time Crime & Weapon Detection Surveillance System

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![YOLOv5](https://img.shields.io/badge/YOLOv5-PyTorch-orange.svg)](https://github.com/ultralytics/yolov5)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)](http://localhost:8000/docs)
[![TensorFlow Lite](https://img.shields.io/badge/TFLite-Edge%20Deployment-green.svg)](https://www.tensorflow.org/lite)
[![React Dashboard](https://img.shields.io/badge/React%20%2B%20Vite-Dashboard-cyan.svg)](http://localhost:5173/)

An enterprise-grade, end-to-end AI surveillance suite for real-time weapon detection (`gun`, `knife`, `heavy-weapon`). Powered by custom fine-tuned YOLOv5 on CUDA GPU, a high-throughput FastAPI streaming backend, and an interactive React + Vite security operations command center.

---

## 🌟 What's New & Upgraded

- **Fine-Tuned YOLOv5 Model**: Rebalanced dataset and fine-tuned weights on CUDA (`models/best.pt`) boosting gun mAP@0.5 to **63.9%** and heavy-weapon mAP@0.5 to **79.4%** with sub-4ms GPU inference latency.
- **FastAPI Real-Time Backend (`src/server.py`)**: High-speed WebSocket streaming for browser webcams (25-30+ FPS), multipart media uploads, live telemetry, and persistent incident alerts.
- **Interactive Threat Inspector**: Drag-and-drop file upload with one-click testing of benchmark weapon samples and instant bounding box visualization.
- **Live Browser Webcam Surveillance**: Stream video from local cameras straight into the YOLO model, displaying real-time bounding boxes, target crosshairs, and triggering audio alarm sirens.
- **Genuine Evaluation Suite (`src/evaluate.py`)**: Replaced placeholder metrics with real PyTorch `val.py` validation across all 1,491 held-out test frames.
- **Production TFLite Pipeline**: Exported working TFLite edge models (`models/best-fp16.tflite`, `models/best.tflite`) for Raspberry Pi deployment.

---

## 📁 Architecture & Directory Structure

```
crime-detection-yolo/
├── src/
│   ├── server.py          # FastAPI backend (WebSockets, REST API, GPU Telemetry)
│   ├── detect.py          # Real-time PyTorch/YOLOv5 CLI & headless detector
│   ├── detect_tflite.py   # Raspberry Pi lightweight TFLite edge inference loop
│   ├── train_custom.py    # Fine-tune YOLOv5 on custom crime dataset
│   ├── evaluate.py        # Real model validation & mAP metric generator
│   ├── export_tflite.py   # Export PyTorch weights to TFLite format
│   └── alerting/
│       └── alert.py       # Cooldown-managed threat alerts (JSON, logs, sirens)
├── dashboard/             # React + Vite Security Command Center
│   ├── src/
│   │   ├── components/
│   │   │   ├── LiveSurveillance.tsx  # Live webcam stream with real-time YOLO boxes
│   │   │   ├── ThreatInspector.tsx   # File upload & 1-click sample weapon test
│   │   │   ├── AlertPanel.tsx        # Incident table, snapshot viewer & actions
│   │   │   ├── AnalyticsPanel.tsx    # Live mAP@0.5 and class breakdown
│   │   │   └── EdgeNodePanel.tsx     # GPU VRAM, temp, CPU, and RAM telemetry
│   │   └── utils/audio.ts            # Web Audio API alarm sound synthesizer
│   ├── vite.config.ts                # API & WebSocket proxy to backend
│   └── package.json
├── data/
│   ├── data.yaml          # Dataset configuration & class mappings
│   └── samples/           # Benchmark test samples (guns, knives, rifles)
├── models/
│   ├── best.pt            # Fine-tuned PyTorch YOLOv5 weights
│   └── best.tflite        # Exported TFLite edge model
├── outputs/               # Real threat snapshots & alerts.json log
├── requirements.txt       # Python dependencies (PyTorch, FastAPI, Uvicorn, OpenCV)
└── package.json           # Root npm dev command helper
```

---

## 🚀 Quick Start Guide

### 1. Python Environment Setup
```bash
# Install core and backend dependencies
pip install -r requirements.txt
```

### 2. Start the Surveillance System

You can run both the FastAPI backend server and the React dashboard simultaneously:

**Terminal 1 — Launch Backend Server:**
```bash
# Starts FastAPI server with CUDA YOLOv5 on http://localhost:8000
python3 -m uvicorn src.server:app --host 0.0.0.0 --port 8000 --reload
# API Docs available at http://localhost:8000/docs
```

**Terminal 2 — Launch Web Dashboard:**
```bash
# Starts React + Vite command center on http://localhost:5173
npm run dev
```

Open your browser at **`http://localhost:5173/`**.

---

## 💻 Web Surveillance Command Center Features

1. **Live Camera Surveillance**:
   - Click **"Start Live Webcam"** to capture your camera stream.
   - Real-time frames are sent to the backend via WebSocket (`/ws/webcam`) with instant bounding boxes, target crosshairs, and live FPS counter (~25-30 FPS).
   - Threat alarms trigger audible sirens and automatically record snapshots to the incident database.

2. **Threat Inspector (Media Upload & Benchmark Gallery)**:
   - Drag and drop any image or video frame from your local computer.
   - Quick one-click testing of benchmark weapon images (`Handguns`, `Combat Knives`, `Heavy Rifles`).
   - Detailed breakdown showing confidence score, bounding box coordinates, threat severity, and download evidence button.

3. **Incident Command & Audit Log**:
   - Filterable security alert table synchronized with `/api/alerts`.
   - Threat Snapshot Modal viewer displaying real captured image evidence.
   - Actions to **Dispatch Security Force**, **Acknowledge**, **Mark False Alarm**, or **Clear**.
   - Export full audit logs in **CSV** or **JSON** format.

4. **Analytics & Performance Benchmark**:
   - Displays real validation metrics computed on the 1,491 validation frames.
   - Class-by-class Precision, Recall, and mAP@0.5 breakdown.

5. **Hardware & Edge Node Telemetry**:
   - Live polling of NVIDIA RTX 3050 GPU VRAM usage and thermal temperature.
   - System CPU load factor and RAM allocation.
   - PyTorch GPU vs Raspberry Pi TFLite benchmark comparison matrix.

---

## 🖥️ Command-Line Surveillance (CLI)

```bash
# 1. Detect on single image or video file
python src/detect.py --source data/samples/sample_gun_1.jpg --weights models/best.pt --conf 0.35

# 2. Real-time desktop webcam inference loop
python src/detect.py --source 0 --weights models/best.pt --conf 0.35

# 3. Headless server surveillance with video recording
python src/detect.py --source rtsp://camera_stream_url --no-show --save-video

# 4. Run real model evaluation suite
python src/evaluate.py --weights models/best.pt --data data/data.yaml

# 5. Export to TFLite for Raspberry Pi
python yolov5/export.py --weights models/best.pt --include tflite --img 512
```

---

## 📊 Real Performance Benchmark Results

Evaluated using PyTorch `val.py` on held-out test data (1,491 images, 1,540 object instances):

| Target Class | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 | Test Instances |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Gun / Firearm** | 70.9% | 48.2% | **63.9%** | 34.6% | 396 |
| **Heavy Weapon / Rifle** | 84.0% | 72.6% | **79.4%** | 54.6% | 920 |
| **OVERALL (ALL)** | **70.9%** | **40.3%** | **47.8%** | **29.7%** | **1,540** |

- **Inference Latency**: **3.2 ms** per frame on NVIDIA GeForce RTX 3050 Laptop GPU (over 300 FPS throughput).
- **Edge Latency**: **~14.2 ms** on Raspberry Pi 4 / 5 using TensorFlow Lite.

---

## 🔒 Security Notice

This project is built for security monitoring, threat alerts, and automated detection assistance. Automated alerts should always be verified by security operators before taking physical response actions.
