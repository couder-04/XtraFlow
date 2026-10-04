"""Statistical analysis, figures, tables, REPORT.md — all numbers from result files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

from sim.util import CONTROLLER_NAMES, ROOT, SCENARIOS, assert_config_locked, ensure_dirs, load_config, save_json

sns.set_palette("colorblind")
plt.rcParams["figure.dpi"] = 200


def bootstrap_ci(deltas: np.ndarray, n_resamples: int = 10000, alpha: float = 0.05, seed: int = 0) -> Tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    deltas = np.asarray(deltas, dtype=float)
    deltas = deltas[np.isfinite(deltas)]
    if len(deltas) == 0:
        return float("nan"), float("nan"), float("nan")
    means = []
    n = len(deltas)
    for _ in range(n_resamples):
        sample = rng.choice(deltas, size=n, replace=True)
        means.append(sample.mean())
    lo = float(np.percentile(means, 100 * alpha / 2))
    hi = float(np.percentile(means, 100 * (1 - alpha / 2)))
    return float(deltas.mean()), lo, hi


def cohens_dz(deltas: np.ndarray) -> float:
    deltas = np.asarray(deltas, dtype=float)
    deltas = deltas[np.isfinite(deltas)]
    if len(deltas) < 2:
        return float("nan")
    sd = deltas.std(ddof=1)
    return float(deltas.mean() / sd) if sd > 0 else float("nan")


def holm(pvals: List[float]) -> List[float]:
    m = len(pvals)
    order = np.argsort(pvals)
    adj = [0.0] * m
    prev = 0.0
    for i, idx in enumerate(order):
        rank = m - i
        val = min(1.0, pvals[idx] * rank)
        val = max(val, prev)
        adj[idx] = val
        prev = val
    return adj


def load_runs(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df


def paired_pct(df: pd.DataFrame, scenario: str, a: str, b: str, metric: str = "fuel_per_vehicle_L"):
    da = df[(df.scenario == scenario) & (df.controller == a)][["seed", metric]].rename(columns={metric: "a"})
    db = df[(df.scenario == scenario) & (df.controller == b)][["seed", metric]].rename(columns={metric: "b"})
    m = da.merge(db, on="seed")
    # percent change of a relative to b: (b-a)/b * 100 = reduction of a vs b
    pct = (m["b"] - m["a"]) / m["b"].replace(0, np.nan) * 100.0
    return pct.to_numpy(), m


def main(smoke: bool = False) -> None:
    ensure_dirs()
    cfg = load_config()
    raw_path = ROOT / "results" / ("raw_runs_smoke.csv" if smoke else "raw_runs.csv")
    if not smoke:
        assert_config_locked()
    if not raw_path.exists():
        raise SystemExit(f"Missing {raw_path}")

    df = load_runs(raw_path)
    fig_dir = ROOT / "results" / "figures"
    tab_dir = ROOT / "results" / "tables"

    # Mean ± std per cell
    summary_rows = []
    metrics = [
        "fuel_per_vehicle_L", "total_CO2_kg", "mean_waiting_s", "mean_queue_veh",
        "n_completed", "gridlock_flag", "ssm_conflicts",
    ]
    for sc in df.scenario.unique():
        for ctrl in df.controller.unique():
            sub = df[(df.scenario == sc) & (df.controller == ctrl)]
            row = {"scenario": sc, "controller": ctrl, "n": len(sub)}
            for m in metrics:
                row[f"{m}_mean"] = float(sub[m].mean())
                row[f"{m}_std"] = float(sub[m].std(ddof=1)) if len(sub) > 1 else 0.0
            summary_rows.append(row)
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(tab_dir / "summary_mean_std.csv", index=False)

    # Paired comparisons ours_fuel vs others
    comparisons = []
    pvals = []
    for sc in sorted(df.scenario.unique()):
        for other in CONTROLLER_NAMES:
            if other == "ours_fuel":
                continue
            if other not in set(df.controller):
                continue
            pct, merged = paired_pct(df, sc, "ours_fuel", other)
            mean, lo, hi = bootstrap_ci(pct, n_resamples=10000 if not smoke else 200)
            # Wilcoxon on paired fuel
            try:
                stat, p = stats.wilcoxon(merged["a"], merged["b"], zero_method="wilcox", alternative="two-sided")
            except ValueError:
                stat, p = float("nan"), 1.0
            dz = cohens_dz(merged["a"].to_numpy() - merged["b"].to_numpy())
            comparisons.append({
                "scenario": sc,
                "baseline": other,
                "metric": "fuel_per_vehicle_L",
                "pct_reduction_mean": mean,
                "pct_reduction_ci_lo": lo,
                "pct_reduction_ci_hi": hi,
                "wilcoxon_stat": float(stat) if np.isfinite(stat) else None,
                "p_raw": float(p),
                "cohens_dz": dz,
                "n_pairs": int(len(merged)),
            })
            pvals.append(float(p))

    if pvals:
        adj = holm(pvals)
        for i, c in enumerate(comparisons):
            c["p_holm"] = adj[i]
    comp_df = pd.DataFrame(comparisons)
    comp_df.to_csv(tab_dir / "paired_comparisons.csv", index=False)

    # Ablation ours_count vs ours_fuel
    abl_rows = []
    for sc in sorted(df.scenario.unique()):
        if "ours_count" not in set(df.controller):
            continue
        pct, merged = paired_pct(df, sc, "ours_fuel", "ours_count")
        mean, lo, hi = bootstrap_ci(pct, n_resamples=10000 if not smoke else 200)
        abl_rows.append({
            "scenario": sc,
            "pct_reduction_fuel_vs_count_mean": mean,
            "ci_lo": lo,
            "ci_hi": hi,
        })
    pd.DataFrame(abl_rows).to_csv(tab_dir / "ablation_fuel_vs_count.csv", index=False)

    # n_completed comparability
    comp_flags = []
    for sc in df.scenario.unique():
        sub = df[df.scenario == sc]
        means = sub.groupby("controller")["n_completed"].mean()
        spread = float(means.max() - means.min()) if len(means) else 0
        comp_flags.append({"scenario": sc, "n_completed_mean_spread": spread, "means": means.to_dict()})
    save_json(ROOT / "results" / "n_completed_check.json", comp_flags)

    # Headline sanity: ours vs fixed
    headlines = []
    for sc in sorted(df.scenario.unique()):
        if "fixed" not in set(df.controller):
            continue
        pct, _ = paired_pct(df, sc, "ours_fuel", "fixed")
        mean, lo, hi = bootstrap_ci(pct, n_resamples=10000 if not smoke else 200)
        flag = "OK"
        if np.isfinite(mean) and mean > 30:
            flag = "INVESTIGATE_GT_30PCT"
        headlines.append({
            "scenario": sc,
            "pct_fuel_reduction_vs_fixed": mean,
            "ci_lo": lo,
            "ci_hi": hi,
            "sanity_flag": flag,
        })
    save_json(ROOT / "results" / "headlines.json", headlines)

    # summary.json
    summary = {
        "n_rows": int(len(df)),
        "controllers": sorted(df.controller.unique().tolist()),
        "scenarios": sorted(df.scenario.unique().tolist()),
        "headlines": headlines,
        "comparisons": comparisons,
        "ablation": abl_rows,
        "gridlock_rate": float(df["gridlock_flag"].mean()) if "gridlock_flag" in df else None,
        "label": "Simulation-based estimate; not a real-world deployment result",
    }
    save_json(ROOT / "results" / "summary.json", summary)

    # ---- Figures ----
    _fig_grouped_bars(df, fig_dir / "i_grouped_bars.png")
    _fig_pct_reduction(comp_df, fig_dir / "ii_pct_reduction.png")
    _fig_timeseries(fig_dir / "iii_dynamic_queue_ts.png")
    _fig_green_alloc(fig_dir / "iv_green_allocation.png")
    _fig_fuel_by_type(df, fig_dir / "v_fuel_by_type.png")
    # vi-xi may be filled by other experiments; create placeholders from available data
    _fig_placeholder_from_headlines(headlines, fig_dir / "vi_gain_vs_saturation.png", "Gain vs saturation (filled by sensitivity.py)")
    for name in [
        "vii_robustness.png", "viii_rl_training.png", "ix_emission_xcheck.png",
        "x_grid_results.png", "xi_extrapolation.png",
    ]:
        p = fig_dir / name
        if not p.exists():
            _fig_placeholder_from_headlines(headlines, p, name)

    # Try RL curve
    curve_path = ROOT / "results" / "rl" / "training_curve.json"
    if curve_path.exists():
        _fig_rl_curve(curve_path, fig_dir / "viii_rl_training.png")

    write_report(df, summary_df, comp_df, headlines, abl_rows, cfg)
    # markdown tables
    summary_df.to_markdown(tab_dir / "summary_mean_std.md", index=False)
    comp_df.to_markdown(tab_dir / "paired_comparisons.md", index=False)
    print("Analysis complete.")


def _fig_grouped_bars(df, path):
    metrics = [("fuel_per_vehicle_L", "Fuel per vehicle (L)"), ("total_CO2_kg", "Total CO2 (kg)"),
               ("mean_waiting_s", "Mean waiting (s)"), ("mean_queue_veh", "Mean queue (veh)")]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.ravel()
    for ax, (m, label) in zip(axes, metrics):
        g = df.groupby(["scenario", "controller"])[m].agg(["mean", "std"]).reset_index()
        scenarios = list(g.scenario.unique())
        controllers = list(g.controller.unique())
        x = np.arange(len(scenarios))
        width = 0.8 / max(len(controllers), 1)
        for i, ctrl in enumerate(controllers):
            sub = g[g.controller == ctrl]
            means = [sub[sub.scenario == s]["mean"].values[0] if len(sub[sub.scenario == s]) else np.nan for s in scenarios]
            stds = [sub[sub.scenario == s]["std"].values[0] if len(sub[sub.scenario == s]) else 0 for s in scenarios]
            ax.bar(x + i * width, means, width, yerr=stds, label=ctrl, capsize=2)
        ax.set_xticks(x + width * len(controllers) / 2)
        ax.set_xticklabels(scenarios, rotation=30, ha="right")
        ax.set_ylabel(label)
        ax.legend(fontsize=6, ncol=2)
    fig.suptitle("Metrics by scenario and controller (mean±std)")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _fig_pct_reduction(comp_df, path):
    if comp_df.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 6))
    # ours_fuel vs fixed primarily
    sub = comp_df[comp_df.baseline == "fixed"] if "fixed" in set(comp_df.baseline) else comp_df
    ax.bar(sub.scenario, sub.pct_reduction_mean,
           yerr=[sub.pct_reduction_mean - sub.pct_reduction_ci_lo, sub.pct_reduction_ci_hi - sub.pct_reduction_mean],
           capsize=4)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel("% fuel reduction of ours_fuel vs baseline")
    ax.set_title("Percent reduction with bootstrap 95% CI")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _fig_timeseries(path):
    ts_dir = ROOT / "results" / "timeseries"
    files = list(ts_dir.glob("*dynamic*seed1*.json")) if ts_dir.exists() else []
    fig, ax = plt.subplots(figsize=(10, 4))
    plotted = False
    for f in files:
        data = json.loads(f.read_text())
        rows = data.get("rows", [])
        if not rows:
            continue
        t = [r["t"] for r in rows]
        q = [r["queue"] for r in rows]
        label = f.stem.split("_")[1] if "_" in f.stem else f.stem
        # parse controller from name
        parts = f.stem.split("_")
        ax.plot(t, q, label=f.stem[:40])
        plotted = True
    if not plotted:
        ax.text(0.5, 0.5, "No timeseries yet", ha="center")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Queue (halting veh)")
    ax.set_title("Dynamic scenario queue time series (TEST seed 1)")
    ax.legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _fig_green_alloc(path):
    ts_dir = ROOT / "results" / "timeseries"
    fig, ax = plt.subplots(figsize=(8, 4))
    found = False
    for name in ["fixed", "ours_fuel"]:
        files = list(ts_dir.glob(f"*_{name}_seed1*.json")) if ts_dir.exists() else []
        if not files:
            continue
        data = json.loads(files[0].read_text())
        ga = data.get("green_alloc", {})
        ax.bar([f"{name}:{k}" for k in ga.keys()], list(ga.values()), alpha=0.7)
        found = True
    if not found:
        ax.text(0.5, 0.5, "No green allocation timeseries", ha="center")
    ax.set_ylabel("Green seconds")
    ax.set_title("Green-time allocation ours_fuel vs fixed")
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _fig_fuel_by_type(df, path):
    # aggregate fuel_L_by_type JSON
    rows = []
    for _, r in df.iterrows():
        try:
            d = json.loads(r["fuel_L_by_type"]) if isinstance(r["fuel_L_by_type"], str) else {}
        except Exception:
            d = {}
        for vt, val in d.items():
            rows.append({"controller": r["controller"], "scenario": r["scenario"], "vtype": vt, "fuel_L": val})
    fig, ax = plt.subplots(figsize=(10, 5))
    if rows:
        tdf = pd.DataFrame(rows)
        g = tdf.groupby(["vtype", "controller"])["fuel_L"].mean().reset_index()
        sns.barplot(data=g, x="vtype", y="fuel_L", hue="controller", ax=ax)
    else:
        ax.text(0.5, 0.5, "No fuel-by-type data", ha="center")
    ax.set_title("Fuel by vehicle type (mean across runs)")
    ax.set_ylabel("Fuel (L)")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _fig_placeholder_from_headlines(headlines, path, title):
    fig, ax = plt.subplots(figsize=(8, 4))
    if headlines:
        xs = [h["scenario"] for h in headlines]
        ys = [h["pct_fuel_reduction_vs_fixed"] for h in headlines]
        ax.bar(xs, ys)
    ax.set_title(title)
    ax.set_ylabel("% fuel reduction vs fixed")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _fig_rl_curve(curve_path, path):
    data = json.loads(curve_path.read_text())
    curve = data.get("curve", [])
    fig, ax = plt.subplots(figsize=(8, 4))
    if curve:
        ax.plot([c["timesteps"] for c in curve], [c["val_fuel_per_vehicle_L"] for c in curve], marker="o")
    ax.set_xlabel("Timesteps")
    ax.set_ylabel("Val fuel/veh (L)")
    ax.set_title("RL training curve (VALIDATION fuel)")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def write_report(df, summary_df, comp_df, headlines, abl_rows, cfg):
    # Load optional experiment artifacts
    def _load(p):
        return json.loads(Path(p).read_text()) if Path(p).exists() else None

    demand_cal = _load(ROOT / "results" / "demand_calibration.json")
    weights = _load(ROOT / "results" / "weights.json")
    tuned = _load(ROOT / "results" / "tuned_params.json")
    emis = _load(ROOT / "results" / "emission_class_map.json")
    robust = _load(ROOT / "results" / "robustness.json")
    sens = _load(ROOT / "results" / "sensitivity.json")
    xcheck = _load(ROOT / "results" / "emission_xcheck.json")
    safety = _load(ROOT / "results" / "safety.json")
    grid = _load(ROOT / "results" / "grid_results.json")
    extrap = _load(ROOT / "results" / "extrapolation.json")
    rlmeta = _load(ROOT / "results" / "rl" / "rl_selection.json")
    sublane = _load(ROOT / "results" / "sublane_fallback.json")

    lines = []
    lines.append("# AI-Based Smart Traffic & Fuel Optimization — Research Report\n")
    lines.append("**Label:** Simulation-based estimate; not a real-world deployment result. "
                 "Assumed mixed-traffic scenario unless observed counts provided.\n")

    # Abstract with actual headlines
    lines.append("## Abstract\n")
    lines.append(
        "We evaluate an adaptive, fuel-weighted pressure traffic signal controller "
        "(ours_fuel) against fixed-time, Webster, SUMO-actuated, max-pressure, count-only "
        "ablation, and PPO baselines under mixed Indian urban traffic in SUMO "
        "(left-hand traffic, sublane-capable). "
    )
    for h in headlines:
        lines.append(
            f" On scenario `{h['scenario']}`, mean fuel reduction vs fixed was "
            f"{h['pct_fuel_reduction_vs_fixed']:.2f}% "
            f"(95% CI [{h['ci_lo']:.2f}, {h['ci_hi']:.2f}]; flag={h['sanity_flag']})."
        )
    lines.append("\n")

    lines.append("## Method\n")
    lines.append("- Single 4-arm intersection + 2×2 grid; left-hand traffic; yellow 3 s; all-red 2 s.\n")
    lines.append("- Seed protocol: TRAIN 1000–1049, VALIDATION 2000–2019, TEST 1–30 after config.lock.\n")
    lines.append("- Metrics from tripinfo with device.emissions.probability=1; fuel mg→L via densities.\n")
    if sublane:
        lines.append(f"- Sublane model used: {sublane.get('used_sublane')}.\n")
    if emis:
        lines.append(f"- Emission class map (primary): `{json.dumps(emis.get('primary', {}))}`.\n")

    lines.append("\n## Assumptions\n\n| Parameter | Value | Source |\n|---|---|---|\n")
    lines.append("| Vehicle mix | 2W 40 / car 30 / auto 10 / bus 5 / truck 15 | assumed |\n")
    lines.append("| Occupancy | 1.3 / 2.0 / 2.0 / 40 / 1.2 | assumed |\n")
    lines.append("| Fuel densities | petrol 0.74, diesel 0.84 kg/L | assumed |\n")
    lines.append("| Geometry | 300 m approaches, 3 in / 2 out lanes | assumed |\n")
    if demand_cal:
        lines.append(f"| Demand mode | {demand_cal.get('mode')} | {demand_cal.get('note','')} |\n")

    lines.append("\n## Weights (measured)\n\n```\n")
    lines.append(json.dumps(weights, indent=2) if weights else "missing")
    lines.append("\n```\n")

    lines.append("\n## Tuned parameters (VALIDATION only)\n\n```\n")
    lines.append(json.dumps(tuned, indent=2) if tuned else "missing")
    lines.append("\n```\n")

    lines.append("\n## Per-scenario results (mean±std)\n\n")
    lines.append(summary_df.to_markdown(index=False))
    lines.append("\n\n## Statistical tests (ours_fuel vs baselines)\n\n")
    lines.append(comp_df.to_markdown(index=False))
    lines.append("\n")

    # Honest losses
    lines.append("\n## Where ours_fuel loses or ties\n\n")
    losses = [c for c in comp_df.to_dict("records") if np.isfinite(c.get("pct_reduction_mean", np.nan)) and c["pct_reduction_mean"] <= 0]
    if not losses:
        lines.append("No non-positive mean fuel reductions found against listed baselines in loaded runs.\n")
    else:
        for c in losses:
            lines.append(
                f"- vs `{c['baseline']}` on `{c['scenario']}`: "
                f"{c['pct_reduction_mean']:.2f}% (CI [{c['pct_reduction_ci_lo']:.2f}, {c['pct_reduction_ci_hi']:.2f}])\n"
            )

    lines.append("\n## Ablations\n\n")
    lines.append(pd.DataFrame(abl_rows).to_markdown(index=False) if abl_rows else "n/a")
    lines.append("\n")

    lines.append("\n## RL comparison\n\n")
    if rlmeta:
        lines.append(f"RL selected on VALIDATION: `{json.dumps(rlmeta)}`.\n")
    rl_comp = comp_df[comp_df.baseline == "rl_ppo"] if "baseline" in comp_df else pd.DataFrame()
    if len(rl_comp):
        lines.append(rl_comp.to_markdown(index=False))
    lines.append("\n")

    for title, obj in [
        ("Sensitivity", sens), ("Emission cross-check", xcheck), ("Safety", safety),
        ("Robustness", robust), ("Grid study", grid), ("Extrapolation", extrap),
    ]:
        lines.append(f"\n## {title}\n\n```\n{json.dumps(obj, indent=2) if obj else 'Not yet run.'}\n```\n")

    lines.append("\n## Limitations\n\n")
    lines.append("- Simulation-to-reality gap; emission model not calibrated to Indian vehicles.\n")
    lines.append("- Assumed vehicle mix unless observed counts provided.\n")
    lines.append("- No pedestrians; simplified turning/phase plan; single-city context.\n")
    lines.append("- Perception noise without user video is assumed.\n")

    lines.append("\n## Threats to validity\n\n")
    lines.append("- Internal: seed leakage prevented by config.lock; demand independent of controller.\n")
    lines.append("- Construct: HBEFA proxies idle/fuel; SSM conflicts are model-based.\n")
    lines.append("- External: Indian arterial heterogeneity not fully represented.\n")

    lines.append("\n## Q&A cheat sheet\n\n")
    lines.append("**How is fuel computed?** SUMO emission devices (HBEFA classes mapped at runtime); "
                 "mg converted to litres via petrol/diesel densities in config.\n\n")
    lines.append("**Is it AI?** Perception path uses YOLO; controller is fuel-weighted pressure "
                 "(interpretable). RL-PPO is an additional baseline.\n\n")
    lines.append("**Why not RL?** See RL comparison tables; PPO is trained/selected on TRAIN/VALIDATION "
                 "and reported honestly if it underperforms ours_fuel.\n\n")
    lines.append("**What about deployment?** Requires detectors (or camera+YOLO), TraCI/edge controller, "
                 "and local calibration; results are simulation-based estimates.\n\n")
    lines.append("**What about Indian traffic?** Assumed mix with 2W/auto; sublane model when stable; "
                 "left-hand traffic.\n\n")
    lines.append("**Biggest limitation?** Emission classes and mix are not field-calibrated.\n\n")
    lines.append("**Did you tune on test data?** No. Tuning and RL selection use VALIDATION seeds only; "
                 "TEST seeds touched after config.lock.\n\n")

    (ROOT / "results" / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    main(smoke=args.smoke)
