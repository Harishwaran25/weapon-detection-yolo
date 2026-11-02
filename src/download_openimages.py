"""
Open Images V6 Weapon Dataset Builder
--------------------------------------
Builds a per-class balanced YOLO dataset (gun / heavy-weapon / knife) from
Google Open Images V6 using its public no-auth endpoints:

  gun           <- Handgun   (/m/0gxl3)
  heavy-weapon  <- Rifle     (/m/06c54) + Shotgun (/m/06nrc)
  knife         <- Knife     (/m/04ctx)

Stages (run in order):
  annotations : stream-filter the 2.2 GB train bbox CSV -> data/openimages/annotations.json
  images      : download selected images -> data/openimages/images/  (resumable)
  build       : stratified 80/10/10 split -> data/weapon3k/{train,valid,test} + data.yaml

Usage:
  python src/download_openimages.py --stage annotations
  python src/download_openimages.py --stage images --workers 10
  python src/download_openimages.py --stage build --cap 4000
"""

import argparse
import csv
import io
import json
import random
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
WORK_DIR = DATA_DIR / "openimages"
OUT_DIR = DATA_DIR / "weapon3k"

# Open Images V6 public endpoints (no API key required)
CLASS_DESC_URL = "https://storage.googleapis.com/openimages/v6/oidv6-class-descriptions.csv"
TRAIN_BBOX_URL = "https://storage.googleapis.com/openimages/v6/oidv6-train-annotations-bbox.csv"
IMAGE_URL = "https://s3.amazonaws.com/open-images-dataset/train/{image_id}.jpg"

# Open Images LabelName MID -> our class index (must match data/data.yaml names order)
MID_TO_CLASS = {
    "/m/0gxl3": 0,  # Handgun    -> gun
    "/m/06c54": 1,  # Rifle      -> heavy-weapon
    "/m/06nrc": 1,  # Shotgun    -> heavy-weapon
    "/m/04ctx": 2,  # Knife      -> knife
}
CLASS_NAMES = ["gun", "heavy-weapon", "knife"]

MIN_CONF = 0.5          # bbox confidence floor
MIN_BOX_SIDE = 0.01     # ignore degenerate boxes smaller than 1% of the image side


def stage_annotations() -> None:
    """Stream-filter the Open Images train bbox CSV down to our weapon classes."""
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    out_path = WORK_DIR / "annotations.json"

    boxes = defaultdict(list)  # image_id -> [{cls, xmin, xmax, ymin, ymax}]
    seen = set()
    n_rows = n_kept = 0

    print(f"📥 Streaming {TRAIN_BBOX_URL} (2.2 GB) ...")
    with requests.get(TRAIN_BBOX_URL, stream=True, timeout=120) as r:
        r.raise_for_status()
        buf = io.StringIO()
        for chunk in r.iter_lines(decode_unicode=True):
            if not chunk:
                continue
            n_rows += 1
            buf.write(chunk)
            buf.seek(0)
            row = next(csv.reader(buf))
            buf.seek(0)
            buf.truncate(0)
            if n_rows == 1 or row[2] not in MID_TO_CLASS:
                continue
            try:
                conf = float(row[3])
                xmin, xmax = float(row[4]), float(row[5])
                ymin, ymax = float(row[6]), float(row[7])
                is_group_of = int(row[10])
                is_depiction = int(row[11])
            except (ValueError, IndexError):
                continue
            if conf < MIN_CONF or is_group_of or is_depiction:
                continue
            if (xmax - xmin) < MIN_BOX_SIDE or (ymax - ymin) < MIN_BOX_SIDE:
                continue
            image_id = row[0]
            box = {"cls": MID_TO_CLASS[row[2]], "xmin": xmin, "xmax": xmax,
                   "ymin": ymin, "ymax": ymax}
            key = (image_id, box["cls"], round(xmin, 4), round(xmax, 4),
                   round(ymin, 4), round(ymax, 4))
            if key in seen:
                continue
            seen.add(key)
            boxes[image_id].append(box)
            n_kept += 1
            if n_kept % 5000 == 0:
                print(f"   ... {n_kept} boxes kept ({len(boxes)} images)", flush=True)

    counts = defaultdict(int)
    for image_boxes in boxes.values():
        for b in image_boxes:
            counts[b["cls"]] += 1

    payload = {
        "images": dict(boxes),
        "box_counts": dict(counts),
        "image_counts": {
            CLASS_NAMES[c]: sum(1 for ib in boxes.values() if any(b["cls"] == c for b in ib))
            for c in range(3)
        },
    }
    out_path.write_text(json.dumps(payload))
    size_mb = out_path.stat().st_size / 1e6
    print(f"\n✅ Saved {n_kept} boxes across {len(boxes)} images -> {out_path} ({size_mb:.1f} MB)")
    for c, name in enumerate(CLASS_NAMES):
        print(f"   {name:13s} images: {payload['image_counts'][name]:6d}   boxes: {counts.get(c, 0):6d}")


def _download_one(session: requests.Session, image_id: str) -> str | None:
    dest = WORK_DIR / "images" / f"{image_id}.jpg"
    if dest.exists() and dest.stat().st_size > 0:
        return "cached"
    url = IMAGE_URL.format(image_id=image_id)
    for attempt in range(3):
        try:
            r = session.get(url, timeout=60)
            if r.status_code == 200 and r.content[:2] == b"\xff\xd8":
                dest.write_bytes(r.content)
                return "ok"
            if r.status_code == 404:
                return None
        except requests.RequestException:
            pass
    return None


