"""
Master Weapon Dataset Builder
------------------------------
Merges every acquired source into the final YOLO dataset at data/weapon3k:

  gun / heavy-weapon / knife          (class order must match src/server.py CLASS_MAP)
  1. Open Images V6  (human labels)   data/openimages/annotations.json + images/
  2. ari-dasci OD-WeaponDetection (human labels, Pascal VOC)  data/external/od-weapon-detection/
     -> "Pistol detection" (class 0) and "Knife_detection" (class 2) subsets
  3. Wikimedia Commons (pseudo labels, teacher = best.tflite) data/wikimedia_heavy/
     -> TRAIN split only; validation/test always stay human-labeled.

Split: per-class stratified 80/10/10 (train/valid/test).

Usage:
  python src/build_master_dataset.py --cap 4000
"""

import argparse
import json
import random
import shutil
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OI_DIR = DATA_DIR / "openimages"
ARI_DIR = DATA_DIR / "external" / "od-weapon-detection"
WM_DIR = DATA_DIR / "wikimedia_heavy"
OUT_DIR = DATA_DIR / "weapon3k"

CLASS_NAMES = ["gun", "heavy-weapon", "knife"]
# ari-dasci VOC object names -> our class ids
ARI_NAME_TO_CLASS = {"pistol": 0, "knive": 2, "knife": 2}


def select_openimages(cap: int) -> tuple[dict, dict]:
    """Greedy per-class selection (scarcest first) from Open Images annotations."""
    ann = json.loads((OI_DIR / "annotations.json").read_text())
    boxes = ann["images"]

    order = [1, 0, 2]  # heavy-weapon is scarcest -> prioritized
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

    return {image_id: boxes[image_id] for image_id in selected}, class_picked


def collect_ari() -> tuple[dict, dict]:
    """Parse ari-dasci Pascal VOC subsets (Pistol detection / Knife detection)."""
    entries: dict[str, list] = {}
    counts = defaultdict(int)
    if not ARI_DIR.exists():
        print(f"⚠️ ari-dasci dir not found at {ARI_DIR} — skipping")
        return entries, counts

    # Case-insensitive stem index (knife annotations reference .JPG, pistols .jpg)
    img_by_stem = {p.stem: p for p in ARI_DIR.rglob("*") if p.suffix.lower() in (".jpg", ".jpeg")}

    for subset_dir in sorted(ARI_DIR.iterdir()):
        if not subset_dir.is_dir():
            continue
        name = subset_dir.name.lower()
        if "pistol" in name and "detection" in name:
            cls = 0
        elif "knife" in name and "detection" in name:
            cls = 2
        else:
            continue

        xmls = list(subset_dir.rglob("*.xml"))
        print(f"📂 ari-dasci '{subset_dir.name}': {len(xmls)} VOC files")
        for xml_path in xmls:
            try:
                root = ET.parse(xml_path).getroot()
            except ET.ParseError:
                continue

            img_path = None
            fname = root.findtext("filename")
            if fname:
                img_path = img_by_stem.get(Path(fname).stem)
            if img_path is None:
                img_path = img_by_stem.get(xml_path.stem)
            if img_path is None:
                continue

            size = root.find("size")
            w = int(float(size.find("width").text)) if size is not None and size.find("width") is not None else 0
            h = int(float(size.find("height").text)) if size is not None and size.find("height") is not None else 0

            boxes = []
            for obj in root.iter("object"):
                obj_name = (obj.findtext("name") or "").strip().lower()
                if obj_name not in ARI_NAME_TO_CLASS:
                    continue
                bnd = obj.find("bndbox")
                if bnd is None:
                    continue
                xmin = float(bnd.findtext("xmin", 0)); xmax = float(bnd.findtext("xmax", 0))
                ymin = float(bnd.findtext("ymin", 0)); ymax = float(bnd.findtext("ymax", 0))
                if w <= 0 or h <= 0:
                    continue
                boxes.append({"cls": ARI_NAME_TO_CLASS[obj_name],
                              "xmin": xmin / w, "xmax": xmax / w,
                              "ymin": ymin / h, "ymax": ymax / h})
            if not boxes:
                continue
            key = f"ad_{subset_dir.name.replace(' ', '_')}_{img_path.stem}"
            entries[key] = {"boxes": boxes, "img_path": img_path, "fake_size": (w, h)}
            for b in boxes:
                counts[b["cls"]] += 1
    return entries, counts


def verify_size(path: Path, fake: tuple[int, int] | None) -> tuple[int, int]:
    try:
        with Image.open(path) as im:
            return im.size
    except Exception:
        return fake or (0, 0)


