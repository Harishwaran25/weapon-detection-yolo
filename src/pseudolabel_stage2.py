"""
Stage-2 Pseudo-Labeler (self-training)
---------------------------------------
Uses the stage-1 trained YOLOv5 model (runs/train/weapon3k-s1/weights/best.pt)
to pseudo-label supplementary image pools that only carry coarse or no class
labels, then stores confident detections as YOLO training data INSIDE the repo:

  kaggle  : 23k single-class 'Weapon' images (Kaggle hub cache, read-only)
  commons : extra Wikimedia Commons search terms (downloaded fresh)
  ari-knife-classification: knife images from ari-dasci classification set

All output goes to data/stage2_pseudo/<source>/{images,labels} and is merged
into the TRAIN split only by src/build_master_dataset.py. Validation/test
always stay human-labeled.

Usage:
  python src/pseudolabel_stage2.py --source kaggle \
      --images /home/harish/.cache/kagglehub/datasets/.../dataset_merged/train/images
  python src/pseudolabel_stage2.py --source commons \
      --search-terms "carbine,bolt-action rifle,hunting rifle,pump-action shotgun"
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_ROOT = PROJECT_ROOT / "data" / "stage2_pseudo"
WEIGHTS = PROJECT_ROOT / "runs" / "train" / "weapon3k-s1" / "weights" / "best.pt"
CLASS_NAMES = ["gun", "heavy-weapon", "knife"]

API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "SentinelAI-DatasetBuilder/1.0 (educational weapon-detection research)"}
MIN_CONF_FLOOR = 0.55


def load_stage1_model():
    sys.path.insert(0, str(PROJECT_ROOT / "yolov5"))
    import torch
    model = torch.hub.load(str(PROJECT_ROOT / "yolov5"), "custom",
                           path=str(WEIGHTS), source="local", device=0)
    model.conf = 0.30   # low floor; per-class guard applied below
    model.iou = 0.50
    return model


def label_image(model, img_path: Path, conf_floor: float):
    """Return YOLO lines for confident detections, or None."""
    import cv2
    img = cv2.imread(str(img_path))
    if img is None:
        return None
    h, w = img.shape[:2]
    results = model(img[:, :, ::-1])  # RGB
    lines = []
    for det in results.xyxy[0].tolist():
        x1, y1, x2, y2, conf, cls = det
        label = CLASS_NAMES[int(cls)] if int(cls) < len(CLASS_NAMES) else None
        if label is None or conf < conf_floor:
            continue
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        bw, bh = (x2 - x1) / w, (y2 - y1) / h
        if bw <= 0 or bh <= 0:
            continue
        cx, cy = (x1 + x2) / 2 / w, (y1 + y2) / 2 / h
        lines.append(f"{int(cls)} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
    return lines or None


def run_pool(model, pool_name: str, image_iter, conf_floor: float, move: bool = False):
    """Pseudo-label an iterable of (key, image_path[, copy_path]) into OUT_ROOT/pool."""
    import cv2
    out_dir = OUT_ROOT / pool_name
    (out_dir / "images").mkdir(parents=True, exist_ok=True)
    (out_dir / "labels").mkdir(parents=True, exist_ok=True)

    kept = rejected = failed = 0
    for n, item in enumerate(image_iter, 1):
        key, img_path = item[0], Path(item[1])
        dst_img = out_dir / "images" / f"{key}.jpg"
        lbl_path = out_dir / "labels" / f"{key}.txt"
        if dst_img.exists() and lbl_path.exists():
            kept += 1
            continue
        try:
            lines = label_image(model, img_path, conf_floor)
        except Exception:
            failed += 1
            continue
        if not lines:
            rejected += 1
            continue
        try:
            if img_path.suffix.lower() in (".jpg", ".jpeg"):
                if move:
                    shutil.move(str(img_path), str(dst_img))
                else:
                    shutil.copyfile(img_path, dst_img)
            else:
                # Re-encode non-JPEG (e.g. PNG) sources as real JPEGs
                img = cv2.imread(str(img_path))
                if img is None:
                    failed += 1
                    continue
                cv2.imwrite(str(dst_img), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
        except OSError:
            failed += 1
            continue
        lbl_path.write_text("\n".join(lines) + "\n")
        kept += 1
        if n % 500 == 0:
            print(f"   {pool_name}: {n} processed, kept {kept}, rejected {rejected}, failed {failed}", flush=True)

    print(f"✅ {pool_name}: kept {kept}, rejected {rejected}, failed {failed} -> {out_dir}", flush=True)
    return kept


def iter_dir_images(dir_path: Path, prefix: str):
    for p in sorted(dir_path.iterdir()):
        if p.suffix.lower() in (".jpg", ".jpeg", ".png"):
            yield f"{prefix}_{p.stem}", p


def list_search_files(session: requests.Session, term: str, limit: int) -> list[dict]:
    """Commons full-text file search (same API pattern as download_wikimedia_heavy)."""
    results, continue_from = [], {}
    while len(results) < limit:
        params = {
            "action": "query", "format": "json",
            "generator": "search", "gsrsearch": f"{term} filetype:bitmap",
            "gsrnamespace": 6, "gsrlimit": 100,
            "prop": "imageinfo", "iiprop": "url|size|mime", "iiurlwidth": 1024,
            **continue_from,
        }
        data = None
        for attempt in range(5):
            try:
                r = session.get(API, params=params, timeout=30)
                if r.status_code == 429:
                    time.sleep(15 * (attempt + 1))
                    continue
                r.raise_for_status()
                data = r.json()
                break
            except requests.RequestException:
                time.sleep(5 * (attempt + 1))
        if not data:
            break
        for page in data.get("query", {}).get("pages", {}).values():
            info = (page.get("imageinfo") or [{}])[0]
            if info.get("mime") != "image/jpeg" or info.get("width", 0) < 600:
                continue
            results.append({"title": page.get("title", "").replace(" ", "_"),
                            "url": info.get("thumburl") or info.get("url")})
        cont = data.get("continue")
        if not cont:
            break
        continue_from = cont
        time.sleep(2)
    return results[:limit]


def run_commons(model, terms: list[str], per_term: int, conf_floor: float):
    """Download fresh Commons candidates with the requests lib, pseudo-label each."""
    import cv2
    out_dir = OUT_ROOT / "commons"
    (out_dir / "images").mkdir(parents=True, exist_ok=True)
    (out_dir / "labels").mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(HEADERS)
    candidates: dict[str, str] = {}
    for term in terms:
        for f in list_search_files(session, term, per_term):
            candidates[f["title"]] = f["url"]
    print(f"🔍 {len(candidates)} unique Commons candidates", flush=True)

    kept = rejected = failed = 0
    for n, (title, url) in enumerate(sorted(candidates.items()), 1):
        time.sleep(0.3)
        safe_name = title.rsplit(".", 1)[0].replace("/", "_")[-80:]
        dst_img = out_dir / "images" / f"{safe_name}.jpg"
        lbl_path = out_dir / "labels" / f"{safe_name}.txt"
        if dst_img.exists() and lbl_path.exists():
            kept += 1
            continue
        try:
            r = session.get(url, timeout=60)
        except requests.RequestException:
            failed += 1
            continue
        if r.status_code != 200 or r.content[:2] != b"\xff\xd8":
            failed += 1
            continue
        dst_img.write_bytes(r.content)
        lines = label_image(model, dst_img, conf_floor)
        if not lines:
            dst_img.unlink(missing_ok=True)
            rejected += 1
            continue
        lbl_path.write_text("\n".join(lines) + "\n")
        kept += 1
        if n % 500 == 0:
            print(f"   commons: {n}/{len(candidates)} processed, kept {kept}, rejected {rejected}", flush=True)
    print(f"✅ commons: kept {kept}, rejected {rejected}, failed {failed}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Stage-2 pseudo-labeling with the stage-1 model")
    parser.add_argument("--source", choices=["kaggle", "ari-knife-classification", "commons"], required=True)
    parser.add_argument("--images", type=str, default="",
                        help="Directory of images (kaggle / ari-knife-classification pools)")
    parser.add_argument("--search-terms", type=str, default="carbine,bolt-action rifle,hunting rifle,pump-action shotgun,lever-action rifle,rifle")
    parser.add_argument("--per-term", type=int, default=800)
    parser.add_argument("--conf", type=float, default=MIN_CONF_FLOOR)
    args = parser.parse_args()

    if not WEIGHTS.exists():
        raise FileNotFoundError(f"Stage-1 weights not found: {WEIGHTS}")
    print(f"🧠 Teacher: {WEIGHTS}  (conf >= {args.conf})", flush=True)
    model = load_stage1_model()

    if args.source == "kaggle":
        img_dir = Path(args.images)
        if not img_dir.exists():
            raise FileNotFoundError(f"Image dir not found: {img_dir}")
        # Copy (cache is outside the repo and stays untouched; source=move=False)
        run_pool(model, "kaggle", iter_dir_images(img_dir, "kg"), args.conf, move=False)
    elif args.source == "ari-knife-classification":
        img_dir = Path(args.images)
        if not img_dir.exists():
            raise FileNotFoundError(f"Image dir not found: {img_dir}")
        run_pool(model, "knife_class", iter_dir_images(img_dir, "kc"), args.conf, move=True)
    else:
        run_commons(model, [t.strip() for t in args.search_terms.split(",") if t.strip()],
                    args.per_term, args.conf)


if __name__ == "__main__":
    main()
