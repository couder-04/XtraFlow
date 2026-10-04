"""YOLOv8 per-approach ROI counts → counts.json schema for controller noise/perception."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from sim.util import ROOT, save_json

CLASS_MAP = {
    2: "car",       # COCO car
    3: "two_wheeler",  # motorcycle
    5: "bus",
    7: "truck",
}


def point_in_poly(x, y, poly):
    # ray casting
    n = len(poly)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--video", required=True)
    p.add_argument("--roi", default=str(ROOT / "perception" / "roi.yaml"))
    p.add_argument("--out", default=str(ROOT / "results" / "perception_counts.json"))
    p.add_argument("--model", default="yolov8n.pt")
    p.add_argument("--fps", type=float, default=3.0)
    args = p.parse_args()

    import cv2
    from ultralytics import YOLO

    roi = yaml.safe_load(Path(args.roi).read_text())
    model = YOLO(args.model)
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise SystemExit(f"Cannot open video {args.video}")
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 25
    stride = max(1, int(round(src_fps / args.fps)))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out_mp4 = Path(args.out).with_suffix(".mp4")
    writer = cv2.VideoWriter(str(out_mp4), cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (w, h))

    # ByteTrack via ultralytics tracker
    frame_i = 0
    counts_series = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_i % stride != 0:
            frame_i += 1
            continue
        results = model.track(frame, persist=True, tracker="bytetrack.yaml", verbose=False)
        per_ap = {a: {"car": 0, "two_wheeler": 0, "bus": 0, "truck": 0, "halting_est": 0} for a in roi["approaches"]}
        r0 = results[0]
        if r0.boxes is not None:
            for box in r0.boxes:
                cls = int(box.cls.item())
                if cls not in CLASS_MAP:
                    continue
                vtype = CLASS_MAP[cls]
                xyxy = box.xyxy[0].tolist()
                cx = ((xyxy[0] + xyxy[2]) / 2) / w
                cy = ((xyxy[1] + xyxy[3]) / 2) / h
                for ap, spec in roi["approaches"].items():
                    if point_in_poly(cx, cy, spec["polygon"]):
                        per_ap[ap][vtype] += 1
                        # crude halting: low vertical box motion unavailable; mark unknown 0
        counts_series.append({"frame": frame_i, "counts": per_ap})
        annotated = r0.plot()
        writer.write(annotated)
        frame_i += 1

    cap.release()
    writer.release()
    out = {
        "schema": "controller_counts_v1",
        "video": args.video,
        "fps": args.fps,
        "series": counts_series,
        "annotated_mp4": str(out_mp4),
    }
    save_json(Path(args.out), out)
    print(f"Wrote {args.out} and {out_mp4}")


if __name__ == "__main__":
    main()
