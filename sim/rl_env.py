"""Gymnasium environment wrapping SUMO/TraCI for PPO training."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:  # pragma: no cover
    import gym
    from gym import spaces

from sim.controllers import PHASE_ORDER, OursFuelController, _load_tuned, _load_weights
from sim.gen_demand import generate
from sim.run_sim import _write_sumocfg
from sim.util import ROOT, load_config, locate_sumo


class SumoTrafficEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, scenario: str = "balanced", seed: int = 1000, smoke: bool = False,
                 cfg: Optional[dict] = None):
        super().__init__()
        self.cfg = cfg or load_config()
        self.scenario = scenario
        self._seed = seed
        self.smoke = smoke
        self.horizon = 120 if smoke else int(self.cfg["simulation"]["demand_horizon_s"])
        self.timeout = 240 if smoke else int(self.horizon * self.cfg["simulation"]["drain_timeout_multiplier"])
        self.weights = _load_weights()
        self.params = _load_tuned()
        # obs: 4 approaches * 3 + phase + time = 14
        self.observation_space = spaces.Box(low=0, high=1e4, shape=(14,), dtype=np.float32)
        self.action_space = spaces.Discrete(2)  # 0 keep, 1 switch
        self._traci = None
        self._ctrl = None
        self._step_count = 0
        self._sumo_bin = None

    def reset(self, *, seed: Optional[int] = None, options: Optional[dict] = None):
        if seed is not None:
            self._seed = seed
        if self._traci is not None:
            try:
                self._traci.close()
            except Exception:
                pass
        _, self._sumo_bin = locate_sumo()
        import traci

        self._traci = traci
        routes = generate(self.scenario, self._seed, self.cfg)
        net = ROOT / "results" / "networks" / "intersection.net.xml"
        vtypes = ROOT / "results" / "networks" / "vtypes.add.xml"
        tls_add = ROOT / "results" / "networks" / "tls.add.xml"
        tag = f"rl_{self.scenario}_seed{self._seed}"
        raw = ROOT / "results" / "rl"
        raw.mkdir(parents=True, exist_ok=True)
        tripinfo = raw / f"{tag}.tripinfo.xml"
        ssm = raw / f"{tag}.ssm.xml"
        cfg_path = raw / f"{tag}.sumocfg"
        _write_sumocfg(net, routes, [vtypes, tls_add], cfg_path, tripinfo, ssm, end=self.timeout)
        traci.start([self._sumo_bin, "-c", str(cfg_path), "--duration-log.disable", "true"])
        try:
            traci.trafficlight.setProgram("C", "fixed")
        except Exception:
            pass
        self._ctrl = OursFuelController(cfg=self.cfg, weights=self.weights, params=self.params)
        # Use RLPPOController shell for transitions
        from sim.controllers import RLPPOController

        self._ctrl = RLPPOController(cfg=self.cfg, weights=self.weights, params=self.params)
        self._step_count = 0
        self._prev_wait = 0.0
        obs = self._get_obs()
        return obs, {}

    def _get_obs(self) -> np.ndarray:
        traci = self._traci
        D = float(self.cfg["controller"]["detection_distance_m"])
        vehicles = self._ctrl.observe_vehicles(traci, D)
        feats = []
        for ap in ["N", "S", "E", "W"]:
            halt = sum(1 for v in vehicles if v["approach"] == ap and v["halting"])
            move = sum(1 for v in vehicles if v["approach"] == ap and not v["halting"])
            wq = sum(self.weights.get(v["vtype"], 1.0) for v in vehicles if v["approach"] == ap)
            feats.extend([halt, move, wq])
        feats.append(float(self._ctrl.state.phase_idx))
        feats.append(float(self._ctrl.state.time_in_phase))
        return np.asarray(feats, dtype=np.float32)

    def step(self, action: int):
        traci = self._traci
        ctrl = self._ctrl
        switched = 0
        if ctrl._tick_transition():
            ctrl.apply_state(traci)
        else:
            ctrl.state.time_in_phase += 1.0
            if int(action) == 1 and ctrl.state.time_in_phase >= ctrl.min_green:
                nxt = (ctrl.state.phase_idx + 1) % len(PHASE_ORDER)
                ctrl._begin_switch(nxt, "rl")
                switched = 1
            elif ctrl.state.time_in_phase >= ctrl.max_green:
                nxt = (ctrl.state.phase_idx + 1) % len(PHASE_ORDER)
                ctrl._begin_switch(nxt, "max_green")
                switched = 1
            ctrl.apply_state(traci)

        traci.simulationStep()
        self._step_count += 1

        # reward: negative fuel-weighted waiting + switch penalty
        vehicles = ctrl.observe_vehicles(traci, float(self.cfg["controller"]["detection_distance_m"]))
        wait_cost = 0.0
        for v in vehicles:
            if v["halting"]:
                wait_cost += float(self.weights.get(v["vtype"], 1.0))
        lam = float(self.cfg["controller"].get("switch_penalty_rl", 0.05))
        reward = -wait_cost - lam * switched

        terminated = False
        truncated = self._step_count >= self.timeout
        if self._step_count >= self.horizon:
            try:
                if traci.simulation.getMinExpectedNumber() == 0:
                    terminated = True
            except Exception:
                terminated = True
        obs = self._get_obs()
        return obs, float(reward), terminated, truncated, {}

    def close(self):
        if self._traci is not None:
            try:
                self._traci.close()
            except Exception:
                pass
            self._traci = None
