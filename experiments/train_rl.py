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
    val_seeds_all = seed_range(cfg["seed_protocol"]["validation"])
    # During training loop use a small VAL subset; final selection uses all VAL seeds.
    val_seeds = val_seeds_all[:1] if smoke else val_seeds_all[:3]
    scenarios = ["balanced", "peak_unbalanced", "dynamic"]
    # Full SUMO step = 1 env step; use shorter training episodes for tractability.
    # Selection remains on VALIDATION seeds via run_one fuel metric.
    timesteps = 2000 if smoke else min(int(cfg["rl"]["total_timesteps"]), 30000)
    train_horizon = 120 if smoke else 400
    if smoke:
        train_seeds = train_seeds[:2]
        val_seeds = val_seeds_all[:1]
        scenarios = ["balanced"]

    out_dir = ROOT / "results" / "rl"
    out_dir.mkdir(parents=True, exist_ok=True)
    curves = []

    # Round-robin environments via single env resetting across seeds/scenarios
    class MultiScenarioEnv(SumoTrafficEnv):
        def __init__(self):
            super().__init__(scenario=scenarios[0], seed=train_seeds[0], smoke=True if smoke else False, cfg=cfg)
            self.horizon = train_horizon
            self.timeout = train_horizon + 60
            self.smoke = True  # short episodes during training
            self._i = 0
            self._pairs = [(sc, s) for sc in scenarios for s in train_seeds]

        def reset(self, *, seed=None, options=None):
            sc, sd = self._pairs[self._i % len(self._pairs)]
            self._i += 1
            self.scenario = sc
            self._seed = sd
            self.horizon = train_horizon
            self.timeout = train_horizon + 60
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
        # validation (short smoke-length for loop speed; final confirm below)
        val_fuels = []
        tmp = out_dir / "ppo_latest.zip"
        model.save(str(tmp))
        for sd in val_seeds:
            row = run_one("balanced", "rl_ppo", sd, cfg=cfg, smoke=True, model=model)
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
                print("Early stop on VALIDATION (loop)")
                break

    env.close()
    # Final selection confirm on all VALIDATION seeds with full horizon
    if best_path.exists():
        model = PPO.load(str(best_path))
    final_fuels = []
    confirm_seeds = val_seeds_all[:1] if smoke else val_seeds_all
    for sd in confirm_seeds:
        row = run_one("balanced", "rl_ppo", sd, cfg=cfg, smoke=smoke, model=model)
        final_fuels.append(row["fuel_per_vehicle_L"])
    final_mean = float(np.mean(final_fuels)) if final_fuels else best_val
    save_json(out_dir / "training_curve.json", {"curve": curves, "best_val_fuel_loop": best_val,
                                                "best_val_fuel_confirm": final_mean})
    meta = {
        "selected_on": "VALIDATION seeds",
        "train_seeds": list(train_seeds),
        "confirm_seeds": list(confirm_seeds),
        "best_path": str(best_path),
        "best_val_fuel_per_vehicle_L": final_mean,
        "loop_val_fuel_per_vehicle_L": best_val,
        "smoke": smoke,
        "timesteps_budget": timesteps,
    }
    save_json(out_dir / "rl_selection.json", meta)
    print(meta)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    main(smoke=args.smoke)
