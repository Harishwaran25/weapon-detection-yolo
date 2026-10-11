#!/usr/bin/env python3
"""
Stratify Knife Dataset: Corrects Roboflow's inverted split.
Transfers 150 knife images from valid/ to train/ to provide adequate training samples,
leaving 45 clean knife images in valid/ (preserving 23% validation ratio).
"""

import random
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRAIN_IMG = ROOT / "data_downloaded" / "train" / "images"
TRAIN_LBL = ROOT / "data_downloaded" / "train" / "labels"
VALID_IMG = ROOT / "data_downloaded" / "valid" / "images"
VALID_LBL = ROOT / "data_downloaded" / "valid" / "labels"


def main():
    rng = random.Random(42)
    val_knife_lbls = []
    for lbl in VALID_LBL.glob("*.txt"):
        has_knife = False
        for line in lbl.read_text().splitlines():
            if line.strip() and line.strip().split()[0] == "2":
                has_knife = True
                break
        if has_knife:
            val_knife_lbls.append(lbl)

    print(f"Total knife files in valid: {len(val_knife_lbls)}")
    rng.shuffle(val_knife_lbls)

    # Keep 45 in valid, transfer the rest to train
    to_transfer = val_knife_lbls[:-45]
    print(f"Transferring {len(to_transfer)} knife images/labels to train/...")

    transferred = 0
    for lbl in to_transfer:
        stem = lbl.stem
        # find matching image
        img_found = None
        for ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
            cand = VALID_IMG / f"{stem}{ext}"
            if cand.exists():
                img_found = cand
                break
        if img_found:
            shutil.move(str(img_found), str(TRAIN_IMG / img_found.name))
            shutil.move(str(lbl), str(TRAIN_LBL / lbl.name))
            transferred += 1

    # Remove stale caches
    for cache in [
        ROOT / "data_downloaded" / "train" / "labels.cache",
        ROOT / "data_downloaded" / "valid" / "labels.cache",
        ROOT / "data_downloaded" / "train_balanced" / "labels.cache",
    ]:
        if cache.exists():
            cache.unlink()

    print(f"✅ Successfully transferred {transferred} knife samples to train split.")
    print(f"   Train now has {transferred + 13} base knife images.")
    print(f"   Valid retains 45 clean held-out knife images.")


if __name__ == "__main__":
    main()
