"""
Finalize Trained Model
-----------------------
One-shot finalization after the stage-2 fine-tune completes:
  1. Copy the winning weights to models/best.pt
  2. Run true test-split evaluation -> outputs/evaluation_results.json
  3. Export TFLite edge model (FP16) -> models/best.tflite
Picks runs/train/weapon3k-s2/weights/best.pt if present, else stage-1.

Usage:
  python src/finalize_model.py [--run runs/train/weapon3k-s2]
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from evaluate import evaluate_model  # noqa: E402

MODEL_DIR = PROJECT_ROOT / "models"
DEFAULT_DATA_YAML = PROJECT_ROOT / "data" / "data.yaml"


def main():
    parser = argparse.ArgumentParser(description="Publish weights, evaluate on validation split, export TFLite")
    parser.add_argument("--run", type=str, default="runs/train/weapon-accuracy", help="Path to run directory")
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATA_YAML), help="Dataset YAML configuration")
    parser.add_argument("--img", type=int, default=512, help="TFLite edge input size")
    args = parser.parse_args()

    data_yaml_path = Path(args.data)
    if not data_yaml_path.exists():
        data_yaml_path = PROJECT_ROOT / "data" / "data.yaml"

    run_dir = Path(args.run)
    if not run_dir.is_absolute():
        run_dir = PROJECT_ROOT / run_dir
    best = run_dir / "weights" / "best.pt"
    if not best.exists():
        # Fallback to models/best.pt if run directory not found
        fallback_best = MODEL_DIR / "best.pt"
        if fallback_best.exists():
            print(f"ℹ️ {best} not found, using existing {fallback_best}")
            best = fallback_best
        else:
            raise FileNotFoundError(f"{best} not found")

    MODEL_DIR.mkdir(exist_ok=True)

    # 1) Publish PyTorch weights
    target_best = MODEL_DIR / "best.pt"
    if best != target_best:
        shutil.copyfile(best, target_best)
        print(f"✅ Published {best} -> models/best.pt")

    # 2) True evaluation (writes outputs/evaluation_results.json)
    results = evaluate_model(
        weights_path=str(MODEL_DIR / "best.pt"),
        data_config=str(data_yaml_path),
        conf_thres=0.35,
    )
    per_class = ", ".join(f"{k}: {v['map50']}" for k, v in results["classes"].items())
    print(f"✅ Metrics: mAP50={results['mAP_50']} per-class=({per_class})")

    # 3) TFLite export via the strict wrapper
    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "src" / "export_tflite.py"),
         "--weights", str(MODEL_DIR / "best.pt"), "--img", str(args.img)],
        check=True, cwd=str(PROJECT_ROOT),
    )

    print("\n🎉 Finalization complete:")
    print("   models/best.pt        (PyTorch, CUDA server)")
    print("   models/best.tflite    (FP16 edge model, Raspberry Pi)")
    print("   outputs/evaluation_results.json (true test-split metrics)")


if __name__ == "__main__":
    main()
