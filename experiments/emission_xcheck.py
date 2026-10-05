"""Rerun key comparisons with alternate emission model."""
from __future__ import annotations

import numpy as np

from sim.run_sim import run_one
from sim.util import ROOT, load_config, load_json, save_json


def main(smoke: bool = False) -> None:
    cfg = load_config()
    seeds = [1, 2] if smoke else list(range(1, 11))
    scenario = "peak_unbalanced"
    rows = []
    for emis in ["primary", "alternate"]:
        for ctrl in ["fixed", "XtraFlow"]:
            for seed in seeds:
                row = run_one(scenario, ctrl, seed, smoke=smoke, emission_model=emis)
                rows.append({
                    "emission_model": emis,
                    "controller": ctrl,
                    "seed": seed,
                    "fuel_per_vehicle_L": row["fuel_per_vehicle_L"],
                    "total_CO2_kg": row["total_CO2_kg"],
                })

    def pct(emis):
        f = [r["fuel_per_vehicle_L"] for r in rows if r["emission_model"] == emis and r["controller"] == "fixed"]
        o = [r["fuel_per_vehicle_L"] for r in rows if r["emission_model"] == emis and r["controller"] == "XtraFlow"]
        paired = []
        # pair by seed order
        fmap = {r["seed"]: r["fuel_per_vehicle_L"] for r in rows if r["emission_model"] == emis and r["controller"] == "fixed"}
        omap = {r["seed"]: r["fuel_per_vehicle_L"] for r in rows if r["emission_model"] == emis and r["controller"] == "XtraFlow"}
        for s in fmap:
            if s in omap and fmap[s]:
                paired.append((fmap[s] - omap[s]) / fmap[s] * 100)
        return float(np.mean(paired)) if paired else float("nan")

    primary_pct = pct("primary")
    alt_pct = pct("alternate")
    emap = load_json(ROOT / "results" / "emission_class_map.json") if (ROOT / "results" / "emission_class_map.json").exists() else {}
    verdict = "unchanged_direction" if (np.isfinite(primary_pct) and np.isfinite(alt_pct) and (primary_pct * alt_pct > 0)) else "changed_or_inconclusive"
    out = {
        "rows": rows,
        "pct_reduction_primary": primary_pct,
        "pct_reduction_alternate": alt_pct,
        "verdict": verdict,
        "emission_map": emap,
        "note": "Alternate uses HBEFA3 fallback set if PHEMlight unavailable.",
    }
    save_json(ROOT / "results" / "emission_xcheck.json", out)

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(["primary", "alternate"], [primary_pct, alt_pct])
    ax.set_ylabel("% fuel reduction XtraFlow vs fixed")
    ax.set_title(f"Emission cross-check ({verdict})")
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "figures" / "ix_emission_xcheck.png", dpi=200)
    plt.close(fig)
    print(out["verdict"], primary_pct, alt_pct)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    main(smoke=args.smoke)
