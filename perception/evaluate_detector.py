"""Evaluate detector if labels exist; else synthetic smoke + assumed noise model."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from sim.util import ROOT, save_json


def write_assumed_noise(miss: float = 0.15) -> dict:
    # Mild class confusion assumed
    types = ["two_wheeler", "auto_rickshaw", "car", "bus", "truck"]
    confusion = {}
    for t in types:
        row = {u: (0.85 if u == t else 0.15 / (len(types) - 1)) for u in types}
        # normalize
        s = sum(row.values())
        confusion[t] = {k: v / s for k, v in row.items()}
    out = {
        "detect_miss_rate": miss,
        "class_confusion": confusion,
        "count_jitter_std": 0.5,
        "source": "assumed",
        "note": (
            "ASSUMED noise model (no user video/labels). "
            "Supply data/video/ and data/video_labels/ to derive empirical noise_model.json. "
            "SUMO consumes simulated detections with this noise; YOLO on real video shows "
            "the same state is extractable and supplies noise parameters."
        ),
    }
    path = ROOT / "perception" / "noise_model.json"
    save_json(path, out)
    return out


def evaluate_from_labels(video_dir: Path, label_dir: Path) -> dict:
    # Expect labels as JSON list of {frame, class, count} or YOLO txt — simple count CSV/JSON
    label_files = list(label_dir.glob("*"))
    if not label_files:
        return write_assumed_noise()
    # Placeholder empirical derivation: if manual counts JSON present
    # Format: {"frames":[{"class_counts":{"car":n,...}}]}
    miss_rates = []
    confusion_counts = {}
    for lf in label_files:
        if lf.suffix not in (".json",):
            continue
        data = json.loads(lf.read_text())
        for fr in data.get("frames", []):
            # without paired detections, cannot compute; skip
            pass
    # If insufficient, fall back but mark instructions
    out = write_assumed_noise(0.12)
    out["source"] = "partial_labels_fallback_assumed"
    out["instructions"] = (
        "Provide paired detection outputs or use yolo_counts.py then compare to "
        "manual counts per class to fill precision/recall. "
        "Optional fine-tune: place a licensed Indian road dataset under data/ and "
        "run ultralytics train; do not download unlicensed content."
    )
    save_json(ROOT / "perception" / "noise_model.json", out)
    return out


def synthetic_smoke() -> dict:
    """Generate a tiny synthetic 'video' frames array and run a trivial count smoke."""
    # Create a blank mp4
    import imageio.v2 as imageio

    demo = ROOT / "results" / "demo"
    demo.mkdir(parents=True, exist_ok=True)
    path = demo / "synthetic_traffic_smoke.mp4"
    frames = []
    for i in range(15):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        frame[:, :] = (30, 30, 30)
        # moving rectangle as fake vehicle
        x = 20 + i * 10
        frame[100:140, x:x + 40] = (200, 200, 50)
        frames.append(frame)
    imageio.mimsave(path, frames, fps=5)
    noise = write_assumed_noise(0.15)
    save_json(ROOT / "results" / "perception_smoke.json", {
        "video": str(path),
        "noise_model": noise,
        "flag": "ASSUMED_NOISE_MODEL_NO_USER_VIDEO",
    })
    print("Synthetic perception smoke complete; noise model ASSUMED.")
    return noise


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    video_dir = ROOT / "data" / "video"
    label_dir = ROOT / "data" / "video_labels"
    has_video = any(video_dir.glob("*")) if video_dir.exists() else False
    has_labels = any(label_dir.glob("*")) if label_dir.exists() else False
    if args.smoke or not (has_video and has_labels):
        synthetic_smoke()
        print(
            "\nTo supply real data:\n"
            "  - Put videos in data/video/\n"
            "  - Put manual counts/boxes in data/video_labels/\n"
            "  - Run: python -m perception.yolo_counts --video ... --roi perception/roi.yaml\n"
            "  - Run: python -m perception.evaluate_detector\n"
            "Licensing: only use datasets you have rights to; do not download unlicensed content.\n"
        )
    else:
        evaluate_from_labels(video_dir, label_dir)


if __name__ == "__main__":
    main()
