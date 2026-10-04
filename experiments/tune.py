"""Grid-search ours_fuel hyperparameters on VALIDATION seeds only."""
from __future__ import annotations

import itertools
from typing import Any, Dict, List

from sim.run_sim import run_one
from sim.util import ROOT, load_config, save_json, seed_range


def main(smoke: bool = False) -> Dict[str, Any]:
    cfg = load_config()
    val_seeds = seed_range(cfg["seed_protocol"]["validation"])
    if smoke:
        val_seeds = val_seeds[:1]
    grid = cfg["tune"]
    keys = list(grid.keys())
    combos = list(itertools.product(*[grid[k] for k in keys]))
    # Limit combos for smoke
    if smoke:
        combos = combos[:2]

    best = None
    best_score = float("inf")
    rows = []
    scenario = "peak_unbalanced"  # tune on challenging scenario
    for combo in combos:
        params = dict(zip(keys, combo))
        fuels = []
        for seed in val_seeds:
            # temporarily inject params via tuned file
            save_json(ROOT / "results" / "tuned_params.json", params)
            row = run_one(scenario, "ours_fuel", seed, cfg=cfg, smoke=smoke)
            fuels.append(row["fuel_per_vehicle_L"])
            rows.append({**params, "seed": seed, "fuel_per_vehicle_L": row["fuel_per_vehicle_L"]})
        score = sum(fuels) / len(fuels)
        if score < best_score:
            best_score = score
            best = dict(params)

    assert best is not None
    best["selected_on"] = "VALIDATION seeds only"
    best["scenario"] = scenario
    best["mean_fuel_per_vehicle_L"] = best_score
    best["smoke"] = smoke
    save_json(ROOT / "results" / "tuned_params.json", best)
    save_json(ROOT / "results" / "tune_grid_results.json", {"rows": rows, "best": best})
    print(f"Best params: {best}")
    return best


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    main(smoke=args.smoke)
