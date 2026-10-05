"""Build a 16:9 deck. Every reported number is loaded from results/ or config."""
from __future__ import annotations

import csv
import statistics
import subprocess
from collections import defaultdict
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

from sim.util import ROOT, load_config

TITLE = "Georgia"
BODY = "Calibri"

NAVY = RGBColor(0x0E, 0x1C, 0x2B)
NAVY_2 = RGBColor(0x17, 0x2A, 0x3C)
INK = RGBColor(0x1A, 0x28, 0x34)
MUTED = RGBColor(0x5E, 0x6E, 0x7C)
CREAM = RGBColor(0xF6, 0xF3, 0xEE)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
AMBER = RGBColor(0xC4, 0x84, 0x1D)
TEAL = RGBColor(0x1B, 0x6B, 0x5A)
CORAL = RGBColor(0xB8, 0x4E, 0x2A)
LINE = RGBColor(0xE3, 0xDB, 0xD0)
SOFT = RGBColor(0xFB, 0xF8, 0xF3)
SOFT_TEAL = RGBColor(0xE5, 0xF2, 0xEE)
SOFT_AMBER = RGBColor(0xFB, 0xF3, 0xE2)
SOFT_CORAL = RGBColor(0xFB, 0xEE, 0xE8)
MIST = RGBColor(0xC9, 0xD4, 0xDC)

L = 0.55
CONTENT_W = 12.28
PAGE_W = 13.333
PAGE_H = 7.5

SCENARIO = {
    "peak_unbalanced": "Peak, one-sided",
    "dynamic": "Shifting",
    "low_demand": "Low demand",
    "balanced": "Balanced",
}
VEHICLE = {
    "two_wheeler": "Two-wheeler",
    "auto_rickshaw": "Auto",
    "car": "Car",
    "bus": "Bus",
    "truck": "Truck",
}
MIX_NAME = {
    "two_wheeler": "two-wheelers",
    "car": "cars",
    "truck": "trucks",
    "auto_rickshaw": "autos",
    "bus": "buses",
}
CTRL = {
    "fixed": "Fixed time",
    "webster": "Webster",
    "actuated": "Actuated",
    "maxpressure": "Max-pressure",
    "ours_count": "Count only",
    "XtraFlow": "XtraFlow",
    "rl_ppo": "PPO",
}


