"""
Stage-2 Addendum Merger
------------------------
Merges stage-2 pseudo-labeled pools (data/stage2_pseudo/*) into the TRAIN split
of the existing dataset at data/weapon3k. Valid/test splits remain untouched,
so test-set metrics stay comparable between stage-1 and stage-2 models.

Usage:
  python src/merge_stage2_addendum.py
"""

import json
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PSEUDO_ROOT = DATA_DIR / "stage2_pseudo"
TRAIN_DIR = DATA_DIR / "weapon3k" / "train"

CLASS_NAMES = ["gun", "heavy-weapon", "knife"]


def main():
    if not PSEUDO_ROOT.exists():
        print("No stage2_pseudo directory — nothing to merge.")
        return
    TRAIN_IMAGES = TRAIN_DIR / "images"
    TRAIN_LABELS = TRAIN_DIR / "labels"

    merged = skipped = 0
    per_class = {c: 0 for c in range(3)}
    for pool in sorted(p for p in PSEUDO_ROOT.iterdir() if p.is_dir()):
        pool_images, pool_labels = pool / "images", pool / "labels"
        if not pool_labels.exists():
            continue
        n_pool = 0
        for lbl_path in sorted(pool_labels.glob("*.txt")):
            stem = lbl_path.stem
            img_path = next((p for p in pool_images.glob(stem + ".*")
                             if p.suffix.lower() in (".jpg", ".jpeg", ".png")), None)
            if img_path is None:
                continue
            dst_lbl = TRAIN_LABELS / f"{pool.name}_{stem}.txt"
            dst_img = TRAIN_IMAGES / f"{pool.name}_{stem}.jpg"
            if dst_lbl.exists() and dst_img.exists():
                skipped += 1
                continue
            lbl_text = lbl_path.read_text()
            shutil.move(str(img_path), str(dst_img))
            shutil.move(str(lbl_path), str(dst_lbl))
            for line in lbl_text.strip().splitlines():
                parts = line.split()
                if len(parts) == 5:
                    per_class[int(parts[0])] += 1
            merged += 1
            n_pool += 1
        print(f"📦 {pool.name}: merged {n_pool} images into train split")

    report = {"merged": merged, "skipped_existing": skipped,
              "boxes_by_class": {CLASS_NAMES[c]: per_class[c] for c in range(3)}}
    (DATA_DIR / "weapon3k" / "stage2_addendum_report.json").write_text(json.dumps(report, indent=2))
    n_train = len(list(TRAIN_IMAGES.glob("*.jpg")))
    print(f"\n✅ Merged {merged} pseudo images (+{skipped} already present)")
    print(f"   train split now holds {n_train} images; boxes by class: {report['boxes_by_class']}")


if __name__ == "__main__":
    main()
