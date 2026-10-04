"""Full TEST sweep / smoke sweep over controllers × scenarios × seeds."""
from __future__ import annotations

import argparse
import csv
import multiprocessing as mp
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tqdm import tqdm

from sim.run_sim import RAW_FIELDS, append_raw_row, run_one
from sim.util import (
    CONTROLLER_NAMES,
    ROOT,
    SCENARIOS,
    assert_config_locked,
    ensure_dirs,
    freeze_config,
    load_config,
    seed_range,
)


def _existing_keys(path: Path) -> set:
    if not path.exists():
        return set()
    keys = set()
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            keys.add((row["scenario"], row["controller"], str(row["seed"]), row.get("emission_model", "primary")))
    return keys


def _worker(task: Tuple) -> Optional[Dict[str, Any]]:
    scenario, controller, seed, smoke, emission_model, save_ts = task
    try:
        # Load RL model if needed
        model = None
        if controller == "rl_ppo":
            from stable_baselines3 import PPO

            best = ROOT / "results" / "rl" / "ppo_best.zip"
            if best.exists():
                model = PPO.load(str(best))
        row = run_one(
            scenario,
            controller,
            seed,
            smoke=smoke,
            emission_model=emission_model,
            save_timeseries=save_ts,
            model=model,
        )
        return row
    except Exception as e:  # noqa: BLE001
        return {
            "scenario": scenario,
            "controller": controller,
            "seed": seed,
            "emission_model": emission_model,
            "n_departed": 0,
            "n_completed": 0,
            "total_fuel_L": float("nan"),
            "fuel_per_vehicle_L": float("nan"),
            "fuel_per_person_L": float("nan"),
            "total_CO2_kg": float("nan"),
            "mean_waiting_s": float("nan"),
            "mean_timeLoss_s": float("nan"),
            "person_delay_s": float("nan"),
            "mean_travel_time_s": float("nan"),
            "stops_per_vehicle": float("nan"),
            "idle_vehicle_seconds": float("nan"),
            "mean_queue_veh": float("nan"),
            "max_queue_veh": float("nan"),
            "fuel_L_by_type": "{}",
            "ssm_conflicts": -1,
            "gridlock_flag": 1,
            "wall_time_s": -1,
            "error": str(e),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--controllers", nargs="*", default=None)
    parser.add_argument("--scenarios", nargs="*", default=None)
    parser.add_argument("--workers", type=int, default=None)
    args = parser.parse_args()

    cfg = load_config()
    ensure_dirs()

    # Ensure network exists
    net = ROOT / "results" / "networks" / "intersection.net.xml"
    if not net.exists():
        from sim.build_network import build
        build()
        from sim.build_grid import build as build_grid
        build_grid()

    if args.smoke:
        controllers = args.controllers or CONTROLLER_NAMES
        scenarios = args.scenarios or ["balanced"]
        seeds = [1]
        out_csv = ROOT / "results" / "raw_runs_smoke.csv"
        # smoke may run before freeze
    else:
        freeze_config()
        assert_config_locked()
        controllers = args.controllers or CONTROLLER_NAMES
        scenarios = args.scenarios or SCENARIOS
        seeds = seed_range(cfg["seed_protocol"]["test"])
        out_csv = ROOT / "results" / "raw_runs.csv"

    existing = _existing_keys(out_csv)
    tasks = []
    for sc in scenarios:
        for ctrl in controllers:
            for seed in seeds:
                key = (sc, ctrl, str(seed), "primary")
                if key in existing:
                    continue
                save_ts = (not args.smoke) and seed == 1
                tasks.append((sc, ctrl, seed, args.smoke, "primary", save_ts))

    n_workers = args.workers or max(1, (os.cpu_count() or 2) - 1)
    # TraCI/SUMO often unstable with high parallelism; cap
    n_workers = min(n_workers, 4 if args.smoke else 6)

    print(f"Sweep tasks={len(tasks)} workers={n_workers} smoke={args.smoke}")
    if not tasks:
        print("Nothing to do (resumable: all keys present).")
        return

    # Use spawn for safety with SUMO
    ctx = mp.get_context("spawn")
    with ctx.Pool(n_workers) as pool:
        for row in tqdm(pool.imap_unordered(_worker, tasks), total=len(tasks)):
            if row is None:
                continue
            # strip error field for CSV
            row = {k: row.get(k, "") for k in RAW_FIELDS}
            append_raw_row(row, out_csv)

    print(f"Wrote/updated {out_csv}")


if __name__ == "__main__":
    main()
