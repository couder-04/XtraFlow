"""Build one simple story video: 2×2 cams + which roads get green when.

Reads overlay clips + clubbed decisions from yolo_demo_summary.json.
Writes results/demo/yolo/yolo_story.mp4 (and a copy under results/demo/).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from demo.yolo_decisions import PHASE_APPROACHES, enrich_summary
from sim.util import ROOT

TILE_W, TILE_H = 640, 360
BANNER_H = 72
FOOTER_H = 48
ORDER = ("N", "E", "S", "W")  # TL, TR, BL, BR
PHASE_PLAIN = {
    "NS_TL": "North–South moving",
    "NS_R": "North–South (right) moving",
    "EW_TL": "East–West moving",
    "EW_R": "East–West (right) moving",
}


def _open(path: Path):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise SystemExit(f"Cannot open {path}")
    return cap


def _read_scaled(cap, w=TILE_W, h=TILE_H):
    ok, frame = cap.read()
    if not ok:
        return None
    return cv2.resize(frame, (w, h), interpolation=cv2.INTER_AREA)


def _phase_at(decisions: list[dict], t_s: float) -> dict:
    if not decisions:
        return {"next_phase": "NS_TL", "t_s": t_s}
    # decisions keyed roughly every 1s (counts @ 3 fps, frame/3)
    best = decisions[0]
    for row in decisions:
        if float(row.get("t_s", 0)) <= t_s + 1e-6:
            best = row
        else:
            break
    return best


def _dim(frame: np.ndarray, amount: float = 0.45) -> np.ndarray:
    return cv2.convertScaleAbs(frame, alpha=amount, beta=0)


def _glow(frame: np.ndarray, color=(40, 220, 90), thickness: int = 10) -> np.ndarray:
    out = frame.copy()
    h, w = out.shape[:2]
    cv2.rectangle(out, (0, 0), (w - 1, h - 1), color, thickness)
    # corner badges
    cv2.rectangle(out, (0, 0), (110, 36), color, -1)
    return out


def _put(img, text, org, scale=0.7, color=(255, 255, 255), thick=2):
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thick + 2, cv2.LINE_AA)
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thick, cv2.LINE_AA)


def build_story(
    overlay_paths: dict[str, Path],
    decisions: list[dict],
    out_path: Path,
    fps: float = 10.0,
) -> Path:
    caps = {a: _open(overlay_paths[a]) for a in ORDER if a in overlay_paths}
    if len(caps) < 2:
        raise SystemExit("Need at least two overlay videos")

    out_w = TILE_W * 2
    out_h = BANNER_H + TILE_H * 2 + FOOTER_H
    out_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(out_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (out_w, out_h),
    )

    frame_i = 0
    while True:
        tiles = {}
        done = False
        for a, cap in caps.items():
            fr = _read_scaled(cap)
            if fr is None:
                done = True
                break
            tiles[a] = fr
        if done or len(tiles) < len(caps):
            break

        t_s = frame_i / fps
        dec = _phase_at(decisions, t_s)
        phase = dec.get("next_phase") or "NS_TL"
        active = set(PHASE_APPROACHES.get(phase, ()))
        plain = PHASE_PLAIN.get(phase, phase)

        canvas = np.zeros((out_h, out_w, 3), dtype=np.uint8)
        # banner
        canvas[:BANNER_H, :] = (28, 28, 28)
        _put(canvas, f"t = {t_s:4.1f}s", (16, 46), 0.85, (220, 220, 220), 2)
        _put(canvas, plain, (200, 46), 0.95, (80, 255, 140), 2)
        _put(canvas, "XtraFlow serves highest fuel-weighted demand", (out_w - 520, 46), 0.45, (180, 180, 180), 1)

        positions = {
            "N": (0, BANNER_H),
            "E": (TILE_W, BANNER_H),
            "S": (0, BANNER_H + TILE_H),
            "W": (TILE_W, BANNER_H + TILE_H),
        }
        for a, (x, y) in positions.items():
            if a not in tiles:
                continue
            tile = tiles[a]
            label = a
            if a in active:
                tile = _glow(tile)
                badge = "GO"
                badge_color = (40, 220, 90)
            else:
                tile = _dim(tile, 0.4)
                badge = "WAIT"
                badge_color = (80, 80, 200)
            canvas[y : y + TILE_H, x : x + TILE_W] = tile
            cv2.rectangle(canvas, (x + 8, y + 8), (x + 100, y + 40), badge_color, -1)
            _put(canvas, f"{label} {badge}", (x + 14, y + 32), 0.65, (255, 255, 255), 2)

        # footer timeline
        canvas[out_h - FOOTER_H :, :] = (22, 22, 22)
        _put(canvas, "Timeline  N/S green = north–south roads move   ·   E/W green = east–west roads move", (16, out_h - 18), 0.5, (200, 200, 200), 1)
        # scrubber
        if decisions:
            t_max = max(float(r.get("t_s") or 0) for r in decisions) or 1.0
            progress = min(1.0, t_s / t_max)
            bar_y = out_h - FOOTER_H + 12
            cv2.rectangle(canvas, (16, bar_y), (out_w - 16, bar_y + 8), (60, 60, 60), -1)
            cv2.rectangle(canvas, (16, bar_y), (16 + int((out_w - 32) * progress), bar_y + 8), (80, 220, 140), -1)
            # mark phase changes
            prev = None
            for r in decisions:
                ph = r.get("next_phase")
                if ph != prev:
                    px = 16 + int((out_w - 32) * (float(r.get("t_s") or 0) / t_max))
                    col = (80, 255, 140) if ph.startswith("NS") else (80, 200, 255)
                    cv2.line(canvas, (px, bar_y - 4), (px, bar_y + 12), col, 2)
                    prev = ph

        writer.write(canvas)
        frame_i += 1

    for cap in caps.values():
        cap.release()
    writer.release()
    return out_path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--summary",
        default=str(ROOT / "results" / "demo" / "yolo" / "yolo_demo_summary.json"),
    )
    p.add_argument(
        "--out",
        default=str(ROOT / "results" / "demo" / "yolo" / "yolo_story.mp4"),
    )
    args = p.parse_args()
    summary_path = Path(args.summary)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if not (summary.get("clubbed") or {}).get("decisions"):
        summary = enrich_summary(summary)
        summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    overlays = {}
    for cam in summary.get("cameras") or []:
        a = cam["approach"]
        rel = (summary.get("per_camera") or {}).get(a, {}).get("overlay")
        path = ROOT / rel if rel else ROOT / f"results/demo/yolo/overlay_{a}.mp4"
        if path.exists():
            overlays[a] = path
    if len(overlays) < 2:
        raise SystemExit("Missing overlay videos — run make yolo_demo first")

    decisions = (summary.get("clubbed") or {}).get("decisions") or []
    out = build_story(overlays, decisions, Path(args.out))
    copy = ROOT / "results" / "demo" / "yolo_story.mp4"
    copy.write_bytes(out.read_bytes())
    summary.setdefault("outputs", {})["story"] = str(out.relative_to(ROOT))
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(out)
    print(copy)


if __name__ == "__main__":
    main()
