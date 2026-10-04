"""Demand multiplier and vehicle-mix Latin-hypercube sensitivity."""
from __future__ import annotations

import numpy as np

from sim.run_sim import run_one
from sim.util import ROOT, load_config, save_json


def lhs_mixes(n: int, seed: int = 0):
    """Latin hypercube over mix ranges (assumed)."""
    rng = np.random.default_rng(seed)
    # ranges assumed
    ranges = {
        "two_wheeler": (0.25, 0.55),
        "car": (0.15, 0.40),
        "auto_rickshaw": (0.05, 0.20),
        "bus": (0.02, 0.10),
        "truck": (0.05, 0.25),
    }
    keys = list(ranges.keys())
    u = (rng.random((n, len(keys))) + np.arange(n)[:, None]) / n
    for j in range(len(keys)):
        rng.shuffle(u[:, j])
    mixes = []
    for i in range(n):
        raw = {}
        for j, k in enumerate(keys):
            lo, hi = ranges[k]
            raw[k] = lo + u[i, j] * (hi - lo)
        s = sum(raw.values())
        mixes.append({k: v / s for k, v in raw.items()})
    return mixes, ranges


def main(smoke: bool = False) -> None:
    cfg = load_config()
    mults = cfg["sensitivity"]["demand_multipliers"]
    n_mix = 3 if smoke else int(cfg["sensitivity"]["mix_lhs_samples"])
    seeds = [1, 2] if smoke else [1, 2, 3, 4, 5]
    scenario = "balanced"
    rows = []

    for m in mults:
        for seed in seeds:
            for ctrl in ["fixed", "ours_fuel"]:
                row = run_one(scenario, ctrl, seed, smoke=smoke, demand_mult=float(m))
                rows.append({
                    "kind": "demand_mult", "mult": m, "controller": ctrl, "seed": seed,
                    "fuel_per_vehicle_L": row["fuel_per_vehicle_L"],
                    "mean_waiting_s": row["mean_waiting_s"],
                })

    mixes, ranges = lhs_mixes(n_mix)
    for i, mix in enumerate(mixes):
        for ctrl in ["fixed", "ours_fuel"]:
            row = run_one(scenario, ctrl, seed=1 + i, smoke=smoke, mix_override=mix)
            rows.append({
                "kind": "mix_lhs", "mix_id": i, "mix": mix, "controller": ctrl,
                "fuel_per_vehicle_L": row["fuel_per_vehicle_L"],
            })

    # saturation proxy vs gain
    gains = []
    for m in mults:
        f = [r["fuel_per_vehicle_L"] for r in rows if r.get("kind") == "demand_mult" and r["mult"] == m and r["controller"] == "fixed"]
        o = [r["fuel_per_vehicle_L"] for r in rows if r.get("kind") == "demand_mult" and r["mult"] == m and r["controller"] == "ours_fuel"]
        if f and o:
            pct = (np.mean(f) - np.mean(o)) / np.mean(f) * 100
            gains.append({"demand_mult": m, "dos_proxy": m, "pct_fuel_reduction": float(pct)})

    out = {"rows": rows, "gains": gains, "mix_ranges_assumed": ranges, "label": "assumed"}
    save_json(ROOT / "results" / "sensitivity.json", out)

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4))
    if gains:
        ax.plot([g["dos_proxy"] for g in gains], [g["pct_fuel_reduction"] for g in gains], marker="o")
    ax.set_xlabel("Demand multiplier (DoS proxy)")
    ax.set_ylabel("% fuel reduction ours vs fixed")
    ax.set_title("Gain vs degree of saturation (proxy)")
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "figures" / "vi_gain_vs_saturation.png", dpi=200)
    plt.close(fig)
    print("sensitivity done")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    main(smoke=args.smoke)
