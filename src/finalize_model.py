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
DATA_YAML = PROJECT_ROOT / "data" / "weapon3k" / "data.yaml"


def main():
    parser = argparse.ArgumentParser(description="Publish weights, evaluate on test split, export TFLite")
    parser.add_argument("--run", type=str, default="runs/train/weapon3k-s2")
    parser.add_argument("--img", type=int, default=512, help="TFLite edge input size")
    args = parser.parse_args()

    run_dir = PROJECT_ROOT / args.run
    best = run_dir / "weights" / "best.pt"
    if not best.exists():
        raise FileNotFoundError(f"{best} not found")

    MODEL_DIR.mkdir(exist_ok=True)

    # 1) Publish PyTorch weights
    shutil.copyfile(best, MODEL_DIR / "best.pt")
    print(f"✅ Published {best} -> models/best.pt")

    # 2) True test-split evaluation (writes outputs/evaluation_results.json)
    results = evaluate_model(
        weights_path=str(MODEL_DIR / "best.pt"),
        data_config=str(DATA_YAML),
        task="test",
    )
    per_class = ", ".join(f"{k}: {v['map50']}" for k, v in results["classes"].items())
    print(f"✅ Test-split metrics: mAP50={results['mAP_50']} per-class=({per_class})")

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
