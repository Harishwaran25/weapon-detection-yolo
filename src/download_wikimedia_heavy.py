"""
Wikimedia Commons Weapon Supplement (pseudo-labeled)
-----------------------------------------------------
Supplements scarce classes with freely licensed (CC) weapon photos from
Wikimedia Commons, pseudo-labeled by the repo's own exported model
(models/best.tflite). Common use: heavy-weapon (rifle/shotgun categories),
gun (Pistols categories).

Pseudo-labels are used for TRAINING only — validation/test metrics always come
from human-annotated sources (Open Images / ari-dasci).

Usage:
  python src/download_wikimedia_heavy.py --target-class heavy-weapon --per-category 600
  python src/download_wikimedia_heavy.py --target-class gun \
      --categories "Pistols,Revolvers,Semi-automatic pistols" --per-category 800
"""

import argparse
import json
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import cv2
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "best.tflite"

CLASS_IDS = {"gun": 0, "heavy-weapon": 1, "knife": 2}

API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "SentinelAI-DatasetBuilder/1.0 (educational weapon-detection research)"}

# Minimum pseudo-label confidence floor (teacher precision guard)
MIN_CONF_FLOOR = 0.55


def _api_query(session: requests.Session, params: dict) -> dict | None:
    """One API request with 429 backoff. Returns json dict or None."""
    for attempt in range(6):
        try:
            r = session.get(API, params=params, timeout=30)
            if r.status_code == 429:
                wait = 15 * (attempt + 1)
                print(f"   ⏳ Rate limited, waiting {wait}s ...", flush=True)
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            time.sleep(5 * (attempt + 1))
    return None


def list_search_files(session: requests.Session, term: str, limit: int) -> list[dict]:
    """Full-text search Commons files (namespace 6) for a term — broad coverage."""
    results, continue_from = [], {}
    while len(results) < limit:
        params = {
            "action": "query", "format": "json",
            "generator": "search", "gsrsearch": f"{term} filetype:bitmap",
            "gsrnamespace": 6, "gsrlimit": 100,
            "prop": "imageinfo", "iiprop": "url|size|mime", "iiurlwidth": 1024,
            **continue_from,
        }
        data = _api_query(session, params)
        if not data:
            break
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            break
        for page in pages.values():
            info = (page.get("imageinfo") or [{}])[0]
            if info.get("mime") != "image/jpeg":
                continue
            if info.get("width", 0) < 600:
                continue
            results.append({
                "title": page.get("title", "").replace(" ", "_"),
                "url": info.get("thumburl") or info.get("url"),
            })
        cont = data.get("continue")
        if not cont:
            break
        continue_from = cont
        time.sleep(2)  # be gentle with the Commons API
    return results[:limit]


def list_category_files(session: requests.Session, category: str, limit: int) -> list[dict]:
    """List image files (JPEG, >=600px wide) directly inside a Commons category."""
    results, continue_from = [], {}
    while len(results) < limit:
        params = {
            "action": "query", "format": "json",
            "generator": "categorymembers", "gcmtype": "file",
            "gcmtitle": f"Category:{category}", "gcmlimit": 100,
            "prop": "imageinfo", "iiprop": "url|size|mime", "iiurlwidth": 1024,
            **continue_from,
        }
        data = _api_query(session, params)
        if not data:
            break
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            break
        for page in pages.values():
            info = (page.get("imageinfo") or [{}])[0]
            if info.get("mime") != "image/jpeg":
                continue
            if info.get("width", 0) < 600:
                continue
            results.append({
                "title": page.get("title", "").replace(" ", "_"),
                "url": info.get("thumburl") or info.get("url"),
            })
        cont = data.get("continue")
        if not cont:
            break
        continue_from = cont
        time.sleep(2)  # be gentle with the Commons API
    return results[:limit]


def download_image(session: requests.Session, url: str, dest: Path) -> bool:
    for _ in range(3):
        try:
            r = session.get(url, timeout=60)
            if r.status_code == 200 and r.content[:2] == b"\xff\xd8":
                dest.write_bytes(r.content)
                return True
        except requests.RequestException:
            time.sleep(1)
    return False


DEFAULT_SEARCH_TERMS = {
    "heavy-weapon": "assault rifle,rifle,shotgun,submachine gun,machine gun,sniper rifle",
    "gun": "pistol,revolver,handgun",
    "knife": "knife,combat knife,utility knife",
}


