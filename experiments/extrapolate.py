"""Monte-Carlo propagation of annual savings from MEASURED per-vehicle saving + CI."""
from __future__ import annotations

import json

import numpy as np

from sim.util import ROOT, load_config, load_json, save_json


def triangular(rng, lo, base, hi, n):
    return rng.triangular(lo, base, hi, size=n)


def main() -> None:
    cfg = load_config()
    headlines = load_json(ROOT / "results" / "headlines.json")
    # Use peak_unbalanced or mean across scenarios for per-vehicle relative saving
    # Convert % reduction to absolute L/veh using summary means
    import pandas as pd

    raw = ROOT / "results" / "raw_runs.csv"
    if not raw.exists():
        raw = ROOT / "results" / "raw_runs_smoke.csv"
    df = pd.read_csv(raw)
    # measured saving: mean (fixed - ours) fuel_per_vehicle on peak_unbalanced if present
    sc = "peak_unbalanced" if "peak_unbalanced" in set(df.scenario) else df.scenario.iloc[0]
    fixed = df[(df.scenario == sc) & (df.controller == "fixed")]["fuel_per_vehicle_L"]
    ours = df[(df.scenario == sc) & (df.controller == "XtraFlow")]["fuel_per_vehicle_L"]
    # paired
    m = pd.DataFrame({"seed": df[(df.scenario == sc) & (df.controller == "fixed")]["seed"].values,
                      "fixed": fixed.values})
    o = pd.DataFrame({"seed": df[(df.scenario == sc) & (df.controller == "XtraFlow")]["seed"].values,
                      "ours": ours.values})
    merged = m.merge(o, on="seed")
    saving = (merged["fixed"] - merged["ours"]).to_numpy()
    # bootstrap CI of mean saving
    rng = np.random.default_rng(0)
    boots = []
    for _ in range(10000):
        sample = rng.choice(saving, size=len(saving), replace=True)
        boots.append(sample.mean())
    mean_save = float(np.mean(saving))
    lo_save, hi_save = float(np.percentile(boots, 5)), float(np.percentile(boots, 95))

    n = int(cfg["extrapolation"]["n_monte_carlo"])
    ex = cfg["extrapolation"]
    price = cfg["fuel"]["price_inr_per_L"]
    co2 = cfg["fuel"]["co2_kg_per_L"]
    # sample saving from normal approx within bootstrap
    save_draw = rng.normal(mean_save, max((hi_save - lo_save) / 3.29, 1e-9), size=n)
    vph = triangular(rng, ex["vehicles_per_peak_hour"]["low"], ex["vehicles_per_peak_hour"]["base"],
                     ex["vehicles_per_peak_hour"]["high"], n)
    phd = triangular(rng, ex["peak_hours_per_day"]["low"], ex["peak_hours_per_day"]["base"],
                     ex["peak_hours_per_day"]["high"], n)
    dpy = triangular(rng, ex["days_per_year"]["low"], ex["days_per_year"]["base"],
                     ex["days_per_year"]["high"], n)
    nint = triangular(rng, ex["n_intersections"]["low"], ex["n_intersections"]["base"],
                      ex["n_intersections"]["high"], n)
    price_d = triangular(rng, price["low"], price["base"], price["high"], n)
    # blend CO2 factor petrol/diesel by mix approx 0.7 petrol
    co2_f = 0.7 * co2["petrol"] + 0.3 * co2["diesel"]

    annual_L = save_draw * vph * phd * dpy * nint
    annual_INR = annual_L * price_d
    annual_tCO2 = annual_L * co2_f / 1000.0

    def summ(arr):
        return {
            "median": float(np.median(arr)),
            "p05": float(np.percentile(arr, 5)),
            "p95": float(np.percentile(arr, 95)),
        }

    out = {
        "label": "Simulation-based estimate; not a real-world deployment result",
        "scenario_basis": sc,
        "measured_saving_L_per_veh": {"mean": mean_save, "p05": lo_save, "p95": hi_save},
        "annual_litres": summ(annual_L),
        "annual_INR_PLACEHOLDER_price": summ(annual_INR),
        "annual_tonnes_CO2": summ(annual_tCO2),
        "fuel_price_note": "INR/L is a user-editable PLACEHOLDER in config.yaml",
        "headlines_ref": headlines,
    }
    save_json(ROOT / "results" / "extrapolation.json", out)

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(annual_L, bins=50, color="C0", alpha=0.8)
    ax.axvline(out["annual_litres"]["median"], color="k", label="median")
    ax.set_xlabel("Annual litres saved (simulation-based)")
    ax.set_title("Extrapolation distribution")
    ax.legend()
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "figures" / "xi_extrapolation.png", dpi=200)
    plt.close(fig)
    print(json.dumps({k: out[k] for k in ["annual_litres", "annual_tonnes_CO2"]}, indent=2))


if __name__ == "__main__":
    main()
