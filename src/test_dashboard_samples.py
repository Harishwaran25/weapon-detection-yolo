"""
Dashboard Sample End-to-End Test
---------------------------------
Starts nothing itself — expects the FastAPI server to be running on
http://localhost:8000. Posts every benchmark sample in data/samples to
/api/detect/sample/{filename} and reports whether the top detected threat
matches the expected class inferred from the filename.

Usage:
  python src/test_dashboard_samples.py [--base http://localhost:8000] [--conf 0.35]
"""

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = PROJECT_ROOT / "data" / "samples"


def expected_class(filename: str) -> str:
    """Same inference rule the server's /api/samples uses."""
    name = filename.lower()
    if "heavy" in name:
        return "heavy-weapon"
    if "knife" in name:
        return "knife"
    return "gun"


def main():
    parser = argparse.ArgumentParser(description="E2E test: every dashboard sample must detect its own class")
    parser.add_argument("--base", type=str, default="http://localhost:8000")
    parser.add_argument("--conf", type=float, default=0.35)
    args = parser.parse_args()

    samples = sorted(SAMPLES_DIR.glob("sample_*.jpg"))
    if not samples:
        print("No benchmark samples found in", SAMPLES_DIR)
        return 1

    results = []
    for sample in samples:
        want = expected_class(sample.name)
        try:
            r = requests.post(f"{args.base}/api/detect/sample/{sample.name}",
                              params={"conf": args.conf, "iou": 0.45}, timeout=60)
            data = r.json()
        except Exception as e:
            results.append((sample.name, want, f"ERROR: {e}", 0.0))
            continue
        detections = data.get("detections") or []
        top = detections[0] if detections else None
        got = top["label"] if top else "none"
        conf = top["confidence"] if top else 0.0
        results.append((sample.name, want, got, float(conf)))

    print(f"\n{'sample':34s} {'expected':13s} {'detected':13s} {'conf':>6s}  ok")
    print("-" * 74)
    ok = 0
    for name, want, got, conf in results:
        good = got == want
        ok += good
        print(f"{name:34s} {want:13s} {got:13s} {conf:6.2f}  {'✅' if good else '❌'}")
    print("-" * 74)
    print(f"RESULT: {ok}/{len(results)} samples detected the correct class")
    (PROJECT_ROOT / "outputs" / "e2e_sample_test.json").write_text(
        json.dumps({"pass": ok, "total": len(results),
                    "details": [{"sample": n, "expected": w, "detected": g, "confidence": c}
                                for n, w, g, c in results]}, indent=2))
    return 0 if ok == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
