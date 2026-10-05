"""Build 16:9 pptx deck; all numbers/figures from results/ files."""
from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

from sim.util import ROOT

FIG = ROOT / "results" / "figures"


def _load(p):
    path = Path(p)
    if path.exists():
        return json.loads(path.read_text())
    return None


def add_title(slide, text, top=0.3, size=32):
    box = slide.shapes.add_textbox(Inches(0.5), Inches(top), Inches(12), Inches(1))
    tf = box.text_frame
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = True
    p.font.color.rgb = RGBColor(20, 40, 60)


def add_body(slide, lines, top=1.3, size=18):
    box = slide.shapes.add_textbox(Inches(0.5), Inches(top), Inches(12), Inches(5))
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.size = Pt(size)
        p.font.color.rgb = RGBColor(30, 30, 30)
        p.space_after = Pt(8)


def add_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def add_fig(slide, name, left=0.5, top=1.5, width=12):
    path = FIG / name
    if path.exists():
        slide.shapes.add_picture(str(path), Inches(left), Inches(top), width=Inches(width))


def main():
    summary = _load(ROOT / "results" / "summary.json") or {}
    headlines = _load(ROOT / "results" / "headlines.json") or []
    robust = _load(ROOT / "results" / "robustness.json")
    xcheck = _load(ROOT / "results" / "emission_xcheck.json")
    grid = _load(ROOT / "results" / "grid_results.json")
    extrap = _load(ROOT / "results" / "extrapolation.json")
    safety = _load(ROOT / "results" / "safety.json")
    perc = _load(ROOT / "results" / "perception_smoke.json")
    tuned = _load(ROOT / "results" / "tuned_params.json")

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # 1 Problem
    s = prs.slides.add_slide(blank)
    add_title(s, "Congestion is energy waste")
    add_body(s, [
        "Idling and stop–go at signals burn fuel and emit CO₂.",
        "Indian mixed traffic (2W / auto / car / bus / truck) amplifies inefficiency.",
        "Question: can energy-aware signal control cut fuel, CO₂, delay, and queues?",
    ])
    add_notes(s, "Open with energy framing for IndianOil — not just mobility.")

    # 2 Why fixed fails
    s = prs.slides.add_slide(blank)
    add_title(s, "Why fixed signals fail")
    add_body(s, [
        "Fixed greens ignore demand imbalance and time-varying peaks.",
        "Webster helps averages but lags dynamic shifts.",
        "Need adaptive control under hard safety timing constraints.",
    ])
    add_notes(s, "Contrast static timing with adaptive pressure control.")

    # 3 Pipeline
    s = prs.slides.add_slide(blank)
    add_title(s, "Pipeline: Vision → Decision → Energy impact")
    add_body(s, [
        "1) Perceive approach queues (detectors or YOLO+ROI).",
        "2) Decide phase with fuel-weighted pressure + min/max green.",
        "3) Measure fuel/CO₂/delay in SUMO with locked evaluation protocol.",
    ])
    add_notes(s, "Emphasize reproducibility: TRAIN/VAL/TEST seeds + config.lock.")

    # 4 Perception
    s = prs.slides.add_slide(blank)
    add_title(s, "AI perception (YOLO)")
    if perc:
        add_body(s, [
            f"Noise model source: {perc.get('noise_model', {}).get('source', 'n/a')}",
            f"Assumed miss rate: {perc.get('noise_model', {}).get('detect_miss_rate', 'n/a')}",
            "Without user video: assumed noise (flagged). With labels: empirical noise_model.json.",
        ])
    else:
        add_body(s, ["Perception artifacts not yet generated."])
    add_notes(s, "SUMO uses noise model; YOLO shows state is extractable from video.")

    # 5 Controller
    s = prs.slides.add_slide(blank)
    add_title(s, "Controller: fuel-weighted pressure")
    add_body(s, [
        "Weight vehicles by measured idle-fuel rate relative to a car.",
        f"Tuned params (VALIDATION only): {json.dumps(tuned) if tuned else 'pending'}",
        "Constraints: MIN_GREEN 15, MAX_GREEN 90, yellow 3, all-red 2, starvation 120.",
    ], size=16)
    add_notes(s, "Explain hysteresis + gap-out; weights.json is measured not guessed.")

    # 6 Experiment design
    s = prs.slides.add_slide(blank)
    add_title(s, "Experiment design")
    add_body(s, [
        "Controllers: fixed, webster, actuated, maxpressure, ours_count, ours_fuel, rl_ppo",
        "Scenarios: balanced, peak_unbalanced, dynamic, low_demand",
        "Seeds: TRAIN 1000–1049, VAL 2000–2019, TEST 1–30 after config.lock",
    ], size=16)
    add_notes(s, "Same seed ⇒ identical demand for every controller.")

    # 7 Results table
    s = prs.slides.add_slide(blank)
    add_title(s, "Results overview")
    add_fig(s, "i_grouped_bars.png", top=1.2, width=12)

    # 8 Headlines
    s = prs.slides.add_slide(blank)
    add_title(s, "Headline fuel reductions (95% CI)")
    lines = []
    for h in headlines:
        lines.append(
            f"{h['scenario']}: {h['pct_fuel_reduction_vs_fixed']:.1f}% "
            f"[{h['ci_lo']:.1f}, {h['ci_hi']:.1f}] ({h['sanity_flag']})"
        )
    if not lines:
        lines = ["Run analyze.py to populate headlines from raw_runs.csv"]
    add_body(s, lines)
    add_fig(s, "ii_pct_reduction.png", top=3.5, width=10)
    add_notes(s, "All numbers read from results/headlines.json — never typed by hand.")

    # 9 Where it helps / not
    s = prs.slides.add_slide(blank)
    add_title(s, "Where it helps — and where it does not")
    losses = []
    for c in summary.get("comparisons", []):
        if c.get("pct_reduction_mean", 1) <= 0:
            losses.append(f"vs {c['baseline']} on {c['scenario']}: {c['pct_reduction_mean']:.1f}%")
    body = losses or ["Check REPORT.md for ties/losses; low_demand often shrinks gains."]
    if safety:
        body.append(f"Safety SSM verdict: {safety.get('verdict')}")
    if xcheck:
        body.append(f"Emission cross-check: {xcheck.get('verdict')}")
    add_body(s, body, size=16)
    add_notes(s, "Be honest about negative/null results.")

    # 10 Robustness
    s = prs.slides.add_slide(blank)
    add_title(s, "Robustness to detection errors")
    add_fig(s, "vii_robustness.png", top=1.3, width=11)
    add_notes(s, "Show graceful degradation as miss rate rises.")

    # 11 Scaling
    s = prs.slides.add_slide(blank)
    add_title(s, "Network scaling & India relevance")
    lines = []
    if grid:
        lines.append(f"Coordination helps: {grid.get('coordination_reduces_fuel')}")
    if extrap:
        al = extrap["annual_litres"]
        lines.append(
            f"Annual litres (sim-based): median {al['median']:.0f} "
            f"(90% interval [{al['p05']:.0f}, {al['p95']:.0f}])"
        )
        lines.append("Fuel price is a PLACEHOLDER — edit config.yaml.")
        lines.append("Label: Simulation-based estimate")
    add_body(s, lines or ["Run grid_sweep + extrapolate"], size=16)
    add_fig(s, "xi_extrapolation.png", top=4.0, width=8)

    # 12 Closing
    s = prs.slides.add_slide(blank)
    add_title(s, "Closing", top=2.5, size=28)
    add_body(s, [
        "Smarter traffic shouldn't just mean faster traffic.",
        "It should mean more energy-efficient traffic.",
    ], top=3.5, size=24)
    add_notes(s, "Close on IndianOil energy mission alignment.")

    out = ROOT / "results" / "deck.pptx"
    prs.save(str(out))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
