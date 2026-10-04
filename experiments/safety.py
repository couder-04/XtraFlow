"""Compare SSM conflict counts across controllers."""
from __future__ import annotations

import pandas as pd

from sim.util import ROOT, save_json


def main(smoke: bool = False) -> None:
    path = ROOT / "results" / ("raw_runs_smoke.csv" if smoke else "raw_runs.csv")
    if not path.exists():
        # run a minimal set
        from sim.run_sim import run_one
        rows = []
        for ctrl in ["fixed", "ours_fuel", "actuated", "maxpressure"]:
            rows.append(run_one("balanced", ctrl, 1, smoke=True))
        df = pd.DataFrame(rows)
    else:
        df = pd.read_csv(path)

    g = df.groupby("controller")["ssm_conflicts"].agg(["mean", "std", "count"]).reset_index()
    ours = g[g.controller == "ours_fuel"]["mean"].values
    fixed = g[g.controller == "fixed"]["mean"].values
    if len(ours) and len(fixed):
        delta = float(ours[0] - fixed[0])
        verdict = "no_increase" if delta <= 0 else "increase_observed"
    else:
        delta = None
        verdict = "insufficient_data"
    out = {
        "by_controller": g.to_dict(orient="records"),
        "ours_minus_fixed_mean_conflicts": delta,
        "verdict": verdict,
        "note": "SSM TTC<1.5s counts from SUMO device; model-based.",
    }
    save_json(ROOT / "results" / "safety.json", out)
    print(out)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    main(smoke=args.smoke)
