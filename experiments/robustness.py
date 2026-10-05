"""Robustness of XtraFlow to detection miss rates. TEST seeds, after the lock.

Miss levels come from config. Reference lines are fixed_tuned, actuated, and maxpressure.
Output files differ by run_id so a 10% miss run does not overwrite a 0% run.
"""
from __future__ import annotations

from sim.controllers import PerceptionNoise
from sim.util import ROOT, load_config, save_json, seed_range


def main(smoke: bool = False) -> None:
    cfg = load_config()
    seeds = seed_range(cfg["seed_protocol"]["test"])
    if smoke:
        seeds = seeds[:1]
    rates = cfg["robustness"]["detect_miss_rates"]
    scenario = "peak_unbalanced"
    rows = []
    references = ["fixed_tuned", "actuated", "maxpressure"]

    from sim.run_sim import run_one

    for ctrl in references:
        for seed in seeds:
            row = run_one(scenario, ctrl, seed, smoke=smoke, run_id="miss0")
            rows.append({
                "kind": "reference",
                "controller": ctrl,
                "miss": 0.0,
                "seed": seed,
                "fuel_per_vehicle_L": row["fuel_per_vehicle_L"],
                "mean_waiting_s": row["mean_waiting_s"],
                "status": row.get("status"),
                "n_unfinished": row.get("n_unfinished"),
            })

    for miss in rates:
        noise = PerceptionNoise(detect_miss_rate=float(miss), mean_burst_s=3.0)
        for seed in seeds:
            row = run_one(
                scenario, "XtraFlow", seed, smoke=smoke, noise=noise,
                run_id=f"miss{miss}",
            )
            rows.append({
                "kind": "XtraFlow",
                "controller": "XtraFlow",
                "miss": miss,
                "seed": seed,
                "fuel_per_vehicle_L": row["fuel_per_vehicle_L"],
                "mean_waiting_s": row["mean_waiting_s"],
                "status": row.get("status"),
                "n_unfinished": row.get("n_unfinished"),
            })

    emp_path = ROOT / "perception" / "noise_model.json"
    if emp_path.exists():
        noise = PerceptionNoise.from_file(emp_path)
        for seed in seeds:
            row = run_one(
                scenario, "XtraFlow", seed, smoke=smoke, noise=noise,
                run_id="miss_empirical",
            )
            rows.append({
                "kind": "empirical_noise" if noise else "noise",
                "controller": "XtraFlow",
                "miss": noise.detect_miss_rate,
                "source": "empirical" if _source(emp_path) == "empirical" else "assumed",
                "seed": seed,
                "fuel_per_vehicle_L": row["fuel_per_vehicle_L"],
                "mean_waiting_s": row["mean_waiting_s"],
                "status": row.get("status"),
            })

    out = {
        "scenario": scenario,
        "seeds": "TEST",
        "rows": rows,
        "label": "Simulation-based estimate; assumed traffic mix",
    }
    save_json(ROOT / "results" / "robustness.json", out)

    import matplotlib.pyplot as plt
    import pandas as pd

    df = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(8, 4))
    ours = df[df.kind == "XtraFlow"].groupby("miss")["fuel_per_vehicle_L"].mean()
    if len(ours):
        ax.plot(ours.index, ours.values, marker="o", label="XtraFlow")
    for ctrl in references:
        sub = df[df.controller == ctrl]["fuel_per_vehicle_L"]
        if len(sub):
            ax.axhline(sub.mean(), linestyle="--", label=ctrl)
    ax.set_xlabel("detect_miss_rate")
    ax.set_ylabel("fuel per departed vehicle (L)")
    ax.set_title("Robustness to detection errors")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "figures" / "vii_robustness.png", dpi=200)
    plt.close(fig)
    print("robustness done")


def _source(path) -> str:
    from sim.util import load_json
    try:
        return str(load_json(path).get("source", ""))
    except Exception:
        return ""


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    main(smoke=args.smoke)