def main():
    parser = argparse.ArgumentParser(description="Merge all sources into data/weapon3k")
    parser.add_argument("--cap", type=int, default=4000, help="Max Open Images picks per class")
    parser.add_argument("--out", type=str, default=str(OUT_DIR), help="Output dataset dir")
    args = parser.parse_args()
    out_dir = Path(args.out)

    rng = random.Random(42)
    for split in ("train", "valid", "test"):
        (out_dir / split / "images").mkdir(parents=True, exist_ok=True)
        (out_dir / split / "labels").mkdir(parents=True, exist_ok=True)

    per_split_class = {s: defaultdict(int) for s in ("train", "valid", "test")}
    source_stats = defaultdict(lambda: defaultdict(int))
    assignment: list[tuple[str, Path, list, str]] = []  # (key, img_path, boxes, split)

    def stratified_split(keys_by_class: dict[int, list[str]]) -> dict[str, str]:
        """Assign each key to train/valid/test balancing classes within each split."""
        split_of: dict[str, str] = {}
        for cls, keys in sorted(keys_by_class.items()):
            keys = sorted(keys)
            rng.shuffle(keys)
            n = len(keys)
            n_test, n_valid = int(n * 0.10), int(n * 0.10)
            for key, split in zip(keys, ["test"] * n_test + ["valid"] * n_valid + ["train"] * (n - n_test - n_valid)):
                split_of[key] = split
        return split_of

    # ---- Source 1: Open Images (human) ------------------------------------
    oi_selected, oi_picked = select_openimages(args.cap)
    oi_available = {}
    for image_id, image_boxes in oi_selected.items():
        p = OI_DIR / "images" / f"{image_id}.jpg"
        if p.exists():
            oi_available[image_id] = image_boxes
    print(f"🔗 Open Images: {len(oi_available)} images (selection per class: {dict(oi_picked)})")

    keys_by_class = defaultdict(list)
    for image_id in oi_available:
        for c in {b["cls"] for b in oi_available[image_id]}:
            keys_by_class[c].append(f"oi_{image_id}")
    oi_split = stratified_split(keys_by_class)
    for image_id, image_boxes in oi_available.items():
        key = f"oi_{image_id}"
        assignment.append((key, OI_DIR / "images" / f"{image_id}.jpg", image_boxes, oi_split[key]))
        source_stats["openimages"][oi_split[key]] += 1

    # ---- Source 2: ari-dasci (human) ---------------------------------------
    ari_entries, ari_counts = collect_ari()
    print(f"🔗 ari-dasci: {len(ari_entries)} images, boxes/class: {dict(ari_counts)}")
    keys_by_class = defaultdict(list)
    for key, entry in ari_entries.items():
        for c in {b["cls"] for b in entry["boxes"]}:
            keys_by_class[c].append(key)
    ari_split = stratified_split(keys_by_class)
    for key, entry in ari_entries.items():
        assignment.append((key, Path(entry["img_path"]), entry["boxes"], ari_split[key]))
        source_stats["ari-dasci"][ari_split[key]] += 1

    # ---- Source 3: Pseudo-labeled pools (train only) -------------------------
    # wikimedia_* dirs (teacher = old best.tflite) and stage2_pseudo/* dirs
    # (teacher = stage-1 model): kaggle / knife_class / commons pools.
    wm_count = 0
    pseudo_roots = sorted(DATA_DIR.glob("wikimedia_*")) + sorted((DATA_DIR / "stage2_pseudo").glob("*")) \
        if (DATA_DIR / "stage2_pseudo").exists() else sorted(DATA_DIR.glob("wikimedia_*"))
    for wm_root in pseudo_roots:
        if not (wm_root / "labels").exists():
            continue
        for lbl_path in sorted((wm_root / "labels").glob("*.txt")):
            img_path = wm_root / "images" / (lbl_path.stem + ".jpg")
            if not img_path.exists():
                continue
            boxes = []
            for line in lbl_path.read_text().strip().splitlines():
                parts = line.split()
                if len(parts) != 5:
                    continue
                c, cx, cy, bw, bh = int(parts[0]), *map(float, parts[1:])
                boxes.append({"cls": c, "xmin": cx - bw / 2, "xmax": cx + bw / 2,
                              "ymin": cy - bh / 2, "ymax": cy + bh / 2})
            if boxes:
                assignment.append((f"wm_{lbl_path.stem}", img_path, boxes, "train"))
                wm_count += 1
    print(f"🔗 Pseudo-labeled supplements: {wm_count} images (train only)")

    # ---- Write dataset -------------------------------------------------------
    total = {"train": 0, "valid": 0, "test": 0}
    for key, img_path, image_boxes, split in assignment:
        img_size = None
        lines = []
        for b in image_boxes:
            w = b["xmax"] - b["xmin"]
            h = b["ymax"] - b["ymin"]
            if w <= 0 or h <= 0:
                continue
            cx, cy = b["xmin"] + w / 2, b["ymin"] + h / 2
            lines.append(f"{b['cls']} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
            per_split_class[split][b["cls"]] += 1
        if not lines:
            continue
        ext = img_path.suffix.lower() or ".jpg"
        dst_img = out_dir / split / "images" / f"{key}{ext}"
        if not dst_img.exists():
            try:
                # Move (not copy): all sources live inside the repo and keeping
                # the originals would double disk usage (disk is tight).
                shutil.move(str(img_path), str(dst_img))
            except OSError:
                continue
        (out_dir / split / "labels" / f"{key}.txt").write_text("\n".join(lines) + "\n")
        total[split] += 1

    yaml_path = out_dir / "data.yaml"
    yaml_path.write_text(
        "# Sentinel AI balanced weapon dataset (Open Images V6 + ari-dasci + Wikimedia pseudo-labels)\n"
        f"path: {out_dir.resolve()}\ntrain: train/images\nval: valid/images\ntest: test/images\n\nnc: 3\nnames: ['gun', 'heavy-weapon', 'knife']\n"
    )

    report = {
        "sources": {k: dict(v) for k, v in source_stats.items()},
        "wikimedia_train_only": wm_count,
        "images_per_split": total,
        "boxes_per_split_class": {s: {CLASS_NAMES[c]: per_split_class[s].get(c, 0) for c in range(3)}
                                  for s in total},
    }
    (out_dir / "build_report.json").write_text(json.dumps(report, indent=2))

    print(f"\n✅ Master dataset written to {out_dir}")
    for split in ("train", "valid", "test"):
        imgs = total[split]
        per = "  ".join(f"{CLASS_NAMES[c]}: {per_split_class[split].get(c, 0)}" for c in range(3))
        print(f"   {split:5s} ({imgs:5d} images)  boxes -> {per}")
    print(f"   data.yaml -> {yaml_path}")


if __name__ == "__main__":
    main()
