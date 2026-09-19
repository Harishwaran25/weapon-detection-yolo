#!/usr/bin/env python3
"""Offline confidence / imgsz sweep on dashboard samples."""
import sys
from pathlib import Path

import cv2
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "yolov5"))

WEIGHTS = ROOT / "models" / "best.pt"
SAMPLES = sorted((ROOT / "data" / "samples").glob("sample_*.jpg"))


def expected(name: str) -> str:
    return name.replace("sample_", "").rsplit("_", 1)[0]


def main():
    device = "0" if torch.cuda.is_available() else "cpu"
    model = torch.hub.load(
        str(ROOT / "yolov5"),
        "custom",
        path=str(WEIGHTS),
        source="local",
        device=device,
    )
    model.eval()
    print(f"weights={WEIGHTS} device={device} samples={len(SAMPLES)}")

    best = None
    print(f"{'conf':>5} {'size':>4}  ok miss wrong")
    for conf in [0.15, 0.20, 0.25, 0.30, 0.35, 0.40]:
        for size in [512, 640]:
            model.conf = conf
            model.iou = 0.45
            model.max_det = 50
            ok = miss = wrong = 0
            fails = []
            for s in SAMPLES:
                want = expected(s.name)
                img = cv2.imread(str(s))[:, :, ::-1]
                df = model(img, size=size).pandas().xyxy[0]
                if df.empty:
                    miss += 1
                    fails.append(f"{s.name}:NONE")
                    continue
                df = df.sort_values("confidence", ascending=False)
                got = str(df.iloc[0]["name"]).lower()
                c = float(df.iloc[0]["confidence"])
                if got == want:
                    ok += 1
                else:
                    wrong += 1
                    fails.append(f"{s.name}:{want}->{got}@{c:.2f}")
            print(f"{conf:5.2f} {size:4d}  {ok:2d}  {miss:2d}   {wrong:2d}  {'; '.join(fails) if fails else ''}")
            score = (ok, -wrong, -miss, size, -conf)
            if best is None or score > best[0]:
                best = (score, conf, size, ok, miss, wrong)

    print(f"\nBEST conf={best[1]} size={best[2]} correct={best[3]}/{len(SAMPLES)}")

    conf, size = best[1], best[2]
    print(f"\n=== detail conf={conf} size={size} ===")
    model.conf = conf
    model.iou = 0.45
    for s in SAMPLES:
        want = expected(s.name)
        img = cv2.imread(str(s))[:, :, ::-1]
        df = model(img, size=size).pandas().xyxy[0]
        if df.empty:
            print(f" FAIL {s.name:32} want={want} -> NONE")
            continue
        df = df.sort_values("confidence", ascending=False)
        tops = ", ".join(
            f"{r['name']}@{float(r['confidence']):.2f}" for _, r in df.head(3).iterrows()
        )
        got = str(df.iloc[0]["name"]).lower()
        print(f" {'OK' if got == want else 'FAIL':4} {s.name:32} want={want:13} -> {tops}")


if __name__ == "__main__":
    main()