def main():
    parser = argparse.ArgumentParser(description="Pseudo-label Commons weapon photos with best.tflite")
    parser.add_argument("--target-class", choices=list(CLASS_IDS), default="heavy-weapon",
                        help="Which class to keep pseudo-labels for")
    parser.add_argument("--search-terms", type=str, default=None,
                        help="Comma-separated Commons search terms (defaults chosen per target class)")
    parser.add_argument("--categories", type=str, default="",
                        help="Optional Commons categories to also pull direct files from")
    parser.add_argument("--per-term", type=int, default=600)
    parser.add_argument("--conf", type=float, default=MIN_CONF_FLOOR)
    parser.add_argument("--refresh", action="store_true", help="Re-list Commons candidates instead of using the cache")
    args = parser.parse_args()

    target_id = CLASS_IDS[args.target_class]
    terms = [t.strip() for t in (args.search_terms or DEFAULT_SEARCH_TERMS[args.target_class]).split(",") if t.strip()]
    out_dir = PROJECT_ROOT / "data" / f"wikimedia_{args.target_class.replace('-', '_')}"
    (out_dir / "images").mkdir(parents=True, exist_ok=True)
    (out_dir / "labels").mkdir(parents=True, exist_ok=True)

    # Lazy import so the script also runs before TF is needed
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from detect_tflite import TFLiteYOLO

    detector = TFLiteYOLO(str(MODEL_PATH), conf_thres=0.25)
    print(f"🧠 Teacher model: {MODEL_PATH.name} (input {detector.width}x{detector.height})")
    print(f"🎯 Target class: {args.target_class} (id {target_id}), conf >= {args.conf}", flush=True)

    session = requests.Session()
    session.headers.update(HEADERS)

    cache_path = out_dir / "candidates.json"
    if cache_path.exists() and not args.refresh:
        candidates = json.loads(cache_path.read_text())
        print(f"♻️ Reusing cached candidate list ({len(candidates)} entries) — pass --refresh to re-list", flush=True)
    else:
        candidates = {}
        for term in terms:
            files = list_search_files(session, term, args.per_term)
            print(f"🔍 Search '{term}': {len(files)} jpeg candidates", flush=True)
            for f in files:
                candidates[f["title"]] = f["url"]
        for category in [c.strip() for c in args.categories.split(",") if c.strip()]:
            files = list_category_files(session, category, args.per_term)
            print(f"📂 Category '{category}': {len(files)} jpeg candidates", flush=True)
            for f in files:
                candidates[f["title"]] = f["url"]
        cache_path.write_text(json.dumps(candidates))

    print(f"🎯 {len(candidates)} unique candidate images", flush=True)

    # ---- Phase 1: parallel download (8 workers) ------------------------------
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def fetch(item):
        title, url = item
        safe_name = title.rsplit(".", 1)[0].replace("/", "_")[-80:] + ".jpg"
        dest = out_dir / "images" / safe_name
        if dest.exists():
            return "cached"
        s2 = requests.Session()
        s2.headers.update(HEADERS)
        return "ok" if download_image(s2, url, dest) else "failed"

    downloaded = cached = failed = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(fetch, item) for item in sorted(candidates.items())]
        for n, fut in enumerate(as_completed(futures), 1):
            result = fut.result()
            if result == "ok":
                downloaded += 1
            elif result == "cached":
                cached += 1
            else:
                failed += 1
            if n % 200 == 0:
                print(f"   ⬇️ {n}/{len(candidates)} fetched ({downloaded} new, {failed} failed)", flush=True)
    print(f"⬇️ Downloads done: {downloaded} new, {cached} cached, {failed} failed", flush=True)

    # ---- Phase 2: sequential pseudo-labeling (TFLite, ~100ms/image) ----------
    kept = rejected = 0
    for i, img_path in enumerate(sorted((out_dir / "images").glob("*.jpg")), 1):
        lbl_path = out_dir / "labels" / (img_path.stem + ".txt")
        if lbl_path.exists():
            kept += 1
            continue
        img = cv2.imread(str(img_path))
        if img is None:
            img_path.unlink(missing_ok=True)
            failed += 1
            continue
        h, w = img.shape[:2]

        detections, _ = detector.predict(img)
        boxes = [d for d in detections
                 if d["label"] == args.target_class and d["confidence"] >= args.conf]
        if not boxes:
            img_path.unlink(missing_ok=True)
            rejected += 1
            continue

        lines = []
        for d in boxes:
            x1, y1, x2, y2 = d["bbox"]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            bw, bh = (x2 - x1) / w, (y2 - y1) / h
            if bw <= 0 or bh <= 0:
                continue
            cx, cy = (x1 + x2) / 2 / w, (y1 + y2) / 2 / h
            lines.append(f"{target_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
        if not lines:
            img_path.unlink(missing_ok=True)
            rejected += 1
            continue

        lbl_path.write_text("\n".join(lines) + "\n")
        kept += 1
        if i % 200 == 0:
            print(f"   🏷️ {i} labeled, kept {kept}, rejected {rejected}", flush=True)

    report = {"candidates": len(candidates), "kept": kept, "rejected": rejected, "failed": failed,
              "conf": args.conf, "terms": terms, "target_class": args.target_class}
    (out_dir / "report.json").write_text(json.dumps(report, indent=2))
    print(f"\n✅ Kept {kept} pseudo-labeled {args.target_class} images -> {out_dir}")
    print(f"   (rejected {rejected} without confident box, {failed} download failures)")


if __name__ == "__main__":
    main()
