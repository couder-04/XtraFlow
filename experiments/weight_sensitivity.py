"""Sensitivity of XtraFlow fuel to the class fuel weights.

Scales the calibrated w_type vector and a few ablations on a small seed set
without retuning. Writes results/weight_sensitivity.json.
"""
from __future__ import annotations

import argparse
import os
from typing import Any, Dict, List, Tuple

import numpy as np

from sim.util import ROOT, load_config, load_json, save_json


SCALES = [0.5, 0.75, 1.0, 1.25, 1.5]
ABLATIONS = ("calibrated", "equal", "no_2w_discount", "car_like_auto")


def _base_weights() -> Dict[str, float]:
    data = load_json(ROOT / "results" / "weights.json")
    return {k: float(v) for k, v in data["w_type"].items()}


def _variant(name: str, scale: float, base: Dict[str, float]) -> Dict[str, float]:
    if name == "equal":
        w = {k: 1.0 for k in base}
    elif name == "no_2w_discount":
        w = dict(base)
        w["two_wheeler"] = float(base.get("car", 1.0))
    elif name == "car_like_auto":
        # Documents the passenger-car emission proxy: auto already equals car.
        w = dict(base)
        w["auto_rickshaw"] = float(base.get("car", 1.0))
    else:
        w = {k: float(v) * float(scale) for k, v in base.items()}
        ref = float(w.get("car", 1.0)) or 1.0
        w = {k: float(v) / ref for k, v in w.items()}
    return w


def _run_with_weights(scenario, seed, smoke, weights, variant, scale) -> Dict[str, Any]:
    import sim.run_sim as run_mod

    orig = run_mod.make_controller

    def _make(*args, **kwargs):
        kwargs = dict(kwargs)
        kwargs["weights"] = weights
        return orig(*args, **kwargs)

    run_mod.make_controller = _make  # type: ignore[assignment]
    try:
        row = run_mod.run_one(
            scenario,
            "XtraFlow",
            seed=int(seed),
            smoke=smoke,
            run_id=f"wsens_{variant}_s{float(scale):g}",
        )
    finally:
        run_mod.make_controller = orig  # type: ignore[assignment]
    return {
        "variant": variant,
        "scale": float(scale),
        "scenario": scenario,
        "seed": int(seed),
        "weights": weights,
        "fuel_per_vehicle_L": row["fuel_per_vehicle_L"],
        "mean_waiting_s": row["mean_waiting_s"],
        "n_completed": row["n_completed"],
        "status": row["status"],
    }


def _task(task: Tuple[Any, ...]) -> Dict[str, Any]:
    variant, scale, scenario, seed, smoke = task
    weights = _variant(variant, scale, _base_weights())
    return _run_with_weights(scenario, seed, smoke, weights, variant, scale)


def main(smoke: bool = False, max_seeds: int | None = None) -> None:
    from multiprocessing import get_context

    base = _base_weights()
    scenarios = ["low_demand"] if smoke else ["balanced", "low_demand"]
    seeds = [1] if smoke else [1, 2, 3]
    if max_seeds is not None:
        seeds = seeds[: int(max_seeds)]

    tasks: List[Tuple[Any, ...]] = []
    for variant in ABLATIONS:
        scales = SCALES if variant == "calibrated" else [1.0]
        for scale in scales:
            for sc in scenarios:
                for seed in seeds:
                    tasks.append((variant, scale, sc, seed, smoke))

    workers = 1 if smoke else min(6, max(1, (os.cpu_count() or 2) - 1))
    print(f"weight_sensitivity tasks={len(tasks)} workers={workers}", flush=True)
    if workers <= 1 or len(tasks) <= 1:
        rows = [_task(t) for t in tasks]
    else:
        ctx = get_context("spawn")
        with ctx.Pool(workers) as pool:
            rows = list(pool.imap_unordered(_task, tasks, chunksize=1))

    summary = []
    for variant in ABLATIONS:
        scales = SCALES if variant == "calibrated" else [1.0]
        for scale in scales:
            for sc in scenarios:
                vals = [
                    r["fuel_per_vehicle_L"] for r in rows
                    if r["variant"] == variant and abs(r["scale"] - float(scale)) < 1e-12
                    and r["scenario"] == sc and r["status"] == "ok"
                ]
                if not vals:
                    continue
                summary.append({
                    "variant": variant,
                    "scale": float(scale),
                    "scenario": sc,
                    "n": len(vals),
                    "fuel_per_vehicle_L_mean": float(np.mean(vals)),
                    "fuel_per_vehicle_L_std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
                })

    out = {
        "label": "assumed weight sensitivity",
        "base_weights": base,
        "note": (
            "auto_rickshaw weight equals car under the passenger-car emission proxy; "
            "two_wheeler uses LDV_G_EU4 when that class loads. This study scales the "
            "calibrated relative vector and ablations; it does not retune the controller."
        ),
        "rows": rows,
        "summary": summary,
    }
    dest = ROOT / "results" / "weight_sensitivity.json"
    save_json(dest, out)
    print(f"wrote {dest} rows={len(rows)} summary={len(summary)}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--max-seeds", type=int, default=None)
    args = p.parse_args()
    main(smoke=args.smoke, max_seeds=args.max_seeds)
