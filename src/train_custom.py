"""
Fine-tune YOLOv5 on the local weapon dataset (efficient defaults for 4GB GPUs).

Usage:
    python src/train_custom.py
    python src/train_custom.py --epochs 30 --batch 8 --img 512
    python src/train_custom.py --data data/data_balanced.yaml --hyp data/hyp.weapon-accuracy.yaml \\
        --epochs 50 --batch 4 --img 640 --image-weights --multi-scale --name weapon-accuracy
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

YOLOV5_DIR = Path(__file__).resolve().parent.parent / "yolov5"
ROOT = Path(__file__).resolve().parent.parent


def main():
    import torch

    default_dev = "0" if torch.cuda.is_available() else "cpu"
    parser = argparse.ArgumentParser(description="Train YOLOv5 on crime/weapon dataset")
    parser.add_argument("--data", type=str, default="data/data.yaml", help="Path to dataset yaml")
    parser.add_argument("--weights", type=str, default="models/best.pt", help="Initial weights to fine-tune from")
    parser.add_argument("--hyp", type=str, default="", help="Optional hyperparameters yaml")
    parser.add_argument("--epochs", type=int, default=30, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=8, help="Batch size (8 fits ~4GB VRAM at 512)")
    parser.add_argument("--img", type=int, default=512, help="Input image size (512 = speed/accuracy balance)")
    parser.add_argument("--workers", type=int, default=4, help="Dataloader workers")
    parser.add_argument("--patience", type=int, default=12, help="Early-stop patience (epochs without improvement)")
    parser.add_argument("--device", type=str, default=default_dev, help="CUDA device '0' or 'cpu'")
    parser.add_argument("--project", type=str, default="runs/train", help="Save project directory")
    parser.add_argument("--name", type=str, default="weapon-efficient", help="Save experiment name")
    parser.add_argument("--no-cos-lr", action="store_true", help="Disable cosine LR schedule")
    parser.add_argument("--image-weights", action="store_true", help="Sample images by rare-class weight")
    parser.add_argument("--multi-scale", action="store_true", help="Vary image size +/-50% during training")
    parser.add_argument("--skip-promote", action="store_true", help="Do not copy best.pt into models/")
    parser.add_argument("--promote-as", type=str, default="best.pt.before-accuracy",
                        help="Backup filename for previous live weights on promote")
    args = parser.parse_args()

    if not YOLOV5_DIR.exists():
        print(
            "yolov5/ directory not found. Please ensure ultralytics/yolov5 is present:\n"
            "  git clone https://github.com/ultralytics/yolov5.git"
        )
        sys.exit(1)

    weights = Path(args.weights)
    if not weights.is_absolute():
        weights = ROOT / weights
    if not weights.exists():
        print(f"❌ Weights not found: {weights}")
        sys.exit(1)

    # Preserve live website weights until training finishes successfully
    live = ROOT / "models" / "best.pt"
    backup = ROOT / "models" / "best.pt.pretrain-backup"
    if live.exists() and not backup.exists():
        shutil.copy2(live, backup)
        print(f"🔒 Backed up live weights → {backup}")

    print("==================================================================")
    print("     YOLOv5 WEAPON DETECTION — ACCURACY FINE-TUNE                 ")
    print("==================================================================")
    print(f"📋 Dataset Config : {args.data}")
    print(f"📦 Model Base     : {weights}")
    print(f"🧪 Hyp            : {args.hyp or '(default)'}")
    print(f"⏳ Epochs         : {args.epochs} (patience={args.patience})")
    print(f"📐 Image Size     : {args.img}x{args.img}")
    print(f"⚡ Batch Size     : {args.batch}")
    print(f"⚖️  Image Weights : {args.image_weights}")
    print(f"📏 Multi-Scale    : {args.multi_scale}")
    print(f"🧵 Workers        : {args.workers}")
    print(f"📉 Cosine LR      : {not args.no_cos_lr}")
    print(f"🖥️  Device         : {args.device}\n")

    data_path = ROOT / args.data if not Path(args.data).is_absolute() else Path(args.data)
    cmd = [
        sys.executable,
        str(YOLOV5_DIR / "train.py"),
        "--data", str(data_path),
        "--weights", str(weights),
        "--epochs", str(args.epochs),
        "--batch-size", str(args.batch),
        "--img", str(args.img),
        "--workers", str(args.workers),
        "--patience", str(args.patience),
        "--project", str(ROOT / args.project),
        "--name", args.name,
        "--exist-ok",
    ]
    if args.hyp:
        hyp_path = ROOT / args.hyp if not Path(args.hyp).is_absolute() else Path(args.hyp)
        cmd.extend(["--hyp", str(hyp_path)])
    if not args.no_cos_lr:
        cmd.append("--cos-lr")
    if args.image_weights:
        cmd.append("--image-weights")
    if args.multi_scale:
        cmd.append("--multi-scale")
    if args.device:
        cmd.extend(["--device", args.device])

    subprocess.run(cmd, check=True, cwd=str(ROOT))

    best_weights_path = ROOT / args.project / args.name / "weights" / "best.pt"
    if best_weights_path.exists() and not args.skip_promote:
        dest_path = ROOT / "models" / "best.pt"
        if dest_path.exists():
            shutil.copy2(dest_path, ROOT / "models" / args.promote_as)
        shutil.copy2(best_weights_path, dest_path)
        print(f"\n🎉 Training complete! Promoted best weights → {dest_path}")
        print(f"   Rollback: models/{args.promote_as}")
    else:
        print(f"\n✅ Training finished. Best run weights: {best_weights_path}")


if __name__ == "__main__":
    main()
