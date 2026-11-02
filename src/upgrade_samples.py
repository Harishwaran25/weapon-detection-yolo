"""
Dashboard Benchmark Samples Upgrader
-------------------------------------
Copies clean, clearly-visible weapon images from the held-out test split into
data/samples/ so the dashboard Threat Inspector can exercise every class with
more than the original 3 benchmark images per category.

Selection rule: test images whose label file contains 1-3 boxes and whose
largest box covers >= 10% of the image area (weapon is prominent).

Usage:
  python src/upgrade_samples.py --data data/weapon3k --per-class 6
"""

import argparse
import json
import random
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = PROJECT_ROOT / "data" / "samples"

CLASS_NAMES = ["gun", "heavy-weapon", "knife"]


def box_stats(label_file: Path) -> tuple[int, float]:
    """Return (n_boxes, largest_box_area_fraction)."""
    best = 0.0
    n = 0
    for line in label_file.read_text().strip().splitlines():
        parts = line.split()
        if len(parts) != 5:
            continue
        n += 1
        w, h = float(parts[3]), float(parts[4])
        best = max(best, w * h)
    return n, best


def main():
    parser = argparse.ArgumentParser(description="Add extra benchmark samples per class from the test split")
    parser.add_argument("--data", type=str, default=str(PROJECT_ROOT / "data" / "weapon3k"))
    parser.add_argument("--per-class", type=int, default=6)
    args = parser.parse_args()

    test_images = Path(args.data) / "test" / "images"
    test_labels = Path(args.data) / "test" / "labels"
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    existing = {p.name for p in SAMPLES_DIR.glob("sample_*.jpg")}
    rng = random.Random(7)

    picked: dict[int, list] = {c: [] for c in range(3)}
    for img_path in sorted(test_images.glob("*.jpg")):
        lbl = test_labels / (img_path.stem + ".txt")
        if not lbl.exists():
            continue
        n, area = box_stats(lbl)
        if 1 <= n <= 3 and area >= 0.10:
            cls = int(lbl.read_text().split()[0])  # dominant (first) class
            picked[cls].append(img_path)

    copied_report = {}
    for cls, name in enumerate(CLASS_NAMES):
        candidates = picked[cls]
        rng.shuffle(candidates)
        copied = []
        idx = 1
        for img_path in candidates:
            if len(copied) >= args.per_class:
                break
            # find next free sample index for this class
            while f"sample_{name}_{idx}.jpg" in existing:
                idx += 1
            dest = SAMPLES_DIR / f"sample_{name}_{idx}.jpg"
            shutil.copyfile(img_path, dest)
            existing.add(dest.name)
            copied.append(dest.name)
            idx += 1
        copied_report[name] = copied
        print(f"✅ {name}: +{len(copied)} samples -> {copied}")

    (SAMPLES_DIR / "samples_manifest.json").write_text(json.dumps(copied_report, indent=2))
    print(f"\n📦 data/samples now holds {len(existing)} benchmark images")


if __name__ == "__main__":
    main()
