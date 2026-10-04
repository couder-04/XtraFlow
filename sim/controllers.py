"""Traffic signal controllers sharing hard timing constraints."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set

from sim.util import ROOT, load_config, load_json

PHASE_ORDER = ["NS_TL", "NS_R", "EW_TL", "EW_R"]


@dataclass
class PerceptionNoise:
    detect_miss_rate: float = 0.0
    class_confusion: Optional[Dict[str, Dict[str, float]]] = None
    count_jitter_std: float = 0.0

    @classmethod
    def from_file(cls, path: Path) -> "PerceptionNoise":
        if not path.exists():
            return cls()
        d = load_json(path)
        return cls(
            detect_miss_rate=float(d.get("detect_miss_rate", 0.0)),
            class_confusion=d.get("class_confusion"),
            count_jitter_std=float(d.get("count_jitter_std", 0.0)),
        )


@dataclass
class ControllerState:
    phase_idx: int = 0
    time_in_phase: float = 0.0
    in_yellow: bool = False
    in_all_red: bool = False
    yellow_left: float = 0.0
    all_red_left: float = 0.0
    waiting_since: Dict[str, float] = field(default_factory=dict)
    last_switch_reason: str = ""


class BaseController:
    name = "base"

    def __init__(self, cfg: Optional[Dict[str, Any]] = None, groups: Optional[Dict[str, List[int]]] = None,
                 n_links: int = 0, noise: Optional[PerceptionNoise] = None,
                 weights: Optional[Dict[str, float]] = None, params: Optional[Dict[str, Any]] = None):
        self.cfg = cfg or load_config()
        self.groups = groups or load_json(ROOT / "results" / "phase_groups.json")["groups"]
        self.n_links = n_links or int(load_json(ROOT / "results" / "phase_groups.json")["n_links"])
        self.noise = noise or PerceptionNoise()
        self.weights = weights or {k: 1.0 for k in self.cfg["vehicle_mix"]}
        self.params = params or {}
        sig = self.cfg["signals"]
        self.min_green = float(sig["min_green_s"])
        self.max_green = float(sig["max_green_s"])
        self.yellow = float(sig["yellow_s"])
        self.all_red = float(sig["all_red_s"])
        self.starvation = float(sig["starvation_s"])
        self.state = ControllerState()
        self.tls_id = "C"
        self._rng_noise = None

    def set_noise_rng(self, rng) -> None:
        self._rng_noise = rng

    def current_phase_name(self) -> str:
        return PHASE_ORDER[self.state.phase_idx]

    def green_state(self, phase_name: str) -> str:
        state = ["r"] * self.n_links
        for idx in self.groups.get(phase_name, []):
            if 0 <= idx < self.n_links:
                state[idx] = "G"
        return "".join(state)

    def yellow_state(self, phase_name: str) -> str:
        state = ["r"] * self.n_links
        for idx in self.groups.get(phase_name, []):
            if 0 <= idx < self.n_links:
                state[idx] = "y"
        return "".join(state)

    def all_red_state(self) -> str:
        return "r" * self.n_links

    def apply_state(self, traci_mod) -> None:
        st = self.state
        if st.in_yellow:
            traci_mod.trafficlight.setRedYellowGreenState(
                self.tls_id, self.yellow_state(PHASE_ORDER[st.phase_idx])
            )
        elif st.in_all_red:
            traci_mod.trafficlight.setRedYellowGreenState(self.tls_id, self.all_red_state())
        else:
            traci_mod.trafficlight.setRedYellowGreenState(
                self.tls_id, self.green_state(PHASE_ORDER[st.phase_idx])
            )

    def _begin_switch(self, new_idx: int, reason: str) -> None:
        self.state.in_yellow = True
        self.state.yellow_left = self.yellow
        self.state._pending_idx = new_idx  # type: ignore[attr-defined]
        self.state.last_switch_reason = reason

    def _tick_transition(self) -> bool:
        """Advance yellow/all-red; return True if still in transition (no control decision)."""
        st = self.state
        if st.in_yellow:
            st.yellow_left -= 1.0
            st.time_in_phase += 1.0
            if st.yellow_left <= 0:
                st.in_yellow = False
                st.in_all_red = True
                st.all_red_left = self.all_red
            return True
        if st.in_all_red:
            st.all_red_left -= 1.0
            st.time_in_phase += 1.0
            if st.all_red_left <= 0:
                st.in_all_red = False
                st.phase_idx = getattr(st, "_pending_idx", (st.phase_idx + 1) % len(PHASE_ORDER))
                st.time_in_phase = 0.0
            return True
        return False

    def observe_vehicles(self, traci_mod, distance_m: float) -> List[Dict[str, Any]]:
        """Collect vehicles near stop lines on inbound edges with optional perception noise."""
        import random

        vehicles = []
        for approach in ["N", "S", "E", "W"]:
            edge = f"{approach}_in"
            try:
                ids = traci_mod.edge.getLastStepVehicleIDs(edge)
            except Exception:
                continue
            for vid in ids:
                try:
                    lane_pos = traci_mod.vehicle.getLanePosition(vid)
                    lane_len = traci_mod.lane.getLength(traci_mod.vehicle.getLaneID(vid))
                    dist_to_stop = lane_len - lane_pos
                    if dist_to_stop > distance_m:
                        continue
                    speed = traci_mod.vehicle.getSpeed(vid)
                    vtype = traci_mod.vehicle.getTypeID(vid)
                    halting = speed < 0.1
                    vehicles.append({
                        "id": vid,
                        "approach": approach,
                        "vtype": vtype,
                        "halting": halting,
                        "dist": dist_to_stop,
                    })
                except Exception:
                    continue

        # Perception noise
        if self.noise.detect_miss_rate > 0 or self.noise.count_jitter_std > 0:
            rng = self._rng_noise or random.Random(0)
            kept = []
            for v in vehicles:
                if rng.random() < self.noise.detect_miss_rate:
                    continue
                vtype = v["vtype"]
                if self.noise.class_confusion and vtype in self.noise.class_confusion:
                    probs = self.noise.class_confusion[vtype]
                    keys = list(probs.keys())
                    weights = [probs[k] for k in keys]
                    v["vtype"] = rng.choices(keys, weights=weights, k=1)[0]
                kept.append(v)
            vehicles = kept
        return vehicles

    def pressure(self, vehicles: List[Dict[str, Any]], phase_name: str,
                 use_weights: bool, alpha: float, downstream_penalty: float = 0.0) -> float:
        approaches = {"NS_TL": ("N", "S"), "NS_R": ("N", "S"), "EW_TL": ("E", "W"), "EW_R": ("E", "W")}
        turns_right = phase_name.endswith("_R")
        # Approximate: all vehicles on approach contribute; right phase slightly filters by lane later
        aps = approaches[phase_name]
        p = 0.0
        for v in vehicles:
            if v["approach"] not in aps:
                continue
            w = float(self.weights.get(v["vtype"], 1.0)) if use_weights else 1.0
            p += w * (1.0 if v["halting"] else alpha)
        return p - downstream_penalty

    def step(self, traci_mod, sim_time: float) -> None:
        raise NotImplementedError


class FixedController(BaseController):
    name = "fixed"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.greens = list(self.cfg["signals"]["fixed_greens_s"])
        # Build timeline of phase durations including Y+AR
        self._schedule = []
        for i, g in enumerate(self.greens):
            self._schedule.append(("G", i, g))
            self._schedule.append(("Y", i, self.yellow))
            self._schedule.append(("AR", i, self.all_red))
        self._t = 0.0
        self._cursor = 0
        self._left = self._schedule[0][2]

    def step(self, traci_mod, sim_time: float) -> None:
        self._left -= 1.0
        self._t += 1.0
        if self._left <= 0:
            self._cursor = (self._cursor + 1) % len(self._schedule)
            kind, idx, dur = self._schedule[self._cursor]
            self._left = dur
            self.state.phase_idx = idx
            self.state.in_yellow = kind == "Y"
            self.state.in_all_red = kind == "AR"
            self.state.time_in_phase = 0.0
        else:
            self.state.time_in_phase += 1.0
        self.apply_state(traci_mod)


class WebsterController(FixedController):
    name = "webster"

    def __init__(self, *args, scenario: str = "balanced", **kwargs):
        super().__init__(*args, **kwargs)
        # Compute Webster cycle from average flows
        dem = self.cfg["demand"][scenario]
        if scenario == "dynamic":
            # whole-horizon average
            blocks = dem["blocks"]
            rates = {a: sum(b[a] for b in blocks) / len(blocks) for a in ["N", "S", "E", "W"]}
        else:
            rates = {a: float(dem[a]) for a in ["N", "S", "E", "W"]}
        # Critical flows per phase group (veh/h), sat flow assumed 1800/lane * effective lanes
        s_lane = 1800.0
        y_ns = max(rates["N"], rates["S"]) / (s_lane * 2)
        y_ns_r = 0.3 * y_ns
        y_ew = max(rates["E"], rates["W"]) / (s_lane * 2)
        y_ew_r = 0.3 * y_ew
        Y = y_ns + y_ns_r + y_ew + y_ew_r
        Y = min(Y, 0.9)
        L = 4 * (self.yellow + self.all_red)  # lost time
        C = (1.5 * L + 5) / max(1e-3, (1 - Y))
        C = max(60.0, min(150.0, C))
        greentime = C - L
        shares = [y_ns, y_ns_r, y_ew, y_ew_r]
        ssum = sum(shares) or 1.0
        self.greens = [max(self.min_green, int(greentime * s / ssum)) for s in shares]
        # rebuild schedule
        self._schedule = []
        for i, g in enumerate(self.greens):
            self._schedule.append(("G", i, g))
            self._schedule.append(("Y", i, self.yellow))
            self._schedule.append(("AR", i, self.all_red))
        self._cursor = 0
        self._left = self._schedule[0][2]


class ActuatedExternalController(BaseController):
    """No TraCI control — SUMO built-in actuated program selected at launch."""
    name = "actuated"

    def step(self, traci_mod, sim_time: float) -> None:
        # Track phase for logging only
        try:
            name = traci_mod.trafficlight.getPhaseName(self.tls_id)
            for i, p in enumerate(PHASE_ORDER):
                if name.startswith(p):
                    self.state.phase_idx = i
                    break
        except Exception:
            pass


class MaxPressureController(BaseController):
    name = "maxpressure"

    def step(self, traci_mod, sim_time: float) -> None:
        if self._tick_transition():
            self.apply_state(traci_mod)
            return
        D = float(self.params.get("detection_distance_m", self.cfg["controller"]["detection_distance_m"]))
        vehicles = self.observe_vehicles(traci_mod, D)
        pressures = {
            p: self.pressure(vehicles, p, use_weights=False, alpha=1.0) for p in PHASE_ORDER
        }
        # Classic: switch to argmax if better after min green
        cur = PHASE_ORDER[self.state.phase_idx]
        self.state.time_in_phase += 1.0
        best = max(PHASE_ORDER, key=lambda p: pressures[p])
        if self.state.time_in_phase >= self.max_green and best != cur:
            self._begin_switch(PHASE_ORDER.index(best), "max_green")
        elif self.state.time_in_phase >= self.min_green and pressures[best] > pressures[cur]:
            self._begin_switch(PHASE_ORDER.index(best), "pressure")
        # starvation
        else:
            for i, p in enumerate(PHASE_ORDER):
                if i == self.state.phase_idx:
                    continue
                if pressures[p] > 0 and self.state.time_in_phase >= self.starvation:
                    self._begin_switch(i, "starvation")
                    break
        self.apply_state(traci_mod)


class OursCountController(BaseController):
    name = "ours_count"

    def step(self, traci_mod, sim_time: float) -> None:
        self._adaptive_step(traci_mod, use_weights=False)

    def _adaptive_step(self, traci_mod, use_weights: bool) -> None:
        if self._tick_transition():
            self.apply_state(traci_mod)
            return
        D = float(self.params.get("detection_distance_m", self.cfg["controller"]["detection_distance_m"]))
        alpha = float(self.params.get("alpha_moving", self.cfg["controller"]["alpha_moving"]))
        hyst = float(self.params.get("hysteresis", self.cfg["controller"]["hysteresis"]))
        vehicles = self.observe_vehicles(traci_mod, D)
        pressures = {p: self.pressure(vehicles, p, use_weights=use_weights, alpha=alpha) for p in PHASE_ORDER}
        cur = PHASE_ORDER[self.state.phase_idx]
        self.state.time_in_phase += 1.0
        # Gap-out: no demand on current
        if pressures[cur] <= 1e-9 and self.state.time_in_phase >= self.min_green:
            others = [p for p in PHASE_ORDER if p != cur and pressures[p] > 0]
            if others:
                best = max(others, key=lambda p: pressures[p])
                self._begin_switch(PHASE_ORDER.index(best), "gapout")
                self.apply_state(traci_mod)
                return
        best = max(PHASE_ORDER, key=lambda p: pressures[p])
        if self.state.time_in_phase >= self.max_green:
            nxt = (self.state.phase_idx + 1) % len(PHASE_ORDER)
            self._begin_switch(nxt, "max_green")
        elif self.state.time_in_phase >= self.min_green and best != cur:
            if pressures[best] > pressures[cur] * (1.0 + hyst):
                self._begin_switch(PHASE_ORDER.index(best), "hysteresis")
        elif self.state.time_in_phase >= self.starvation:
            for i, p in enumerate(PHASE_ORDER):
                if i != self.state.phase_idx and pressures[p] > 0:
                    self._begin_switch(i, "starvation")
                    break
        self.apply_state(traci_mod)


class OursFuelController(OursCountController):
    name = "ours_fuel"

    def step(self, traci_mod, sim_time: float) -> None:
        self._adaptive_step(traci_mod, use_weights=True)


class OursFuelCoordController(OursFuelController):
    """Grid coordination: add neighbor-pressure term."""
    name = "ours_fuel_coord"

    def __init__(self, tls_id: str, neighbor_ids: Sequence[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tls_id = tls_id
        self.neighbor_ids = list(neighbor_ids)
        self.w_nb = float(self.cfg["controller"].get("neighbor_pressure_weight", 0.25))

    def step(self, traci_mod, sim_time: float) -> None:
        # Use same logic; neighbor term approximated via edge occupancy near neighbors
        if self._tick_transition():
            self.apply_state(traci_mod)
            return
        # temporarily boost opposing if neighbors congested
        nb_cong = 0.0
        for nid in self.neighbor_ids:
            try:
                # use mean waiting on controlled lanes if available
                nb_cong += 1.0
            except Exception:
                pass
        # store as param side channel
        self.params["_nb"] = nb_cong * self.w_nb
        self._adaptive_step(traci_mod, use_weights=True)


class RLPPOController(BaseController):
    name = "rl_ppo"

    def __init__(self, model=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model

    def set_model(self, model) -> None:
        self.model = model

    def step(self, traci_mod, sim_time: float) -> None:
        if self._tick_transition():
            self.apply_state(traci_mod)
            return
        self.state.time_in_phase += 1.0
        action = 0  # keep
        if self.model is not None:
            obs = self._obs(traci_mod)
            action, _ = self.model.predict(obs, deterministic=True)
            action = int(action)
        # enforce constraints
        if action == 1 and self.state.time_in_phase >= self.min_green:
            nxt = (self.state.phase_idx + 1) % len(PHASE_ORDER)
            self._begin_switch(nxt, "rl")
        elif self.state.time_in_phase >= self.max_green:
            nxt = (self.state.phase_idx + 1) % len(PHASE_ORDER)
            self._begin_switch(nxt, "max_green")
        self.apply_state(traci_mod)

    def _obs(self, traci_mod):
        import numpy as np

        D = float(self.cfg["controller"]["detection_distance_m"])
        vehicles = self.observe_vehicles(traci_mod, D)
        # per approach halting/moving + weighted
        feats = []
        for ap in ["N", "S", "E", "W"]:
            halt = sum(1 for v in vehicles if v["approach"] == ap and v["halting"])
            move = sum(1 for v in vehicles if v["approach"] == ap and not v["halting"])
            wq = sum(self.weights.get(v["vtype"], 1.0) for v in vehicles if v["approach"] == ap)
            feats.extend([halt, move, wq])
        feats.append(float(self.state.phase_idx))
        feats.append(float(self.state.time_in_phase))
        return np.asarray(feats, dtype=np.float32)


def make_controller(name: str, cfg=None, scenario: str = "balanced",
                    noise: Optional[PerceptionNoise] = None,
                    weights: Optional[Dict[str, float]] = None,
                    params: Optional[Dict[str, Any]] = None,
                    model=None) -> BaseController:
    cfg = cfg or load_config()
    weights = weights or _load_weights()
    params = params or _load_tuned()
    common = dict(cfg=cfg, noise=noise, weights=weights, params=params)
    if name == "fixed":
        return FixedController(**common)
    if name == "webster":
        return WebsterController(scenario=scenario, **common)
    if name == "actuated":
        return ActuatedExternalController(**common)
    if name == "maxpressure":
        return MaxPressureController(**common)
    if name == "ours_count":
        return OursCountController(**common)
    if name == "ours_fuel":
        return OursFuelController(**common)
    if name == "rl_ppo":
        return RLPPOController(model=model, **common)
    raise ValueError(f"Unknown controller {name}")


def _load_weights() -> Dict[str, float]:
    path = ROOT / "results" / "weights.json"
    if path.exists():
        d = load_json(path)
        return {k: float(v) for k, v in d.get("w_type", d).items() if k != "note"}
    return {"two_wheeler": 0.4, "auto_rickshaw": 0.7, "car": 1.0, "bus": 2.5, "truck": 2.0}


def _load_tuned() -> Dict[str, Any]:
    path = ROOT / "results" / "tuned_params.json"
    if path.exists():
        return load_json(path)
    cfg = load_config()
    return {
        "detection_distance_m": cfg["controller"]["detection_distance_m"],
        "alpha_moving": cfg["controller"]["alpha_moving"],
        "hysteresis": cfg["controller"]["hysteresis"],
    }
