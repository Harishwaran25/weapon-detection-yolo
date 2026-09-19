"""
Dataset Deduplicator
---------------------
The Kaggle ds3 pool turned out to include ari-dasci knife images, creating
exact-duplicate pairs (md5) — including train<->test contamination where a
pseudo-labeled kaggle copy sits in train while the human-labeled original
sits in test/valid.

Removal policy per duplicate group (md5):
  - delete kaggle_* pseudo copies first (human labels are authoritative)
  - delete train copies when a twin lives in valid/ or test/
  - always keep at least one member per group
Victim images AND their label files are removed.

Usage:
  python src/dedupe_dataset.py [--scan /tmp/dup_scan.txt]
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA = PROJECT_ROOT / "data" / "weapon3k"
SPLIT_PRIORITY = {"test": 0, "valid": 1, "train": 2}


def main():
    parser = argparse.ArgumentParser(description="Remove exact-duplicate images (and labels) from weapon3k")
    parser.add_argument("--scan", type=str, default="/tmp/dup_scan.txt",
                        help="md5sum output file (path<space>hash lines)")
    args = parser.parse_args()

    scan = Path(args.scan)
    if not scan.exists():
        # Recompute on the fly
        import hashlib
        groups_tmp = defaultdict(list)
        for img in DATA.rglob("*.jpg"):
            h = hashlib.md5(img.read_bytes()).hexdigest()
            groups_tmp[h].append(str(img.relative_to(DATA)))
        groups = groups_tmp
    else:
        groups = defaultdict(list)
        for line in scan.read_text().splitlines():
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            groups[parts[0]].append(parts[1].strip().lstrip("./"))

    removed, kept_groups = [], 0
    for h, members in groups.items():
        if len(members) < 2:
            continue
        kept_groups += 1

        def split_of(rel):
            return rel.split("/")[0]

        def is_kaggle(rel):
            return Path(rel).stem.startswith("kaggle_")

        # Rank victims: kaggle pseudo first, then by split (train last to keep)
        def rank(rel):
            return (0 if is_kaggle(rel) else 1,
                    SPLIT_PRIORITY.get(split_of(rel), 3), rel)

        ordered = sorted(members, key=rank)
        keep = ordered[-1]  # human-labeled and/or valid/test member survives
        for victim in ordered[:-1]:
            img = DATA / victim
            lbl = img.with_suffix(".txt")
            if img.exists():
                img.unlink()
            if lbl.exists():
                lbl.unlink()
            removed.append(victim)

    report = {
        "duplicate_groups": kept_groups,
        "removed_files": len(removed),
        "removed_by_split": {s: sum(1 for r in removed if r.startswith(s)) for s in ("train", "valid", "test")},
        "removed": sorted(removed),
    }
    out = DATA / "dedupe_report.json"
    out.write_text(json.dumps(report, indent=2))
    print(f"🧹 Removed {len(removed)} duplicate images across {kept_groups} groups "
          f"(by split: {report['removed_by_split']})")
    print(f"   report -> {out}")

    remaining = sum(1 for _ in (DATA / "train" / "images").glob("*"))
    print(f"   train split now holds {remaining} images")


if __name__ == "__main__":
    main()
