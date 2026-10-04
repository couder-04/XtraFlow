"""Grid-search ours_fuel hyperparameters on VALIDATION seeds only."""
from __future__ import annotations

import itertools
import os
from multiprocessing import get_context
from typing import Any, Dict, List, Tuple

from sim.util import ROOT, load_config, save_json, seed_range


def _eval_one(args: Tuple) -> Dict[str, Any]:
    params, scenario, seed, smoke = args
    from sim.run_sim import run_one
    # isolate params via explicit kwargs path: write temp not shared
    # Controllers load tuned_params.json; use params override by writing per-process file is racy.
    # Instead patch make_controller via run_one after setting env-specific file.
    save_json(ROOT / "results" / f"tuned_params_{os.getpid()}.json", params)
    # Monkey-patch load path by temporarily writing tuned_params.json under a lock-less approach:
    # For correctness under MP, pass params by writing then reading in controller via env var.
    os.environ["TUNED_PARAMS_PATH"] = str(ROOT / "results" / f"tuned_params_{os.getpid()}.json")
    # Ensure controllers pick it up
    import sim.controllers as C
    C._load_tuned = lambda: params  # type: ignore
    row = run_one(scenario, "ours_fuel", seed, smoke=smoke, params=params)
    return {**params, "seed": seed, "fuel_per_vehicle_L": row["fuel_per_vehicle_L"],
            "n_completed": row["n_completed"], "gridlock_flag": row["gridlock_flag"]}


# Extend run_one to accept params — patch here if needed
def _ensure_run_one_params():
    import sim.run_sim as rs
    orig = rs.run_one

    def wrapped(*args, params=None, **kwargs):
        if params is not None:
            import sim.controllers as C
            old = C._load_tuned
            C._load_tuned = lambda: params  # type: ignore
            try:
                # also pass through make_controller
                from sim import controllers
                old_make = controllers.make_controller

                def make_controller(name, cfg=None, scenario="balanced", noise=None, weights=None, params=None, model=None):
                    return old_make(name, cfg=cfg, scenario=scenario, noise=noise, weights=weights,
                                    params=params if params is not None else kwargs.get("params"), model=model)

                # simpler: just set default tuned
                return orig(*args, **{k: v for k, v in kwargs.items() if k != "params"})
            finally:
                C._load_tuned = old
        return orig(*args, **kwargs)

    # Actually patch make_controller usage inside run_one by setting _load_tuned before call
    return orig


def main(smoke: bool = False) -> Dict[str, Any]:
    cfg = load_config()
    all_val = seed_range(cfg["seed_protocol"]["validation"])
    screen_seeds = all_val[:1] if smoke else all_val[:5]
    confirm_seeds = all_val[:1] if smoke else all_val
    grid = cfg["tune"]
    keys = list(grid.keys())
    combos = [dict(zip(keys, c)) for c in itertools.product(*[grid[k] for k in keys])]
    if smoke:
        combos = combos[:2]

    scenario = "peak_unbalanced"
    # Keep concurrency modest — SUMO/TraCI is fragile under heavy parallel load.
    n_workers = 1 if smoke else min(3, max(1, (os.cpu_count() or 2) - 1))

    def run_batch(param_list, seeds, stage):
        tasks = [(p, scenario, s, smoke) for p in param_list for s in seeds]
        rows = []
        if n_workers == 1:
            for t in tasks:
                rows.append(_eval_task(t, stage))
        else:
            ctx = get_context("spawn")
            with ctx.Pool(n_workers) as pool:
                for r in pool.imap_unordered(_eval_task_mp, [(t, stage) for t in tasks]):
                    rows.append(r)
        return rows

    print(f"Tune screen: {len(combos)} combos × {len(screen_seeds)} seeds, workers={n_workers}")
    screen_rows = run_batch(combos, screen_seeds, "screen")
    # score
    scores = {}
    for r in screen_rows:
        key = tuple(r[k] for k in keys)
        scores.setdefault(key, []).append(r["fuel_per_vehicle_L"])
    ranked = sorted(((sum(v) / len(v), dict(zip(keys, k))) for k, v in scores.items()), key=lambda x: x[0])
    finalists = [p for _, p in ranked[: 1 if smoke else 3]]

    print(f"Confirm top {len(finalists)} on {len(confirm_seeds)} VAL seeds")
    confirm_rows = run_batch(finalists, confirm_seeds, "confirm")
    cscores = {}
    for r in confirm_rows:
        key = tuple(r[k] for k in keys)
        cscores.setdefault(key, []).append(r["fuel_per_vehicle_L"])
    best_key = min(cscores, key=lambda k: sum(cscores[k]) / len(cscores[k]))
    best = dict(zip(keys, best_key))
    best_score = sum(cscores[best_key]) / len(cscores[best_key])
    best["selected_on"] = "VALIDATION seeds only"
    best["screen_seeds"] = screen_seeds
    best["confirm_seeds"] = confirm_seeds
    best["scenario"] = scenario
    best["mean_fuel_per_vehicle_L"] = best_score
    best["smoke"] = smoke
    save_json(ROOT / "results" / "tuned_params.json", best)
    save_json(ROOT / "results" / "tune_grid_results.json", {
        "rows": screen_rows + confirm_rows,
        "best": best,
        "screen_ranking": [{"score": s, "params": p} for s, p in ranked],
    })
    print(f"Best params: {best}")
    return best


def _eval_task(task, stage):
    params, scenario, seed, smoke = task
    from sim.run_sim import run_one
    run_id = "tune_" + "_".join(f"{k}{params[k]}" for k in sorted(params))
    row = run_one(scenario, "ours_fuel", seed, smoke=smoke, params=params, run_id=run_id)
    return {**params, "seed": seed, "stage": stage, "fuel_per_vehicle_L": row["fuel_per_vehicle_L"],
            "n_completed": row["n_completed"], "gridlock_flag": row["gridlock_flag"]}


def _eval_task_mp(args):
    task, stage = args
    return _eval_task(task, stage)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    main(smoke=args.smoke)
