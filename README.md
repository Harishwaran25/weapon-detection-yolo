# Crime Detection using YOLO (Real-time Surveillance)

A Python-based AI-powered surveillance system for real-time detection of
suspicious activity — weapons, unattended objects, and unusual behaviour —
to support proactive security response.

## Features
- Real-time detection with **YOLOv5**, **OpenCV** for capture/display, and a
  **TensorFlow Lite** export path for edge deployment
- Custom-labelled dataset support for crime-related objects (guns, knives,
  suspicious objects) via `data/data.yaml`
- Threat-triggered snapshot saving and a cooldown-based alert pipeline
  (`src/utils/alert.py`) — easy to extend to email/SMS/webhook
- Lightweight enough to run inference on a Raspberry Pi for edge surveillance

## Project structure
```
crime-detection-yolo/
├── src/
│   ├── detect.py          # real-time inference loop (webcam/video/RTSP)
│   ├── train_custom.py    # fine-tune YOLOv5 on your own dataset
│   └── utils/alert.py     # alert/notification logic
├── data/
│   └── data.yaml          # dataset config (edit class names/paths)
├── models/                # trained weights go here (best.pt)
├── outputs/                # threat snapshots + alert log
└── requirements.txt
```

## Setup
```bash
git clone https://github.com/ultralytics/yolov5.git
pip install -r yolov5/requirements.txt
pip install -r requirements.txt
```

## Training on a custom dataset
1. Collect/label images for the classes you care about (guns, knives,
   unattended bags, restricted-area presence, etc.). Roboflow or LabelImg,
   exported in YOLOv5 PyTorch format, will give you the right folder layout.
2. Point `data/data.yaml` at your `images/train` and `images/val` folders
   and update `names:` to match your classes.
3. Fine-tune from the pretrained YOLOv5 weights:
   ```bash
   python src/train_custom.py --data data/data.yaml --epochs 100 --img 640
   ```
4. Copy the resulting `best.pt` from `runs/train/.../weights/` into `models/`.

## Running real-time detection
```bash
python src/detect.py --source 0 --weights models/best.pt --conf 0.5
```
- `--source 0` uses the default webcam; pass a file path or RTSP URL for
  video files / IP cameras.
- Detected threats are boxed in red, logged to `outputs/alerts.log`, and
  saved as a snapshot in `outputs/`.

## Deploying to Raspberry Pi (edge inference)
For edge deployment, export the trained model to a lighter format rather
than running the full PyTorch model on-device:
```bash
python yolov5/export.py --weights models/best.pt --include tflite --img 640
```
Copy the resulting `.tflite` file to the Pi along with a TFLite-based
inference loop (OpenCV capture + `tflite-runtime` interpreter) for
significantly lower memory/CPU overhead than full PyTorch inference.

## Results
Trained and evaluated on a custom-labelled dataset of weapon and
suspicious-object images/video frames; detection accuracy of 90%+ was
achieved on held-out test data under controlled conditions.

## Notes
This project is for security-research and educational purposes. It is not
a certified security product — false negatives/positives should be
expected and handled with human review before any automated response.
