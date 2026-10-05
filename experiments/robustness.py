"""Robustness of XtraFlow to detection miss rates and empirical noise model."""
from __future__ import annotations

from sim.controllers import PerceptionNoise
from sim.run_sim import run_one
from sim.util import ROOT, load_config, load_json, save_json, seed_range


def main(smoke: bool = False) -> None:
    cfg = load_config()
    seeds = seed_range(cfg["seed_protocol"]["test"])[: 2 if smoke else 10]
    rates = cfg["robustness"]["detect_miss_rates"]
    scenario = "peak_unbalanced"
    rows = []

    # reference lines
    for ctrl in ["fixed", "actuated"]:
        for seed in seeds:
            row = run_one(scenario, ctrl, seed, smoke=smoke)
            rows.append({"kind": "reference", "controller": ctrl, "miss": 0.0, **{k: row[k] for k in
                        ["seed", "fuel_per_vehicle_L", "mean_waiting_s"]}})

    for miss in rates:
        noise = PerceptionNoise(detect_miss_rate=float(miss))
        for seed in seeds:
            row = run_one(scenario, "XtraFlow", seed, smoke=smoke, noise=noise)
            rows.append({"kind": "XtraFlow", "controller": "XtraFlow", "miss": miss,
                         "seed": seed, "fuel_per_vehicle_L": row["fuel_per_vehicle_L"],
                         "mean_waiting_s": row["mean_waiting_s"]})

    # empirical noise if present
    emp_path = ROOT / "perception" / "noise_model.json"
    if emp_path.exists():
        noise = PerceptionNoise.from_file(emp_path)
        for seed in seeds:
            row = run_one(scenario, "XtraFlow", seed, smoke=smoke, noise=noise)
            rows.append({"kind": "empirical_noise", "controller": "XtraFlow", "miss": noise.detect_miss_rate,
                         "seed": seed, "fuel_per_vehicle_L": row["fuel_per_vehicle_L"],
                         "mean_waiting_s": row["mean_waiting_s"]})

    out = {"scenario": scenario, "rows": rows, "label": "Simulation-based"}
    save_json(ROOT / "results" / "robustness.json", out)

    # figure
    import matplotlib.pyplot as plt
    import pandas as pd

    df = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(8, 4))
    ours = df[df.kind == "XtraFlow"].groupby("miss")["fuel_per_vehicle_L"].mean()
    ax.plot(ours.index, ours.values, marker="o", label="XtraFlow")
    for ctrl in ["fixed", "actuated"]:
        val = df[df.controller == ctrl]["fuel_per_vehicle_L"].mean()
        ax.axhline(val, linestyle="--", label=ctrl)
    ax.set_xlabel("detect_miss_rate")
    ax.set_ylabel("fuel_per_vehicle_L")
    ax.set_title("Robustness to detection errors")
    ax.legend()
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "figures" / "vii_robustness.png", dpi=200)
    plt.close(fig)
    print("robustness done")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    main(smoke=args.smoke)
