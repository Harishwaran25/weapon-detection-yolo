#!/usr/bin/env python3
"""
Crime & Weapon Dataset Sanitizer & Deduplication Pipeline
----------------------------------------------------------
1. Scans MD5 hashes across valid/images and train/images.
2. Identifies and removes train-validation contamination (data leakage).
3. Verifies zero leakage remains.
4. Generates a clean dataset report in outputs/dataset_health_report.json.

Usage:
    python src/clean_dataset.py [--dry-run]
    python src/clean_dataset.py --verify
"""

import argparse
import glob
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data_downloaded"
TRAIN_IMG = DATA_DIR / "train" / "images"
TRAIN_LBL = DATA_DIR / "train" / "labels"
VALID_IMG = DATA_DIR / "valid" / "images"
VALID_LBL = DATA_DIR / "valid" / "labels"
REPORT_PATH = PROJECT_ROOT / "outputs" / "dataset_health_report.json"


def get_file_md5(filepath: Path) -> str:
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def scan_and_clean(dry_run: bool = False):
    print("==================================================================")
    print("      DATASET LEAKAGE SANITIZER & HEALTH INSPECTOR               ")
    print("==================================================================")
    print(f"📁 Train Dir : {TRAIN_IMG}")
    print(f"📁 Valid Dir : {VALID_IMG}\n")

    valid_hashes = {}
    print("🔍 Hashing validation set images...")
    for p in VALID_IMG.glob("*"):
        if p.is_file() and p.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
            valid_hashes[get_file_md5(p)] = p

    print(f"   Validation images indexed: {len(valid_hashes)}")

    print("🔍 Scanning training set for duplicates and validation leakage...")
    train_duplicates_in_val = []
    train_unique_hashes = {}
    train_internal_duplicates = 0

    for p in TRAIN_IMG.glob("*"):
        if not p.is_file() or p.suffix.lower() not in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
            continue
        h = get_file_md5(p)
        if h in valid_hashes:
            train_duplicates_in_val.append((p, valid_hashes[h]))
        if h in train_unique_hashes:
            train_internal_duplicates += 1
        else:
            train_unique_hashes[h] = p

    leakage_count = len(train_duplicates_in_val)
    print(f"\n🚨 FOUND {leakage_count} TRAIN/VALID LEAKAGE IMAGES (Exact MD5 Match)")
    print(f"⚠️ Internal train duplicate hashes: {train_internal_duplicates}")

    removed_files = 0
    if not dry_run and leakage_count > 0:
        print(f"\n🧹 Purging {leakage_count} leaking images and labels from train/ ...")
        for train_img_path, val_img_path in train_duplicates_in_val:
            stem = train_img_path.stem
            lbl_path = TRAIN_LBL / f"{stem}.txt"
            if train_img_path.exists():
                train_img_path.unlink()
                removed_files += 1
            if lbl_path.exists():
                lbl_path.unlink()

        # Remove stale label cache files so YOLO rebuilds clean cache
        for cache_file in [DATA_DIR / "train" / "labels.cache", DATA_DIR / "valid" / "labels.cache"]:
            if cache_file.exists():
                cache_file.unlink()
                print(f"🔄 Cleared stale cache: {cache_file.name}")

        print(f"✅ Successfully removed {removed_files} leaking images from train split.")

    # Re-verify
    re_leaked = 0
    for p in TRAIN_IMG.glob("*"):
        if p.is_file() and p.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            if get_file_md5(p) in valid_hashes:
                re_leaked += 1

    remaining_train = len(list(TRAIN_IMG.glob("*.jpg")))
    total_valid = len(list(VALID_IMG.glob("*.jpg")))

    # Count boxes by class in train
    train_boxes = Counter()
    for lbl in TRAIN_LBL.glob("*.txt"):
        with open(lbl, "r") as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    train_boxes[parts[0]] += 1

    report = {
        "train_images": remaining_train,
        "valid_images": total_valid,
        "purged_leakage_images": removed_files,
        "remaining_train_valid_leakage": re_leaked,
        "internal_train_duplicates": train_internal_duplicates,
        "train_boxes_by_class": {
            "0 (gun)": train_boxes.get("0", 0),
            "1 (heavy-weapon)": train_boxes.get("1", 0),
            "2 (knife)": train_boxes.get("2", 0)
        },
        "leak_free": re_leaked == 0
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    print("\n------------------------------------------------------------------")
    print(f"✅ Dataset Sanitization Finished:")
    print(f"   Remaining Train Images : {remaining_train}")
    print(f"   Validation Images      : {total_valid}")
    print(f"   Remaining Leakage      : {re_leaked} ({'CLEAN' if re_leaked == 0 else 'WARNING'})")
    print(f"   Report Exported        : {REPORT_PATH}")
    print("------------------------------------------------------------------")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sanitize crime dataset and eliminate data leakage")
    parser.add_argument("--dry-run", action="store_true", help="Report leakage without deleting files")
    parser.add_argument("--verify", action="store_true", help="Only verify leakage status")
    args = parser.parse_args()

    scan_and_clean(dry_run=args.dry_run or args.verify)