def stage_images(cap: int) -> None:
    """Select up to `cap` images per class and download them (resumable)."""
    ann = json.loads((WORK_DIR / "annotations.json").read_text())
    boxes = ann["images"]

    # Greedy selection by class scarcity: heavy-weapon first, then gun, then knife.
    order = [1, 0, 2]
    selected: set[str] = set()
    class_picked = defaultdict(int)
    for cls in order:
        for image_id, image_boxes in boxes.items():
            if class_picked[cls] >= cap:
                break
            if image_id in selected:
                continue
            if any(b["cls"] == cls for b in image_boxes):
                selected.add(image_id)
                class_picked[cls] += 1

    print(f"🎯 Selected {len(selected)} images. Per-class selection counts:")
    for c, name in enumerate(CLASS_NAMES):
        n = sum(1 for image_id in selected if any(b["cls"] == c for b in boxes[image_id]))
        print(f"   {name:13s} {n}")

    (WORK_DIR / "selected.json").write_text(json.dumps(sorted(selected)))
    img_dir = WORK_DIR / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    done = failed = 0
    print(f"📥 Downloading {len(selected)} images with 10 workers ...")
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(_download_one, session, image_id): image_id for image_id in selected}
        for fut in as_completed(futures):
            result = fut.result()
            if result is None:
                failed += 1
            else:
                done += 1
            if (done + failed) % 500 == 0:
                print(f"   ... {done} downloaded ({failed} unavailable)", flush=True)
    print(f"\n✅ {done} images ready in {img_dir} ({failed} unavailable/skipped)")


def stage_build() -> None:
    """Stratified 80/10/10 train/valid/test split -> YOLO dataset + data.yaml."""
    ann = json.loads((WORK_DIR / "annotations.json").read_text())
    boxes = ann["images"]
    selected = json.loads((WORK_DIR / "selected.json").read_text())
    img_dir = WORK_DIR / "images"

    # Only keep images that actually downloaded as valid JPEGs
    selected = [i for i in selected if (img_dir / f"{i}.jpg").exists()]
    print(f"📦 {len(selected)} downloaded images available for splitting")

    # Stratify by the scarcest class each image contains, then split 80/10/10
    by_primary = defaultdict(list)
    for image_id in selected:
        classes = {b["cls"] for b in boxes[image_id]}
        primary = min(classes)  # 1 (heavy-weapon) scarcest, then 0 (gun), then 2 (knife)
        by_primary[primary].append(image_id)

    rng = random.Random(42)
    splits = {"train": defaultdict(int), "valid": defaultdict(int), "test": defaultdict(int)}
    assignment: dict[str, str] = {}
    for cls, ids in sorted(by_primary.items()):
        ids = sorted(ids)
        rng.shuffle(ids)
        n = len(ids)
        n_test, n_valid = int(n * 0.10), int(n * 0.10)
        for image_id, split in zip(ids, ["test"] * n_test + ["valid"] * n_valid + ["train"] * (n - n_test - n_valid)):
            assignment[image_id] = split
            for c in {b["cls"] for b in boxes[image_id]}:
                splits[split][c] += 1

    for split in ("train", "valid", "test"):
        (OUT_DIR / split / "images").mkdir(parents=True, exist_ok=True)
        (OUT_DIR / split / "labels").mkdir(parents=True, exist_ok=True)

    copied = 0
    for image_id, split in assignment.items():
        src = img_dir / f"{image_id}.jpg"
        dst_img = OUT_DIR / split / "images" / f"{image_id}.jpg"
        dst_lbl = OUT_DIR / split / "labels" / f"{image_id}.txt"
        if not dst_img.exists():
            src.replace(dst_img) if src.exists() else None
        lines = []
        for b in boxes[image_id]:
            w = b["xmax"] - b["xmin"]
            h = b["ymax"] - b["ymin"]
            cx = b["xmin"] + w / 2
            cy = b["ymin"] + h / 2
            lines.append(f"{b['cls']} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
        dst_lbl.write_text("\n".join(lines) + "\n")
        copied += 1

    yaml_path = OUT_DIR / "data.yaml"
    yaml_path.write_text(
        f"# Balanced weapon dataset built from Open Images V6 (src/download_openimages.py)\n"
        f"path: {OUT_DIR}\ntrain: train/images\nval: valid/images\ntest: test/images\n\nnc: 3\nnames: ['gun', 'heavy-weapon', 'knife']\n"
    )

    print(f"✅ Built dataset at {OUT_DIR} ({copied} images)")
    for split in ("train", "valid", "test"):
        per = "  ".join(f"{CLASS_NAMES[c]}: {splits[split].get(c, 0)}" for c in range(3))
        total = sum(splits[split].values())
        print(f"   {split:5s} ({total:5d} img)  {per}")
    print(f"   data.yaml -> {yaml_path}")


def main():
    parser = argparse.ArgumentParser(description="Build balanced weapon dataset from Open Images V6")
    parser.add_argument("--stage", choices=["annotations", "images", "build", "all"], default="all")
    parser.add_argument("--cap", type=int, default=4000, help="Max images selected per class")
    args = parser.parse_args()

    if args.stage in ("annotations", "all"):
        stage_annotations()
    if args.stage in ("images", "all"):
        stage_images(args.cap)
    if args.stage in ("build", "all"):
        stage_build()


if __name__ == "__main__":
    main()