def _load(path: Path):
    if not path.exists():
        return None
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def _repo_url() -> str:
    try:
        raw = subprocess.check_output(
            ["git", "remote", "get-url", "origin"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""
    if raw.endswith(".git"):
        raw = raw[:-4]
    return raw.removeprefix("https://").removeprefix("http://")


def _means(path: Path) -> dict:
    if not path.exists():
        return {}
    out = {}
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            parsed = {}
            for key, value in row.items():
                if key in ("scenario", "controller"):
                    continue
                parsed[key] = float(value)
            out[(row["scenario"], row["controller"])] = parsed
    return out


def _robust(blob: dict | None) -> list[dict]:
    if not blob:
        return []
    groups: dict[tuple, list] = defaultdict(list)
    for row in blob.get("rows", []):
        groups[(row["controller"], row.get("kind"), float(row.get("miss") or 0))].append(
            float(row["fuel_per_vehicle_L"])
        )
    rows = []
    for (controller, kind, miss), vals in groups.items():
        rows.append(
            {
                "controller": controller,
                "kind": kind,
                "miss": miss,
                "n": len(vals),
                "mean": statistics.fmean(vals),
                "std": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
            }
        )
    return rows


def load() -> dict:
    cfg = load_config()
    summary = _load(ROOT / "results" / "summary.json") or {}
    weights = _load(ROOT / "results" / "weights.json") or {}
    tuned = _load(ROOT / "results" / "tuned_params.json") or {}
    safety = _load(ROOT / "results" / "safety.json") or {}
    xcheck = _load(ROOT / "results" / "emission_xcheck.json") or {}
    grid = _load(ROOT / "results" / "grid_results.json") or {}
    extra = _load(ROOT / "results" / "extrapolation.json") or {}
    perc = _load(ROOT / "results" / "perception_smoke.json") or {}
    sublane = _load(ROOT / "results" / "sublane_fallback.json") or {}
    headlines = list(summary.get("headlines") or _load(ROOT / "results" / "headlines.json") or [])
    headlines.sort(key=lambda row: -float(row["pct_fuel_reduction_vs_fixed"]))
    comps = {}
    for row in summary.get("comparisons", []):
        if row.get("metric") == "fuel_per_vehicle_L":
            comps[(row["scenario"], row["baseline"])] = row
    return {
        "cfg": cfg,
        "summary": summary,
        "weights": weights,
        "tuned": tuned,
        "safety": safety,
        "xcheck": xcheck,
        "grid": grid,
        "extra": extra,
        "perc": perc,
        "sublane": sublane,
        "headlines": headlines,
        "comps": comps,
        "means": _means(ROOT / "results" / "tables" / "summary_mean_std.csv"),
        "robust": _robust(_load(ROOT / "results" / "robustness.json")),
        "url": _repo_url(),
        "label": summary.get("label")
        or extra.get("label")
        or "Simulation-based estimate; not a real-world deployment result",
    }


def _style(run, font, size, color, bold=False):
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = False
    run.font.color.rgb = color
    rpr = run._r.get_or_add_rPr()
    for tag in ("latin", "ea", "cs"):
        node = rpr.find(qn(f"a:{tag}"))
        if node is None:
            node = rpr.makeelement(qn(f"a:{tag}"))
            rpr.append(node)
        node.set("typeface", font)


def write(slide, l, t, w, h, paragraphs, align=PP_ALIGN.LEFT, anchor="t"):
    box = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    anchor_map = {"t": MSO_ANCHOR.TOP, "ctr": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}
    tf.paragraphs[0].alignment = align
    try:
        tf._txBody.bodyPr.set("anchor", {"t": "t", "ctr": "ctr", "b": "b"}[anchor])
    except Exception:
        _ = anchor_map
    for i, runs in enumerate(paragraphs):
        paragraph = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        paragraph.alignment = align
        paragraph.space_before = Pt(0)
        paragraph.space_after = Pt(0)
        for text, size, color, bold, font in runs:
            run = paragraph.add_run()
            run.text = text
            _style(run, font or BODY, size, color, bold)
    return box


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def rect(slide, l, t, w, h, fill, line=None, radius=None):
    kind = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(kind, Inches(l), Inches(t), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line is None:
        shape.line.fill.background()
    else:
        shape.line.color.rgb = line
        shape.line.width = Pt(1)
    if radius:
        try:
            shape.adjustments[0] = radius
        except Exception:
            pass
    return shape


def blank(prs, dark=False):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg(slide, NAVY if dark else CREAM)
    rect(slide, 0, 0, 0.08, PAGE_H, AMBER)
    return slide


def footer(slide, page, dark=False):
    color = MIST if dark else MUTED
    write(
        slide,
        L,
        7.12,
        9.2,
        0.26,
        [[("XtraFlow    ·    Simulation-based estimate", 12, color, False, BODY)]],
    )
    write(
        slide,
        10.6,
        7.12,
        2.2,
        0.26,
        [[(f"{page:02d}", 12, color, False, TITLE)]],
        align=PP_ALIGN.RIGHT,
    )


def chrome(slide, kicker, title, dek, page):
    write(slide, L, 0.28, 10, 0.26, [[(kicker.upper(), 12, AMBER, True, BODY)]])
    write(slide, L, 0.52, CONTENT_W, 0.52, [[(title, 28, INK, True, TITLE)]])
    if dek:
        write(slide, L, 1.08, CONTENT_W, 0.46, [[(dek, 15, MUTED, False, BODY)]])
    footer(slide, page)


def _card(slide, l, t, w, h, fill=WHITE):
    return rect(slide, l, t, w, h, fill, line=LINE, radius=0.08)


def _fmt_pct(value, digits=1) -> str:
    return f"{value:.{digits}f}%"


def _scenario(name: str) -> str:
    return SCENARIO.get(name, name.replace("_", " "))


def _focus(data) -> str:
    tuned = data["tuned"].get("scenario")
    if tuned:
        return tuned
    if data["headlines"]:
        return data["headlines"][0]["scenario"]
    return "peak_unbalanced"


def _mean(data, scenario, controller, key):
    row = data["means"].get((scenario, controller))
    if not row:
        return None
    return row.get(key)


def _comp(data, scenario, baseline):
    return data["comps"].get((scenario, baseline))


def slide_title(prs, data, page, _total):
    slide = blank(prs, dark=True)
    write(slide, 0.78, 1.42, 10, 0.28, [[("SIMULATION STUDY", 13, AMBER, True, BODY)]])
    write(slide, 0.75, 1.78, 11, 0.95, [[("XtraFlow", 54, WHITE, True, TITLE)]])
    rect(slide, 0.8, 2.82, 2.15, 0.035, AMBER)
    write(
        slide,
        0.78,
        3.05,
        10,
        0.5,
        [[("Fuel-weighted traffic signals", 26, RGBColor(0xF0, 0xC2, 0x6A), False, TITLE)]],
    )
    write(
        slide,
        0.78,
        3.7,
        9.2,
        0.85,
        [[(
            "A locked comparison on mixed Indian traffic. Same cars, seven controllers, "
            "four demand patterns. Not a field deployment.",
            18,
            MIST,
            False,
            BODY,
        )]],
    )
    cfg = data["cfg"]
    test = cfg.get("seed_protocol", {}).get("test", [1, 30])
    facts = [
        (str(len(data["summary"].get("scenarios") or cfg.get("demand", {}))), "scenarios"),
        (str(int(test[1]) - int(test[0]) + 1), "test seeds, scored once"),
        (str(len(data["summary"].get("controllers") or [])), "controllers"),
    ]
    x = 0.78
    for value, label in facts:
        write(slide, x, 5.15, 3.3, 0.5, [[(value, 28, WHITE, True, TITLE)]])
        write(slide, x, 5.68, 3.3, 0.35, [[(label, 13, MIST, False, BODY)]])
        x += 3.5
    url = data["url"] or "local study"
    write(slide, 0.78, 6.55, 8, 0.3, [[(url, 13, MIST, False, BODY)]])
    write(slide, 0.78, 6.88, 10, 0.28, [[(data["label"], 12, RGBColor(0x8A, 0x9B, 0xA8), False, BODY)]])
    notes(
        slide,
        "Open on energy, not on travel time. Say out loud that this is a simulation before the first percentage. "
        f"Source label: {data['label']}",
    )


def slide_problem(prs, data, page, _total):
    slide = blank(prs)
    weights = (data["weights"].get("w_type") or {})
    truck = weights.get("truck")
    bike = weights.get("two_wheeler")
    truck_bit = f"{truck:.1f}× a car" if truck is not None else "several times a car"
    bike_bit = f"{bike:.2f}×" if bike is not None else "a fraction of"
    chrome(
        slide,
        "The problem",
        "A stopped queue is burning fuel",
        "Fixed green cannot see which approach is waiting, or what that wait costs.",
        page,
    )
    cards = [
        (
            "01",
            "Fixed green is blind",
            "The split stays put when one road is empty and the other is full. Webster helps the average hour. It still lags a peak that moves.",
        ),
        (
            "02",
            "A count is the wrong unit",
            f"Here a truck idles at {truck_bit}, a two-wheeler at {bike_bit}. Treating them as one vehicle spends green on the wrong queue.",
        ),
        (
            "03",
            "The question",
            "If the signal weighs each vehicle by idle fuel, do fuel, CO₂, delay, and queues fall — inside hard green, yellow, and all-red limits?",
        ),
    ]
    gap = 0.18
    width = (CONTENT_W - 2 * gap) / 3
    for i, (num, title, body) in enumerate(cards):
        x = L + i * (width + gap)
        _card(slide, x, 1.72, width, 4.05)
        write(slide, x + 0.26, 1.96, width - 0.5, 0.4, [[(num, 20, AMBER, True, TITLE)]])
        write(slide, x + 0.26, 2.55, width - 0.5, 0.85, [[(title, 20, INK, True, TITLE)]])
        write(slide, x + 0.26, 3.5, width - 0.52, 1.9, [[(body, 15, INK, False, BODY)]])
    mix = data["cfg"].get("vehicle_mix") or {}
    parts = [
        f"{MIX_NAME.get(key, key)} {share * 100:.0f}%"
        for key, share in sorted(mix.items(), key=lambda item: -item[1])
    ]
    mix_line = "Assumed mix   ·   " + "   ·   ".join(parts) if parts else "Vehicle mix not loaded"
    rect(slide, L, 5.95, CONTENT_W, 0.95, SOFT, line=LINE, radius=0.08)
    write(slide, L + 0.28, 6.08, CONTENT_W - 0.5, 0.28, [[("LEFT-HAND TRAFFIC  ·  ONE FOUR-ARM JUNCTION", 12, AMBER, True, BODY)]])
    write(slide, L + 0.28, 6.38, CONTENT_W - 0.5, 0.35, [[(mix_line, 14, INK, False, BODY)]])
    notes(
        slide,
        "The mix is assumed until observed counts are supplied. Do not present it as a city survey. "
        "Idle-fuel ratios are measured in SUMO, not guessed.",
    )


def slide_weights(prs, data, page, _total):
    slide = blank(prs)
    weights = data["weights"]
    wtype = weights.get("w_type") or {}
    tuned = data["tuned"]
    duration = weights.get("duration_s")
    chrome(
        slide,
        "The controller",
        "Weigh the queue by the fuel it burns",
        "Max-pressure, with one change: a vehicle counts in proportion to its idle fuel, relative to a car.",
        page,
    )
    probe = f"{duration:.0f}-second" if duration else "stopped"
    write(
        slide,
        L,
        1.75,
        5.35,
        1.5,
        [[(
            f"Weights come from a {probe} probe of fuel burned while the vehicle is stopped. "
            "Emission classes are assumed. Autos and cars share a class in this run, so they share a weight.",
            16,
            INK,
            False,
            BODY,
        )]],
    )
    if tuned:
        write(
            slide,
            L,
            3.45,
            5.35,
            1.35,
            [[
                ("Chosen on validation only", 13, AMBER, True, BODY),
            ], [
                (
                    f"Look back {tuned.get('detection_distance_m', 0):.0f} m. "
                    f"Count moving vehicles at {tuned.get('alpha_moving', 0):.2f}. "
                    f"Switch only past hysteresis {tuned.get('hysteresis', 0):.2f}. "
                    f"Scenario: {_scenario(tuned.get('scenario', ''))}.",
                    15,
                    INK,
                    False,
                    BODY,
                ),
            ]],
        )
    order = [key for key in ("two_wheeler", "auto_rickshaw", "car", "bus", "truck") if key in wtype]
    max_w = max((wtype[key] for key in order), default=1) or 1
    top = 1.78
    for key in order:
        value = wtype[key]
        write(slide, 6.05, top, 1.55, 0.46, [[(VEHICLE.get(key, key), 14, INK, False, BODY)]], anchor="ctr")
        rect(slide, 7.7, top + 0.14, 3.15, 0.16, LINE)
        rect(slide, 7.7, top + 0.14, 3.15 * (value / max_w), 0.16, TEAL)
        write(
            slide,
            11.15,
            top,
            1.35,
            0.46,
            [[(f"{value:.2f}×", 15, TEAL, True, TITLE)]],
            anchor="ctr",
        )
        top += 0.62
    sig = data["cfg"].get("signals") or {}
    chips = [
        ("Min green", sig.get("min_green_s")),
        ("Max green", sig.get("max_green_s")),
        ("Yellow", sig.get("yellow_s")),
        ("All-red", sig.get("all_red_s")),
        ("Must serve", sig.get("starvation_s")),
    ]
    chips = [(name, value) for name, value in chips if value is not None]
    rect(slide, L, 5.45, CONTENT_W, 1.42, NAVY, radius=0.08)
    write(slide, L + 0.28, 5.58, 8, 0.28, [[("TIMING THAT STAYS IN FORCE", 12, AMBER, True, BODY)]])
    if chips:
        cw = (CONTENT_W - 0.5) / len(chips)
        for i, (name, value) in enumerate(chips):
            x = L + 0.22 + i * cw
            write(slide, x, 5.95, cw - 0.1, 0.4, [[(f"{value:g} s", 20, WHITE, True, TITLE)]])
            write(slide, x, 6.4, cw - 0.1, 0.28, [[(name, 12, MIST, False, BODY)]])
    notes(
        slide,
        "Explain hysteresis: the new phase must beat the current pressure by the tuned margin. "
        "Must-serve forces a switch so a waiting approach is not ignored. Weights file: results/weights.json. "
        "Tuned parameters: results/tuned_params.json, validation seeds only.",
    )


def slide_cycle(prs, data, page, _total):
    slide = blank(prs)
    flag = (data["perc"].get("flag") or "").replace("_", " ").lower()
    chrome(
        slide,
        "How a decision is made",
        "See the queue. Score the fuel. Keep the timing.",
        "The signal never skips yellow or all-red, and it cannot hold green past the cap.",
        page,
    )
    miss = (data["perc"].get("noise_model") or {}).get("detect_miss_rate")
    assumed = "ASSUMED" in str(data["perc"].get("flag", "")) or "assumed" in flag
    if assumed:
        see = "Detectors on each approach, or a camera. YOLO with a region of interest can read the same queue. This run had no field video, so detector error is assumed"
        see += f" ({miss:.0%} miss in the smoke check)." if isinstance(miss, (int, float)) else "."
    else:
        see = "Detectors on each approach, or a camera. YOLO with a region of interest can read the same queue. Detector error in this run comes from supplied video."
    cards = [
        (
            "01",
            "See",
            see,
        ),
        (
            "02",
            "Score",
            "Each queued vehicle is scaled by its idle-fuel weight. Moving vehicles count at the tuned fraction. The phase changes only after minimum green, and only if the gain clears hysteresis.",
        ),
        (
            "03",
            "Measure",
            "Fuel and CO₂ come from SUMO on every completed trip. Waiting and queues use the same seed the other controllers saw. The test set was not used to pick the settings.",
        ),
    ]
    gap = 0.18
    width = (CONTENT_W - 2 * gap) / 3
    for i, (num, title, body) in enumerate(cards):
        x = L + i * (width + gap)
        _card(slide, x, 1.75, width, 4.15)
        write(slide, x + 0.26, 1.98, width - 0.5, 0.36, [[(num, 18, AMBER, True, TITLE)]])
        write(slide, x + 0.26, 2.45, width - 0.5, 0.5, [[(title, 26, INK, True, TITLE)]])
        write(slide, x + 0.26, 3.2, width - 0.52, 2.4, [[(body, 15, INK, False, BODY)]])
    notes(
        slide,
        "If asked about the camera: the noise model is assumed. Supply data/video and labels to replace it. "
        "Do not claim a field detector result.",
    )


def _demand_blurb(name, demand) -> str:
    block = demand.get(name) or {}
    if name == "dynamic":
        first = (block.get("blocks") or [{}])[0]
        minutes = float(first.get("duration", 0)) / 60
        return f"The heavy axis swaps every {minutes:.0f} min. {first.get('N', 0):.0f} against {first.get('E', 0):.0f} veh/h."
    if name == "peak_unbalanced":
        return f"North–south {block.get('N', 0):.0f} veh/h. East–west {block.get('E', 0):.0f}."
    return f"{block.get('N', 0):.0f} veh/h on every approach."


def slide_design(prs, data, page, _total):
    slide = blank(prs)
    chrome(
        slide,
        "The experiment",
        "Same cars for every controller",
        "Settings are frozen before the test. A seed is one hour of the same demand, replayed.",
        page,
    )
    protocol = data["cfg"].get("seed_protocol") or {}
    roles = [
        ("Train", protocol.get("train"), "Reinforcement-learning baseline only"),
        ("Validation", protocol.get("validation"), "Settings chosen here, then frozen"),
        ("Test", protocol.get("test"), "The numbers in the rest of this deck"),
    ]
    gap = 0.16
    width = (CONTENT_W - 2 * gap) / 3
    for i, (name, span, role) in enumerate(roles):
        x = L + i * (width + gap)
        _card(slide, x, 1.7, width, 1.55)
        write(slide, x + 0.22, 1.82, width - 0.4, 0.26, [[(name.upper(), 12, AMBER, True, BODY)]])
        label = f"{span[0]} – {span[1]}" if span and len(span) == 2 else "—"
        write(slide, x + 0.22, 2.1, width - 0.4, 0.42, [[(label, 22, INK, True, TITLE)]])
        write(slide, x + 0.22, 2.58, width - 0.4, 0.48, [[(role, 13, MUTED, False, BODY)]])
    demand = data["cfg"].get("demand") or {}
    names = [row["scenario"] for row in data["headlines"]] or list(demand)
    gap = 0.16
    width = (CONTENT_W - 3 * gap) / 4
    for i, name in enumerate(names[:4]):
        x = L + i * (width + gap)
        _card(slide, x, 3.45, width, 1.85)
        write(slide, x + 0.18, 3.58, width - 0.32, 0.45, [[(_scenario(name), 16, INK, True, TITLE)]])
        write(slide, x + 0.18, 4.12, width - 0.34, 0.95, [[(_demand_blurb(name, demand), 13, MUTED, False, BODY)]])
    present = data["summary"].get("controllers") or []
    others = [CTRL.get(name, name) for name in ("fixed", "webster", "actuated", "maxpressure", "ours_count", "rl_ppo") if name in present]
    write(
        slide,
        L,
        5.5,
        CONTENT_W,
        0.7,
        [[(
            "Compared with " + ", ".join(others) + ".",
            15,
            INK,
            False,
            BODY,
        )]],
    )
    sub = data["sublane"]
    if sub and sub.get("used_sublane") is False:
        write(
            slide,
            L,
            6.2,
            CONTENT_W,
            0.35,
            [[("Built with standard lanes.", 13, MUTED, False, BODY)]],
        )
    notes(
        slide,
        "Same seed means identical demand. Test seeds are 1–30 after config.lock. "
        "Mention the sublane fallback only if asked: netconvert failed, standard lanes were used.",
    )


def slide_headlines(prs, data, page, _total):
    slide = blank(prs)
    headlines = data["headlines"]
    n_pairs = None
    if headlines:
        comp = _comp(data, headlines[0]["scenario"], "fixed")
        if comp:
            n_pairs = comp.get("n_pairs")
    dek = "Fuel per completed vehicle against fixed time. Bootstrap 95% intervals."
    if n_pairs:
        dek = f"Fuel per completed vehicle against fixed time. {n_pairs:.0f} paired seeds. Bootstrap 95% intervals."
    chrome(slide, "Test set", "Less fuel than fixed time, every scenario", dek, page)
    if not headlines:
        write(slide, L, 2.4, CONTENT_W, 0.5, [[("Run analyze.py to fill results/headlines.json.", 16, MUTED, False, BODY)]])
        return
    gap = 0.16
    width = (CONTENT_W - 3 * gap) / 4
    peak = max(row["pct_fuel_reduction_vs_fixed"] for row in headlines) or 1
    for i, row in enumerate(headlines[:4]):
        x = L + i * (width + gap)
        _card(slide, x, 1.75, width, 3.85)
        rect(slide, x + 0.24, 1.98, 0.55, 0.045, AMBER)
        write(slide, x + 0.22, 2.15, width - 0.4, 0.55, [[(_scenario(row["scenario"]), 16, INK, True, TITLE)]])
        write(
            slide,
            x + 0.22,
            2.85,
            width - 0.4,
            0.7,
            [[
                (f"{row['pct_fuel_reduction_vs_fixed']:.1f}", 36, TEAL, True, TITLE),
                ("%", 18, TEAL, True, TITLE),
            ]],
        )
        write(
            slide,
            x + 0.22,
            3.65,
            width - 0.4,
            0.55,
            [[(f"{row['ci_lo']:.1f}  –  {row['ci_hi']:.1f}", 14, MUTED, False, BODY)]],
        )
        write(slide, x + 0.22, 4.15, width - 0.4, 0.3, [[("95% interval", 12, MUTED, False, BODY)]])
        bar = (width - 0.48) * (row["pct_fuel_reduction_vs_fixed"] / peak)
        rect(slide, x + 0.24, 5.15, width - 0.48, 0.08, LINE)
        rect(slide, x + 0.24, 5.15, max(bar, 0.08), 0.08, TEAL)
        flag = row.get("sanity_flag", "")
        if flag != "OK":
            write(slide, x + 0.22, 4.7, width - 0.4, 0.28, [[(str(flag), 12, CORAL, True, BODY)]])
    flags_ok = all(row.get("sanity_flag") == "OK" for row in headlines)
    note = "All four scenarios are flagged OK. Tuning stopped before these seeds were scored."
    if not flags_ok:
        note = "Read any flag that is not OK before quoting the percentage."
    rect(slide, L, 5.85, CONTENT_W, 1.0, SOFT_TEAL, radius=0.08)
    write(slide, L + 0.28, 6.12, CONTENT_W - 0.5, 0.5, [[(note, 15, INK, False, BODY)]], anchor="ctr")
    notes(
        slide,
        "Read the peak interval, not a rounded-up slogan. All numbers are from results/headlines.json. "
        "Completed-trip counts match fixed time in the summary table, so the cut is not from stranded vehicles.",
    )


def slide_baselines(prs, data, page, _total):
    slide = blank(prs)
    chrome(
        slide,
        "The honest comparison",
        "The gap that matters is versus fixed time",
        "Against a strong adaptive controller, fuel weighting is a smaller edge. It is still on the same side every time.",
        page,
    )
    scenarios = [row["scenario"] for row in data["headlines"]]
    columns = [("Scenario", 2.55), ("vs fixed", 2.43), ("vs actuated", 2.43), ("vs max-pressure", 2.55), ("vs count only", 2.32)]
    baselines = [None, "fixed", "actuated", "maxpressure", "ours_count"]
    top = 1.72
    header_h = 0.46
    row_h = 0.78
    x0 = L
    rect(slide, x0, top, CONTENT_W, header_h, NAVY)
    x = x0
    for title, width in columns:
        write(slide, x + 0.12, top, width - 0.16, header_h, [[(title, 13, WHITE, True, BODY)]], anchor="ctr")
        x += width
    for r, scenario in enumerate(scenarios):
        y = top + header_h + r * row_h
        rect(slide, x0, y, CONTENT_W, row_h, WHITE if r % 2 == 0 else SOFT)
        x = x0
        for c, (_title, width) in enumerate(columns):
            if c == 0:
                write(slide, x + 0.14, y, width - 0.2, row_h, [[(_scenario(scenario), 14, INK, True, BODY)]], anchor="ctr")
            else:
                comp = _comp(data, scenario, baselines[c])
                if not comp:
                    write(slide, x + 0.08, y, width - 0.12, row_h, [[("—", 14, MUTED, False, BODY)]], align=PP_ALIGN.CENTER, anchor="ctr")
                else:
                    tone = TEAL if comp["pct_reduction_mean"] > 0 else CORAL
                    write(
                        slide,
                        x + 0.08,
                        y + 0.08,
                        width - 0.12,
                        0.36,
                        [[(_fmt_pct(comp["pct_reduction_mean"]), 16, tone, True, TITLE)]],
                        align=PP_ALIGN.CENTER,
                    )
                    write(
                        slide,
                        x + 0.06,
                        y + 0.4,
                        width - 0.1,
                        0.28,
                        [[(f"{comp['pct_reduction_ci_lo']:.1f} – {comp['pct_reduction_ci_hi']:.1f}", 11, MUTED, False, BODY)]],
                        align=PP_ALIGN.CENTER,
                    )
            x += width
    mp = [_comp(data, s, "maxpressure") for s in scenarios]
    mp = [row for row in mp if row]
    ct = [_comp(data, s, "ours_count") for s in scenarios]
    ct = [row for row in ct if row]
    bits = []
    if mp:
        lo = min(row["pct_reduction_mean"] for row in mp)
        hi = max(row["pct_reduction_mean"] for row in mp)
        above = all(row["pct_reduction_ci_lo"] > 0 for row in mp)
        tail = " Every 95% interval is above zero." if above else ""
        bits.append(f"Versus max-pressure: {_fmt_pct(lo)} to {_fmt_pct(hi)}.{tail}")
    if ct:
        lo = min(row["pct_reduction_mean"] for row in ct)
        hi = max(row["pct_reduction_mean"] for row in ct)
        bits.append(f"Versus the count-only ablation: {_fmt_pct(lo)} to {_fmt_pct(hi)}.")
    ppo = [_comp(data, s, "rl_ppo") for s in scenarios]
    ppo = [row for row in ppo if row]
    if ppo and all(row["pct_reduction_mean"] > 0 for row in ppo):
        bits.append("PPO used more fuel than XtraFlow in every scenario.")
    y = top + header_h + len(scenarios) * row_h + 0.16
    if bits:
        rect(slide, L, y, CONTENT_W, 0.95, SOFT_AMBER, radius=0.08)
        write(slide, L + 0.24, y + 0.14, CONTENT_W - 0.45, 0.7, [[(" ".join(bits), 14, INK, False, BODY)]])
    notes(
        slide,
        "If someone says this is just max-pressure, stay on this slide. The operational claim versus today's fixed signals "
        "is the first column. The scientific claim for fuel weights is the last two columns: small, positive, intervals above zero. "
        "PPO was selected on validation and still lost; on the peak it also gridlocked. See the summary table.",
    )


def slide_experience(prs, data, page, _total):
    slide = blank(prs)
    focus = _focus(data)
    fixed_n = _mean(data, focus, "fixed", "n_completed_mean")
    ours_n = _mean(data, focus, "XtraFlow", "n_completed_mean")
    matched = fixed_n is not None and ours_n is not None and abs(fixed_n - ours_n) < 0.05
    dek = f"{_scenario(focus)}. This is the scenario the settings were tuned on. Figures are the locked test."
    if matched:
        dek = (
            f"{_scenario(focus)}, the tuning scenario, on the locked test. "
            f"Completed trips match fixed time ({fixed_n:,.0f})."
        )
    chrome(slide, "What changes", "Shorter waits, shorter queues, less CO₂", dek, page)
    specs = [
        ("Fuel / vehicle", "fuel_per_vehicle_L_mean", "L", 3),
        ("Mean wait", "mean_waiting_s_mean", "s", 1),
        ("Mean queue", "mean_queue_veh_mean", "veh", 1),
        ("CO₂", "total_CO2_kg_mean", "kg", 0),
    ]
    gap = 0.16
    width = (CONTENT_W - 3 * gap) / 4
    for i, (label, key, unit, digits) in enumerate(specs):
        before = _mean(data, focus, "fixed", key)
        after = _mean(data, focus, "XtraFlow", key)
        x = L + i * (width + gap)
        _card(slide, x, 1.75, width, 2.15)
        write(slide, x + 0.18, 1.88, width - 0.32, 0.3, [[(label.upper(), 12, AMBER, True, BODY)]])
        if before is None or after is None:
            write(slide, x + 0.18, 2.4, width - 0.32, 0.4, [[("—", 18, MUTED, False, BODY)]])
            continue
        spec = f"{{:.{digits}f}}"
        write(slide, x + 0.18, 2.28, width - 0.32, 0.4, [[(spec.format(before) + f" {unit}", 14, MUTED, False, BODY)]])
        write(slide, x + 0.18, 2.68, width - 0.32, 0.55, [[(spec.format(after) + f" {unit}", 22, TEAL, True, TITLE)]])
        write(slide, x + 0.18, 3.3, width - 0.32, 0.3, [[("from fixed time", 12, MUTED, False, BODY)]])
    others = [row["scenario"] for row in data["headlines"] if row["scenario"] != focus]
    write(slide, L, 4.12, CONTENT_W, 0.3, [[("WAITING TIME ON THE OTHER SCENARIOS", 12, AMBER, True, BODY)]])
    y = 4.48
    for scenario in others:
        before = _mean(data, scenario, "fixed", "mean_waiting_s_mean")
        after = _mean(data, scenario, "XtraFlow", "mean_waiting_s_mean")
        _card(slide, L, y, CONTENT_W, 0.62)
        write(slide, L + 0.22, y, 3.2, 0.62, [[(_scenario(scenario), 15, INK, True, BODY)]], anchor="ctr")
        if before is not None and after is not None and before:
            cut = (before - after) / before * 100
            write(
                slide,
                L + 3.4,
                y,
                5.4,
                0.62,
                [[(f"{before:.1f} s   to   {after:.1f} s", 15, INK, False, BODY)]],
                anchor="ctr",
            )
            write(
                slide,
                L + 8.8,
                y,
                3.1,
                0.62,
                [[(f"{cut:.0f}% shorter", 15, TEAL, True, BODY)]],
                align=PP_ALIGN.RIGHT,
                anchor="ctr",
            )
        y += 0.72
    notes(
        slide,
        "Levels are means from results/tables/summary_mean_std.csv. The fuel percentage on the previous slide "
        "is the mean of paired percent cuts, which is not identical to the percent gap between these two means. "
        "Waiting cuts are percent gaps between means. Say that if someone mixes the two.",
    )


def slide_robust(prs, data, page, _total):
    slide = blank(prs)
    curve = [row for row in data["robust"] if row["controller"] == "XtraFlow" and row["kind"] == "XtraFlow"]
    curve.sort(key=lambda row: row["miss"])
    refs = {
        row["controller"]: row
        for row in data["robust"]
        if row["kind"] == "reference" and row["miss"] == 0
    }
    empirical = next(
        (row for row in data["robust"] if row["controller"] == "XtraFlow" and row["kind"] == "empirical_noise"),
        None,
    )
    n = curve[0]["n"] if curve else None
    dek = "Peak, one-sided. Vehicles are dropped from the detector at random."
    if n:
        dek = f"Peak, one-sided. {n} seeds. Vehicles are dropped from the detector at random."
    chrome(slide, "If the camera misses", "A missed vehicle does not erase the saving", dek, page)
    if not curve:
        write(slide, L, 2.2, CONTENT_W, 0.4, [[("Robustness results are not loaded.", 16, MUTED, False, BODY)]])
        return
    gap = 0.16
    width = (CONTENT_W - (len(curve) - 1) * gap) / len(curve)
    for i, row in enumerate(curve):
        x = L + i * (width + gap)
        _card(slide, x, 1.75, width, 2.45)
        write(slide, x + 0.18, 1.92, width - 0.32, 0.3, [[(f"{row['miss']:.0%} missed", 13, AMBER, True, BODY)]])
        write(slide, x + 0.18, 2.35, width - 0.32, 0.6, [[(f"{row['mean']:.3f}", 28, TEAL, True, TITLE)]])
        write(slide, x + 0.18, 3.05, width - 0.32, 0.3, [[("litres / vehicle", 13, MUTED, False, BODY)]])
        write(slide, x + 0.18, 3.5, width - 0.32, 0.35, [[(f"± {row['std']:.3f}   ·   n={row['n']}", 12, MUTED, False, BODY)]])
    rect(slide, L, 4.45, CONTENT_W, 2.35, WHITE, line=LINE, radius=0.08)
    write(slide, L + 0.3, 4.62, 8, 0.3, [[("SAME SEEDS, NO MISSES", 12, AMBER, True, BODY)]])
    rx = L + 0.3
    for key, label in (("XtraFlow", "XtraFlow"), ("actuated", "Actuated"), ("fixed", "Fixed time")):
        row = refs.get(key)
        if key == "XtraFlow":
            row = next((item for item in curve if item["miss"] == 0), row)
        if not row:
            continue
        write(slide, rx, 5.05, 3.4, 0.45, [[(f"{row['mean']:.3f} L", 22, TEAL if key == "XtraFlow" else INK, True, TITLE)]])
        write(slide, rx, 5.55, 3.4, 0.3, [[(label, 13, MUTED, False, BODY)]])
        rx += 3.6
    extra = ""
    if empirical:
        extra = f" The assumed noise model at {empirical['miss']:.0%} miss lands at {empirical['mean']:.3f} L."
    write(
        slide,
        L + 0.3,
        6.05,
        CONTENT_W - 0.6,
        0.5,
        [[("XtraFlow stays under both reference lines across this miss range." + extra, 14, INK, False, BODY)]],
    )
    notes(
        slide,
        "This is not the full 30-seed test. It is the robustness sweep on the peak scenario. "
        "The curve is flat in the third decimal from 0 to 30% misses. Perception noise elsewhere in the deck is assumed.",
    )


def slide_grid(prs, data, page, _total):
    slide = blank(prs)
    means = (data["grid"].get("summary_means") or {}).get("fuel_per_vehicle_L") or {}
    waits = (data["grid"].get("summary_means") or {}).get("mean_waiting_s") or {}
    rows = data["grid"].get("rows") or []
    n = len([row for row in rows if row.get("controller") == "XtraFlow"])
    coord = data["grid"].get("coordination_reduces_fuel")
    same = (
        "XtraFlow" in means
        and "XtraFlow_coord" in means
        and abs(means["XtraFlow"] - means["XtraFlow_coord"]) < 1e-9
    )
    dek = "A 2×2 network. The controller was tuned for a single junction."
    if n:
        dek = f"A 2×2 network, {n} seeds. The controller was tuned for a single junction."
    chrome(slide, "Where it does not transfer", "On a grid, fuel goes the wrong way", dek, page)
    order = [("actuated", "Actuated", "Lowest fuel here"), ("fixed", "Fixed time", "The simple baseline"), ("XtraFlow", "XtraFlow", "Higher fuel")]
    gap = 0.18
    width = (CONTENT_W - 2 * gap) / 3
    for i, (key, label, caption) in enumerate(order):
        x = L + i * (width + gap)
        tone = CORAL if key == "XtraFlow" else TEAL
        fill = SOFT_CORAL if key == "XtraFlow" else WHITE
        _card(slide, x, 1.75, width, 3.35, fill=fill)
        write(slide, x + 0.24, 1.95, width - 0.45, 0.3, [[(label.upper(), 13, tone, True, BODY)]])
        fuel = means.get(key)
        wait = waits.get(key)
        write(
            slide,
            x + 0.24,
            2.45,
            width - 0.45,
            0.7,
            [[(f"{fuel:.3f}" if fuel is not None else "—", 32, tone, True, TITLE)]],
        )
        write(slide, x + 0.24, 3.2, width - 0.45, 0.3, [[("litres / vehicle", 13, MUTED, False, BODY)]])
        if wait is not None:
            write(slide, x + 0.24, 3.65, width - 0.45, 0.35, [[(f"{wait:.1f} s mean wait", 15, INK, False, BODY)]])
        write(slide, x + 0.24, 4.15, width - 0.45, 0.4, [[(caption, 14, MUTED, False, BODY)]])
    if coord is False and same:
        sentence = "A neighbor-pressure coordination term matched independent control exactly. It did not reduce fuel or waiting."
    elif coord is False:
        sentence = "The coordination variant did not reduce fuel."
    else:
        sentence = "Read results/grid_results.json before describing coordination."
    rect(slide, L, 5.3, CONTENT_W, 1.5, NAVY, radius=0.08)
    write(slide, L + 0.32, 5.5, CONTENT_W - 0.6, 0.35, [[("DO NOT SCALE THIS TO A CITY", 12, AMBER, True, BODY)]])
    write(slide, L + 0.32, 5.9, CONTENT_W - 0.6, 0.65, [[(sentence + " A corridor needs its own design.", 16, WHITE, False, BODY)]])
    notes(
        slide,
        "Say this slide out loud. Independent and coordinated XtraFlow both used more fuel and more waiting than fixed time "
        "and actuated. Coordination did not change outcomes. Decision D018. Label: simulation-based estimate.",
    )


def _plain_verdict(value: str) -> str:
    mapping = {
        "no_increase": "No increase",
        "unchanged_direction": "Same direction",
    }
    return mapping.get(value, (value or "Not loaded").replace("_", " "))


def slide_checks(prs, data, page, _total):
    slide = blank(prs)
    chrome(
        slide,
        "Beside the headline",
        "Conflicts did not rise. CO₂ still falls.",
        "One caveat sits with those two checks: the camera model is assumed.",
        page,
    )
    safety = data["safety"]
    xcheck = data["xcheck"]
    perc = data["perc"]
    noise = perc.get("noise_model") or {}
    miss = noise.get("detect_miss_rate")
    assumed = "ASSUMED" in str(perc.get("flag", ""))
    cards = []
    delta = safety.get("ours_minus_fixed_mean_conflicts")
    safety_body = "Time-to-collision conflicts from the simulator."
    if delta is not None:
        safety_body += f" XtraFlow minus fixed time averages {delta:.0f}."
    safety_body += " A model count, not a crash record."
    cards.append((TEAL, _plain_verdict(safety.get("verdict", "")), "Safety", safety_body))
    primary = xcheck.get("pct_reduction_primary")
    alternate = xcheck.get("pct_reduction_alternate")
    emis = "Peak scenario, cross-check seeds."
    if primary is not None and alternate is not None:
        emis = (
            f"Primary model {_fmt_pct(primary)}. Alternate model {_fmt_pct(alternate)}. "
            "The reduction shrinks. It does not flip."
        )
    cards.append((TEAL, _plain_verdict(xcheck.get("verdict", "")), "Emissions model", emis))
    perc_title = "Assumed" if assumed else "From video"
    perc_body = "No field video in this run." if assumed else "Noise model derived from supplied video."
    if isinstance(miss, (int, float)):
        perc_body += f" Smoke-test miss rate {miss:.0%}."
    if noise.get("note"):
        perc_body += " Treat detector error as assumed until labels exist."
    cards.append((AMBER, perc_title, "Perception", perc_body))
    gap = 0.18
    width = (CONTENT_W - 2 * gap) / 3
    for i, (tone, big, label, body) in enumerate(cards):
        x = L + i * (width + gap)
        _card(slide, x, 1.75, width, 4.15)
        rect(slide, x + 0.26, 2.0, 0.55, 0.045, tone)
        write(slide, x + 0.24, 2.2, width - 0.45, 0.3, [[(label.upper(), 12, tone, True, BODY)]])
        write(slide, x + 0.24, 2.55, width - 0.45, 0.85, [[(big, 28, INK, True, TITLE)]])
        write(slide, x + 0.24, 3.55, width - 0.48, 2.05, [[(body, 15, INK, False, BODY)]])
    notes(
        slide,
        "Safety verdict comes from results/safety.json. Emission cross-check is HBEFA3 versus PHEMlight on a smaller seed set "
        "than the main test; quote both percentages. Perception flag is ASSUMED_NOISE_MODEL_NO_USER_VIDEO.",
    )


def _millions(value: float) -> str:
    return f"{value / 1e6:.1f} million litres"


def _tonnes(value: float) -> str:
    return f"{value:,.0f} tonnes"


def slide_scale(prs, data, page, _total):
    slide = blank(prs)
    extra = data["extra"]
    chrome(
        slide,
        "Scaling",
        "Per vehicle is measured. Per year is a range.",
        "The wide bar is the assumed city size, not uncertainty in the junction test.",
        page,
    )
    saving = extra.get("measured_saving_L_per_veh") or {}
    annual = extra.get("annual_litres") or {}
    co2 = extra.get("annual_tonnes_CO2") or {}
    basis = _scenario(extra.get("scenario_basis", ""))
    _card(slide, L, 1.72, 7.35, 2.15)
    if saving:
        write(slide, L + 0.28, 1.88, 6.8, 0.28, [[(f"MEASURED ON {basis.upper()}", 12, AMBER, True, BODY)]])
        write(
            slide,
            L + 0.28,
            2.22,
            6.8,
            0.65,
            [[
                (f"{saving['mean']:.3f}", 32, TEAL, True, TITLE),
                ("  L saved / vehicle", 16, INK, False, BODY),
            ]],
        )
        write(
            slide,
            L + 0.28,
            3.05,
            6.8,
            0.5,
            [[(
                f"5th – 95th percentile of that mean: {saving['p05']:.3f} – {saving['p95']:.3f} L",
                14,
                MUTED,
                False,
                BODY,
            )]],
        )
    if annual:
        p05, med, p95 = annual["p05"], annual["median"], annual["p95"]
        write(slide, L, 4.05, 7.3, 0.28, [[("IF THAT SAVING IS MULTIPLIED OUT", 12, AMBER, True, BODY)]])
        span = p95 - p05
        rect(slide, L, 4.42, 7.35, 0.14, RGBColor(0xC5, 0xDD, 0xD4))
        if span > 0:
            tick = L + 7.35 * ((med - p05) / span)
            rect(slide, tick - 0.03, 4.28, 0.06, 0.42, TEAL)
        write(slide, L, 4.78, 3.2, 0.28, [[(_millions(p05), 12, MUTED, False, BODY)]])
        write(slide, L + 4.15, 4.78, 3.2, 0.28, [[(_millions(p95), 12, MUTED, False, BODY)]], align=PP_ALIGN.RIGHT)
        write(slide, L, 5.2, 7.3, 0.48, [[(_millions(med), 22, INK, True, TITLE)]])
        write(slide, L, 5.68, 7.3, 0.28, [[("median of the scaled draws", 13, MUTED, False, BODY)]])
        if co2:
            write(
                slide,
                L,
                6.05,
                7.3,
                0.55,
                [[(
                    f"CO₂ median {_tonnes(co2['median'])}   ·   {_tonnes(co2['p05'])} – {_tonnes(co2['p95'])}",
                    13,
                    MUTED,
                    False,
                    BODY,
                )]],
            )
    ex = data["cfg"].get("extrapolation") or {}
    _card(slide, 8.1, 1.72, 4.73, 4.95)
    write(slide, 8.34, 1.9, 4.3, 0.7, [[("Why the bar is wide", 18, INK, True, TITLE)]])
    ranges = [
        ("Junctions", ex.get("n_intersections")),
        ("Vehicles / peak hour", ex.get("vehicles_per_peak_hour")),
        ("Peak hours / day", ex.get("peak_hours_per_day")),
        ("Days / year", ex.get("days_per_year")),
    ]
    y = 2.7
    for label, block in ranges:
        if not block:
            continue
        write(slide, 8.34, y, 4.2, 0.24, [[(label, 12, MUTED, False, BODY)]])
        write(
            slide,
            8.34,
            y + 0.22,
            4.2,
            0.32,
            [[(f"{block['low']:,.0f}  –  {block['high']:,.0f}", 16, INK, True, TITLE)]],
        )
        y += 0.72
    write(
        slide,
        8.34,
        5.85,
        4.25,
        0.6,
        [[("Rupee value uses a placeholder price, so it is not shown.", 13, MUTED, False, BODY)]],
    )
    notes(
        slide,
        "Lead with the per-vehicle litres. The annual figure multiplies that saving by the ranges on the right, "
        "Monte Carlo from config.yaml. The price in fuel.price_inr_per_L is a placeholder. "
        "Quote the extrapolation label: simulation-based estimate, not a deployment result.",
    )


def slide_close(prs, data, page, _total):
    slide = blank(prs, dark=True)
    write(slide, 0.78, 0.85, 8, 0.28, [[("BEFORE A STRONGER CLAIM", 13, AMBER, True, BODY)]])
    write(slide, 0.75, 1.2, 11, 0.8, [[("XtraFlow", 44, WHITE, True, TITLE)]])
    write(
        slide,
        0.78,
        2.1,
        10.5,
        0.7,
        [[("Smarter signals should burn less fuel.", 24, RGBColor(0xF0, 0xC2, 0x6A), False, TITLE)]],
    )
    steps = [
        ("01", "Count the junction", "Replace the assumed flows with observed demand before quoting a site."),
        ("02", "Film the queue", "A real video replaces the assumed detector-error model."),
        ("03", "Redesign the corridor", "Neighbor pressure, as implemented, did not help the grid."),
    ]
    gap = 0.16
    width = (CONTENT_W - 2 * gap) / 3
    for i, (num, title, body) in enumerate(steps):
        x = L + i * (width + gap)
        rect(slide, x, 3.15, width, 2.35, NAVY_2, radius=0.08)
        write(slide, x + 0.22, 3.32, width - 0.4, 0.3, [[(num, 14, AMBER, True, TITLE)]])
        write(slide, x + 0.22, 3.7, width - 0.42, 0.55, [[(title, 18, WHITE, True, TITLE)]])
        write(slide, x + 0.22, 4.35, width - 0.42, 0.9, [[(body, 14, MIST, False, BODY)]])
    write(slide, 0.78, 5.8, 10, 0.3, [[(data["url"] or "", 14, MIST, False, BODY)]])
    write(slide, 0.78, 6.2, 11, 0.4, [[(data["label"], 14, RGBColor(0x8A, 0x9B, 0xA8), False, BODY)]])
    footer(slide, page, dark=True)
    notes(
        slide,
        "Close on the three conditions. Do not end on the annual litre range. "
        "The single-junction fuel result versus fixed time is the result. The grid is the limit.",
    )


def main():
    data = load()
    prs = Presentation()
    prs.slide_width = Inches(PAGE_W)
    prs.slide_height = Inches(PAGE_H)
    prs.core_properties.title = "XtraFlow"
    prs.core_properties.subject = "Fuel-weighted traffic signals"
    prs.core_properties.category = data["label"]
    builders = [
        slide_title,
        slide_problem,
        slide_weights,
        slide_cycle,
        slide_design,
        slide_headlines,
        slide_baselines,
        slide_experience,
        slide_robust,
        slide_grid,
        slide_checks,
        slide_scale,
        slide_close,
    ]
    total = len(builders)
    for page, builder in enumerate(builders, start=1):
        builder(prs, data, page, total)
    out = ROOT / "results" / "deck.pptx"
    prs.save(str(out))
    print(f"Wrote {out} ({total} slides)")


if __name__ == "__main__":
    main()
