"""Train PPO on TRAIN seeds across all four scenarios. Select on VALIDATION.

Non-smoke training runs at least config rl.total_timesteps. Checkpoint choice
uses full-horizon VALIDATION runs on every scenario. TEST seeds are not used.
"""
from __future__ import annotations

import hashlib

import numpy as np

from sim.rl_env import SumoTrafficEnv
from sim.run_sim import run_one
from sim.util import ROOT, SCENARIOS, ensure_dirs, load_config, save_json, seed_range


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(smoke: bool = False) -> None:
    cfg = load_config()
    ensure_dirs()
    from stable_baselines3 import PPO

    train_seeds = seed_range(cfg["seed_protocol"]["train"])
    val_seeds = seed_range(cfg["seed_protocol"]["validation"])
    scenarios = list(SCENARIOS)
    budget = int(cfg["rl"]["total_timesteps"])
    if smoke:
        train_seeds = train_seeds[:2]
        val_seeds = val_seeds[:1]
        scenarios = ["balanced"]
        budget = 256
    horizon = 60 if smoke else int(cfg["simulation"]["demand_horizon_s"])

    out_dir = ROOT / "results" / "rl"
    out_dir.mkdir(parents=True, exist_ok=True)
    curves = []

    class MultiScenarioEnv(SumoTrafficEnv):
        def __init__(self):
            super().__init__(scenario=scenarios[0], seed=train_seeds[0], smoke=smoke, cfg=cfg)
            self.horizon = horizon
            self.timeout = horizon + (30 if smoke else 60)
            self._i = 0
            self._pairs = [(sc, s) for sc in scenarios for s in train_seeds]

        def reset(self, *, seed=None, options=None):
            sc, sd = self._pairs[self._i % len(self._pairs)]
            self._i += 1
            self.scenario = sc
            self._seed = sd
            self.horizon = horizon
            self.timeout = horizon + (30 if smoke else 60)
            return super().reset(seed=sd, options=options)

    env = MultiScenarioEnv()
    n_steps = 128 if smoke else int(cfg["rl"]["n_steps"])
    batch = min(int(cfg["rl"]["batch_size"]), n_steps)
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=float(cfg["rl"]["learning_rate"]),
        n_steps=n_steps,
        batch_size=batch,
        gamma=float(cfg["rl"]["gamma"]),
        verbose=1,
        seed=42,
    )

    # Train the full budget. Do not stop early below total_timesteps.
    chunk = max(n_steps, budget // 4)
    done_steps = 0
    ckpts = []
    while done_steps < budget:
        step_now = min(chunk, budget - done_steps)
        model.learn(total_timesteps=step_now, reset_num_timesteps=False)
        done_steps += step_now
        path = out_dir / f"ppo_step{done_steps}.zip"
        model.save(str(path))
        ckpts.append(path)
        curves.append({"timesteps": done_steps, "checkpoint": path.name})
        print(f"timesteps={done_steps}/{budget}")

    env.close()

    def val_fuel(ppo) -> float:
        fuels = []
        for scenario in scenarios:
            for sd in val_seeds:
                row = run_one(
                    scenario, "rl_ppo", sd, cfg=cfg,
                    smoke=smoke,
                    horizon_s=horizon if smoke else None,
                    model=ppo,
                    run_id="rlval",
                )
                if row.get("status") == "ok":
                    fuels.append(row["fuel_per_vehicle_L"])
        if not fuels:
            return float("inf")
        return float(np.mean(fuels))

    best_path = out_dir / "ppo_best.zip"
    best_score = float("inf")
    wrote_best = False
    # Score the final checkpoint and one midpoint on full VALIDATION episodes.
    candidates = []
    if ckpts:
        candidates.append(ckpts[-1])
        if len(ckpts) > 2:
            candidates.append(ckpts[len(ckpts) // 2])
    scored = []
    for path in candidates:
        candidate = PPO.load(str(path))
        score = val_fuel(candidate)
        scored.append({"checkpoint": path.name, "val_fuel_per_vehicle_L": score})
        print(f"val {path.name} {score}")
        if score < best_score:
            best_score = score
            candidate.save(str(best_path))
            wrote_best = True

    # An older zip must not block the checkpoint this run just trained.
    if not wrote_best and ckpts:
        PPO.load(str(ckpts[-1])).save(str(best_path))
        wrote_best = True

    meta = {
        "selected_on": "VALIDATION seeds, all scenarios, full horizon" if not smoke else "VALIDATION smoke horizon",
        "train_seeds": list(train_seeds),
        "confirm_seeds": list(val_seeds),
        "scenarios": scenarios,
        "best_path": "results/rl/ppo_best.zip",
        "best_val_fuel_per_vehicle_L": None if best_score == float("inf") else best_score,
        "smoke": smoke,
        "timesteps_budget": budget,
        "config_total_timesteps": int(cfg["rl"]["total_timesteps"]),
        "sha256": _sha256(best_path) if best_path.exists() else None,
        "scored_checkpoints": scored,
        "note": "Baseline trained with the recorded timestep budget. Not an oracle controller.",
    }
    save_json(out_dir / "training_curve.json", {"curve": curves, "scored": scored})
    save_json(out_dir / "rl_selection.json", meta)
    print(meta)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    main(smoke=args.smoke)
