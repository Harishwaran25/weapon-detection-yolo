"""
Fine-tune YOLOv5 on Roboflow Weapon Detection Dataset (12,000+ images).

Usage:
    python src/train_custom.py --data data/data.yaml --weights yolov5s.pt --epochs 100 --img 640 --batch 16
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

YOLOV5_DIR = Path(__file__).resolve().parent.parent / "yolov5"


def main():
    parser = argparse.ArgumentParser(description="Train YOLOv5 on Roboflow Crime/Weapon Dataset")
    parser.add_argument("--data", type=str, default="data/data.yaml", help="Path to dataset yaml")
    parser.add_argument("--weights", type=str, default="yolov5s.pt", help="Initial weights to fine-tune from")
    parser.add_argument("--epochs", type=int, default=100, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--img", type=int, default=640, help="Input image size")
    parser.add_argument("--device", type=str, default="", help="CUDA device '0', '0,1,2,3', or 'cpu'")
    parser.add_argument("--project", type=str, default="runs/train", help="Save project directory")
    parser.add_argument("--name", type=str, default="weapon-detection-yolo", help="Save experiment name")
    args = parser.parse_args()

    if not YOLOV5_DIR.exists():
        print(
            "yolov5/ directory not found. Please ensure ultralytics/yolov5 is present:\n"
            "  git clone https://github.com/ultralytics/yolov5.git"
        )
        sys.exit(1)

    print("==================================================================")
    print("     YOLOv5 WEAPON & CRIME DETECTION TRAINING PIPELINE            ")
    print("==================================================================")
    print(f"📋 Dataset Config : {args.data}")
    print(f"📦 Model Base     : {args.weights}")
    print(f"⏳ Epochs         : {args.epochs}")
    print(f"📐 Image Size     : {args.img}x{args.img}")
    print(f"⚡ Batch Size     : {args.batch}\n")

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
        "--exist-ok"
    ]
    if args.device:
        cmd.extend(["--device", args.device])

    subprocess.run(cmd, check=True)

    # Copy best weights to models/best.pt upon completion
    best_weights_path = Path(args.project) / args.name / "weights" / "best.pt"
    dest_path = Path("models/best.pt")
    if best_weights_path.exists():
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(best_weights_path, dest_path)
        print(f"\n🎉 Training complete! Best weights updated at {dest_path}")
    else:
        print(f"\n✅ Training process completed.")


if __name__ == "__main__":
    main()
