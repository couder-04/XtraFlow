"""Streamlit YOLO demo dashboard — clubbed mosaic + per-camera videos & stats."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "results" / "demo" / "yolo" / "yolo_demo_summary.json"
YOLO_DIR = ROOT / "results" / "demo" / "yolo"


def load_summary() -> dict | None:
    if not SUMMARY.exists():
        return None
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


def resolve(rel: str | None) -> Path | None:
    if not rel:
        return None
    p = ROOT / rel
    return p if p.exists() and p.stat().st_size > 0 else None


def cam_table(summary: dict) -> pd.DataFrame:
    rows = []
    for approach, stats in (summary.get("per_camera") or {}).items():
        rows.append(
            {
                "approach": approach,
                "title": stats.get("title", ""),
                "peak_vehicles": stats.get("peak_vehicles"),
                "mean_vehicles": stats.get("mean_vehicles"),
                "mean_pressure": stats.get("mean_weighted_pressure"),
                "samples": stats.get("n_samples"),
                "source": stats.get("source_video"),
            }
        )
    if not rows:
        # Fallback from cameras list only
        for cam in summary.get("cameras") or []:
            rows.append(
                {
                    "approach": cam["approach"],
                    "title": cam.get("title", ""),
                    "peak_vehicles": None,
                    "mean_vehicles": None,
                    "mean_pressure": None,
                    "samples": None,
                    "source": cam.get("file"),
                }
            )
    return pd.DataFrame(rows)


def series_df(stats: dict) -> pd.DataFrame:
    series = stats.get("totals_series") or []
    if not series:
        return pd.DataFrame()
    return pd.DataFrame(series).set_index("frame")


def show_video(path: Path | None, caption: str) -> None:
    if path is None:
        st.warning(f"Missing video: {caption}")
        return
    st.caption(caption)
    st.video(str(path))


st.set_page_config(page_title="XtraFlow YOLO demo", layout="wide")
st.title("XtraFlow · YOLO input feasibility")
st.caption("Detector counts from CCTV — not a fuel-saving result")

summary = load_summary()
if summary is None:
    st.error("No YOLO summary found. Run `make yolo_demo` first.")
    st.stop()

st.info(summary.get("label", "Input feasibility — not a fuel-saving result"))
with st.expander("Source & attribution", expanded=False):
    st.write(summary.get("source", ""))
    st.write(summary.get("attribution", ""))
    st.write(summary.get("note", ""))

view = st.sidebar.radio(
    "View",
    ["Clubbed (all cameras)", "Individual camera"],
    index=0,
)
approaches = [c["approach"] for c in summary.get("cameras") or []]
if not approaches:
    approaches = list((summary.get("per_camera") or {}).keys())

# ── Clubbed ──────────────────────────────────────────────────────────────
if view.startswith("Clubbed"):
    st.subheader("All cameras")
    club = summary.get("clubbed") or {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cameras", club.get("n_cameras", len(approaches)))
    c2.metric("Σ peak vehicles", club.get("peak_vehicles", "—"))
    c3.metric("Σ mean vehicles", club.get("mean_vehicles", "—"))
    c4.metric("Σ mean pressure", club.get("mean_weighted_pressure", "—"))

    mosaic = resolve((summary.get("outputs") or {}).get("mosaic"))
    if mosaic is None:
        mosaic = resolve("results/demo/yolo/yolo_mosaic.mp4")
    show_video(mosaic, "2×2 mosaic (N · E / S · W)")

    st.subheader("Per-camera summary")
    df = cam_table(summary)
    st.dataframe(df, use_container_width=True, hide_index=True)

    if not df.empty and df["mean_vehicles"].notna().any():
        chart = df.set_index("approach")[["mean_vehicles", "peak_vehicles"]]
        st.bar_chart(chart)

    st.subheader("Vehicle time series (all cameras)")
    cols = st.columns(2)
    for i, approach in enumerate(approaches):
        stats = (summary.get("per_camera") or {}).get(approach) or {}
        sdf = series_df(stats)
        with cols[i % 2]:
            st.markdown(f"**{approach}**")
            if sdf.empty:
                st.caption("No series in summary — re-run `make yolo_demo`.")
            else:
                st.line_chart(sdf[["vehicles", "weighted_pressure"]])

    st.subheader("Individual overlays (grid)")
    g = st.columns(2)
    for i, approach in enumerate(approaches):
        stats = (summary.get("per_camera") or {}).get(approach) or {}
        ov = resolve(stats.get("overlay") or f"results/demo/yolo/overlay_{approach}.mp4")
        with g[i % 2]:
            show_video(ov, f"{approach} — {stats.get('title', '')}")

# ── Individual ───────────────────────────────────────────────────────────
else:
    cam = st.sidebar.selectbox("Camera", approaches, index=0)
    stats = (summary.get("per_camera") or {}).get(cam) or {}
    title = stats.get("title") or cam
    st.subheader(f"Camera {cam}")
    st.write(title)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Peak vehicles", stats.get("peak_vehicles", "—"))
    m2.metric("Mean vehicles", stats.get("mean_vehicles", "—"))
    m3.metric("Mean pressure", stats.get("mean_weighted_pressure", "—"))
    m4.metric("Samples", stats.get("n_samples", "—"))

    ov = resolve(stats.get("overlay") or f"results/demo/yolo/overlay_{cam}.mp4")
    show_video(ov, f"YOLO overlay · {cam}")

    sdf = series_df(stats)
    if not sdf.empty:
        st.subheader("Counts over time")
        st.line_chart(sdf[["vehicles", "weighted_pressure"]])
        class_cols = [c for c in ("car", "truck", "bus", "two_wheeler", "auto_rickshaw") if c in sdf.columns]
        if class_cols:
            st.subheader("Class mix over time")
            st.area_chart(sdf[class_cols])
            st.subheader("Last sample")
            last = sdf.iloc[-1]
            st.dataframe(
                pd.DataFrame(
                    {
                        "class": class_cols + ["vehicles", "weighted_pressure"],
                        "count": [last[c] for c in class_cols]
                        + [last["vehicles"], last["weighted_pressure"]],
                    }
                ),
                hide_index=True,
                use_container_width=True,
            )
    else:
        # Load raw counts file if summary is from an older run
        counts_path = resolve(stats.get("counts") or f"results/demo/yolo/counts_{cam}.json")
        if counts_path:
            blob = json.loads(counts_path.read_text(encoding="utf-8"))
            rows = []
            for step in blob.get("series") or []:
                veh = 0
                press = 0.0
                for vals in (step.get("counts") or {}).values():
                    veh += sum(
                        int(vals.get(k) or 0)
                        for k in ("car", "two_wheeler", "bus", "truck", "auto_rickshaw")
                    )
                    press += float(vals.get("weighted_pressure") or 0)
                rows.append({"frame": step.get("frame"), "vehicles": veh, "weighted_pressure": press})
            if rows:
                st.line_chart(pd.DataFrame(rows).set_index("frame"))
        else:
            st.warning("No counts series available.")

    st.caption(f"Source clip: `{stats.get('source_video', '—')}`")

st.sidebar.divider()
st.sidebar.caption("Re-run pipeline: `make yolo_demo`")
st.sidebar.caption(str(SUMMARY.relative_to(ROOT)))
