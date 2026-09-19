#!/usr/bin/env python3
"""
Build a class-balanced training split by oversampling rare classes (knife, gun).

Creates data_downloaded/train_balanced/{images,labels} with hardlinks/copies so
heavy-weapon no longer overwhelms the rare classes. Validation stays untouched.
"""

from __future__ import annotations

import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_IMG = ROOT / "data_downloaded" / "train" / "images"
SRC_LBL = ROOT / "data_downloaded" / "train" / "labels"
DST_IMG = ROOT / "data_downloaded" / "train_balanced" / "images"
DST_LBL = ROOT / "data_downloaded" / "train_balanced" / "labels"

# Target approximate box counts after oversampling (relative to rare classes)
# knife ~189 → ×12 ≈ 2268; gun ~2644 → ×2 ≈ 5288; heavy left as-is ~10679
OVERSAMPLE = {2: 12, 0: 2, 1: 1}  # class_id -> multiplier
NAMES = {0: "gun", 1: "heavy-weapon", 2: "knife"}


def class_ids(label_path: Path) -> set[int]:
    ids = set()
    for line in label_path.read_text().splitlines():
        if line.strip():
            ids.add(int(line.split()[0]))
    return ids


def link_or_copy(src: Path, dst: Path) -> None:
    if dst.exists():
        return
    try:
        dst.hardlink_to(src)
    except OSError:
        shutil.copy2(src, dst)


def main() -> None:
    if DST_IMG.exists():
        shutil.rmtree(DST_IMG.parent)
    DST_IMG.mkdir(parents=True)
    DST_LBL.mkdir(parents=True)

    # Group images by rarest class present (knife > gun > heavy)
    buckets = {0: [], 1: [], 2: []}
    for lbl in SRC_LBL.glob("*.txt"):
        ids = class_ids(lbl)
        if not ids:
            continue
        img = None
        for ext in (".jpg", ".jpeg", ".png", ".bmp", ".webp"):
            cand = SRC_IMG / f"{lbl.stem}{ext}"
            if cand.exists():
                img = cand
                break
        if img is None:
            continue
        if 2 in ids:
            buckets[2].append((img, lbl))
        elif 0 in ids:
            buckets[0].append((img, lbl))
        else:
            buckets[1].append((img, lbl))

    written = 0
    box_counts = Counter()
    for cid, pairs in buckets.items():
        reps = OVERSAMPLE.get(cid, 1)
        for rep in range(reps):
            for img, lbl in pairs:
                stem = f"{img.stem}__bal{cid}r{rep}" if rep > 0 or cid in (0, 2) else img.stem
                # Always unique names when oversampling
                if reps > 1 or cid in (0, 2):
                    stem = f"{img.stem}__c{cid}r{rep}"
                dst_img = DST_IMG / f"{stem}{img.suffix}"
                dst_lbl = DST_LBL / f"{stem}.txt"
                link_or_copy(img, dst_img)
                link_or_copy(lbl, dst_lbl)
                written += 1
                for line in lbl.read_text().splitlines():
                    if line.strip():
                        box_counts[int(line.split()[0])] += 1

    print(f"Balanced train images: {written}")
    print(
        "Box counts: "
        + ", ".join(f"{NAMES[k]}={box_counts[k]}" for k in sorted(box_counts))
    )
    print(f"Output: {DST_IMG.parent}")


if __name__ == "__main__":
    main()
