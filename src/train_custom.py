"""
Fine-tune YOLOv5 on a custom weapons / suspicious-object dataset.

This wraps the official Ultralytics YOLOv5 training entrypoint so the
whole pipeline (train + detect) lives in one repo. Clone yolov5 as a
sibling directory first (see README), then run this script.

Usage:
    python src/train_custom.py --data data/data.yaml --epochs 100 --img 640
"""

import argparse
import subprocess
import sys
from pathlib import Path

YOLOV5_DIR = Path(__file__).resolve().parent.parent / "yolov5"


def main():
    parser = argparse.ArgumentParser(description="Train YOLOv5 on a custom crime/weapon dataset")
    parser.add_argument("--data", type=str, default="data/data.yaml", help="Path to dataset yaml")
    parser.add_argument("--weights", type=str, default="yolov5s.pt", help="Initial weights to fine-tune from")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--img", type=int, default=640)
    parser.add_argument("--project", type=str, default="runs/train")
    parser.add_argument("--name", type=str, default="crime-detection-yolo")
    args = parser.parse_args()

    if not YOLOV5_DIR.exists():
        print(
            "yolov5/ not found. Clone it first:\n"
            "  git clone https://github.com/ultralytics/yolov5.git\n"
            "  pip install -r yolov5/requirements.txt"
        )
        sys.exit(1)

    cmd = [
        sys.executable,
        str(YOLOV5_DIR / "train.py"),
        "--data", args.data,
        "--weights", args.weights,
        "--epochs", str(args.epochs),
        "--batch-size", str(args.batch),
        "--img", str(args.img),
        "--project", args.project,
        "--name", args.name,
    ]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
