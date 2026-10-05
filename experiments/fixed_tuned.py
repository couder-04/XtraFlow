"""Search fixed green splits on VALIDATION seeds only.

Greens run from min_green to 45 s in steps of 5. Cycle length is the sum of
the four greens plus yellow and all-red. The legacy plan stays on controller
`fixed`. This writes results/fixed_tuned.json and does not touch TEST seeds.
"""
from __future__ import annotations

import itertools
import os
from multiprocessing import get_context
from typing import Any, Dict, List

from sim.util import ROOT, SCENARIOS, load_config, save_json, seed_range


def _green_values(min_green: float) -> List[int]:
    start = max(10, int(min_green))
    # Snap up to the 5 s grid, then stay inside 10..45.
    if start % 5:
        start += 5 - (start % 5)
    return list(range(start, 46, 5))


def _candidates(min_green: float, smoke: bool) -> List[List[int]]:
    values = _green_values(min_green)
    if smoke:
        return [values[:1] * 4, [values[0], values[0], values[min(1, len(values) - 1)], values[0]]]
    # Coarse screen on the 5 s grid, then the caller refines ±5.
    coarse = values[::2] or values
    plans = [list(p) for p in itertools.product(coarse, repeat=4)]
    return plans


def _one_run(task):
    scenario, greens, seed, smoke = task
    from sim.run_sim import run_one
    row = run_one(
        scenario, "fixed_tuned", seed, smoke=smoke,
        params={"greens": list(greens)},
        run_id="ft_" + "_".join(str(int(g)) for g in greens),
    )
    return tuple(int(g) for g in greens), row


def _usable(row: Dict[str, Any], smoke: bool) -> bool:
    # A short smoke horizon often still has vehicles on the road. Those rows
    # are usable for a smoke screen. The VALIDATION search keeps only finished runs.
    if smoke:
        ok = row.get("status") != "error" and not row.get("gridlock_flag")
    else:
        ok = row.get("status") == "ok"
    return bool(ok and row.get("n_departed"))


def _score_plans(scenario: str, plans: List[List[int]], seeds: List[int], smoke: bool) -> List:
    tasks = [(scenario, list(g), s, smoke) for g in plans for s in seeds]
    grouped: Dict[tuple, List[float]] = {tuple(int(x) for x in g): [] for g in plans}
    workers = 1 if smoke else min(6, max(1, (os.cpu_count() or 2) - 1))
    if workers <= 1 or len(tasks) <= 1:
        results = [_one_run(t) for t in tasks]
    else:
        print(f"fixed_tuned {scenario}: {len(tasks)} runs, {workers} workers", flush=True)
        ctx = get_context("spawn")
        with ctx.Pool(workers) as pool:
            results = list(pool.imap_unordered(_one_run, tasks, chunksize=1))
    for key, row in results:
        if _usable(row, smoke):
            grouped[key].append(float(row["fuel_per_vehicle_L"]))
    scored = []
    for g in plans:
        key = tuple(int(x) for x in g)
        fuels = grouped[key]
        score = sum(fuels) / len(fuels) if fuels else float("inf")
        scored.append((score, list(g)))
    scored.sort(key=lambda item: (item[0], item[1]))
    return scored


def _refine(best: List[int], values: List[int]) -> List[List[int]]:
    neighborhood = {tuple(best)}
    for i in range(4):
        if best[i] not in values:
            continue
        ix = values.index(best[i])
        for j in (ix - 1, ix + 1):
            if 0 <= j < len(values):
                trial = list(best)
                trial[i] = values[j]
                neighborhood.add(tuple(trial))
    return [list(p) for p in neighborhood]


def main(smoke: bool = False) -> Dict[str, Any]:
    cfg = load_config()
    val = seed_range(cfg["seed_protocol"]["validation"])
    screen_seeds = val[:1] if smoke else val[:3]
    confirm_seeds = val[:1] if smoke else val
    scenarios = ["balanced"] if smoke else list(SCENARIOS)
    values = _green_values(float(cfg["signals"]["min_green_s"]))
    plans: Dict[str, Any] = {}
    for scenario in scenarios:
        cands = _candidates(float(cfg["signals"]["min_green_s"]), smoke=smoke)
        ranked = _score_plans(scenario, cands, screen_seeds, smoke)
        best = ranked[0][1]
        if not smoke:
            refined = _refine(best, values)
            ranked2 = _score_plans(scenario, refined, confirm_seeds, smoke)
            best = ranked2[0][1]
            best_score = ranked2[0][0]
        else:
            best_score = ranked[0][0]
        yellow = float(cfg["signals"]["yellow_s"])
        all_red = float(cfg["signals"]["all_red_s"])
        cycle = sum(best) + 4 * (yellow + all_red)
        plans[scenario] = {
            "greens": [int(g) for g in best],
            "cycle_s": cycle,
            "mean_fuel_per_vehicle_L": None if best_score == float("inf") else best_score,
            "selected_on": "VALIDATION",
            "screen_seeds": screen_seeds,
        }
        print(scenario, plans[scenario])
    out = {
        "selected_on": "VALIDATION seeds only",
        "green_grid_s": values,
        "min_green_s": cfg["signals"]["min_green_s"],
        "smoke": smoke,
        "plans": plans,
        "label": "Simulation-based estimate; assumed traffic mix",
    }
    save_json(ROOT / "results" / "fixed_tuned.json", out)
    return out


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    main(smoke=args.smoke)
