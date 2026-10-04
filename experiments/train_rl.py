"""Train PPO on TRAIN seeds; select checkpoint on VALIDATION seeds."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from sim.rl_env import SumoTrafficEnv
from sim.run_sim import run_one
from sim.util import ROOT, ensure_dirs, load_config, save_json, seed_range


def main(smoke: bool = False) -> None:
    cfg = load_config()
    ensure_dirs()
    from stable_baselines3 import PPO

    train_seeds = seed_range(cfg["seed_protocol"]["train"])
    val_seeds = seed_range(cfg["seed_protocol"]["validation"])
    scenarios = ["balanced", "peak_unbalanced", "dynamic"]
    timesteps = 2000 if smoke else int(cfg["rl"]["total_timesteps"])
    if smoke:
        train_seeds = train_seeds[:2]
        val_seeds = val_seeds[:1]
        scenarios = ["balanced"]

    out_dir = ROOT / "results" / "rl"
    out_dir.mkdir(parents=True, exist_ok=True)
    curves = []

    # Round-robin environments via single env resetting across seeds/scenarios
    class MultiScenarioEnv(SumoTrafficEnv):
        def __init__(self):
            super().__init__(scenario=scenarios[0], seed=train_seeds[0], smoke=smoke, cfg=cfg)
            self._i = 0
            self._pairs = [(s, sc) for sc in scenarios for s in train_seeds]

        def reset(self, *, seed=None, options=None):
            sc, sd = self._pairs[self._i % len(self._pairs)]
            self._i += 1
            self.scenario = sc
            self._seed = sd
            return super().reset(seed=sd, options=options)

    env = MultiScenarioEnv()
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=float(cfg["rl"]["learning_rate"]),
        n_steps=min(256, timesteps) if smoke else int(cfg["rl"]["n_steps"]),
        batch_size=int(cfg["rl"]["batch_size"]),
        gamma=float(cfg["rl"]["gamma"]),
        verbose=1,
        seed=42,
    )

    # Manual training loop with logging
    chunk = max(500, timesteps // 10)
    done_steps = 0
    best_val = float("inf")
    best_path = out_dir / "ppo_best.zip"
    patience = int(cfg["rl"]["early_stop_patience"])
    stale = 0

    while done_steps < timesteps:
        model.learn(total_timesteps=chunk, reset_num_timesteps=False)
        done_steps += chunk
        # validation
        val_fuels = []
        for sd in val_seeds:
            # save temp and evaluate with run_one
            tmp = out_dir / "ppo_latest.zip"
            model.save(str(tmp))
            row = run_one("balanced", "rl_ppo", sd, cfg=cfg, smoke=True if smoke else False, model=model)
            val_fuels.append(row["fuel_per_vehicle_L"])
        mean_val = float(np.mean(val_fuels))
        curves.append({"timesteps": done_steps, "val_fuel_per_vehicle_L": mean_val})
        print(f"timesteps={done_steps} val_fuel={mean_val:.4f}")
        if mean_val < best_val:
            best_val = mean_val
            model.save(str(best_path))
            stale = 0
        else:
            stale += 1
            if stale >= patience:
                print("Early stop on VALIDATION")
                break

    env.close()
    save_json(out_dir / "training_curve.json", {"curve": curves, "best_val_fuel": best_val})
    meta = {
        "selected_on": "VALIDATION seeds",
        "train_seeds": train_seeds if not smoke else list(train_seeds),
        "best_path": str(best_path),
        "best_val_fuel_per_vehicle_L": best_val,
        "smoke": smoke,
    }
    save_json(out_dir / "rl_selection.json", meta)
    print(meta)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    main(smoke=args.smoke)
