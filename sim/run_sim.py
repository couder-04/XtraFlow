"""Run a single SUMO simulation with a given controller and collect metrics."""
from __future__ import annotations

import csv
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from sim.controllers import PerceptionNoise, make_controller
from sim.gen_demand import generate
from sim.metrics import parse_ssm_conflicts, parse_tripinfo
from sim.util import ROOT, ensure_dirs, load_config, load_json, locate_sumo, save_json


def _write_sumocfg(net: Path, routes: Path, additional: List[Path], out_cfg: Path,
                   tripinfo: Path, ssm: Optional[Path] = None, emission_prob: float = 1.0,
                   begin: int = 0, end: Optional[int] = None,
                   lateral_resolution: Optional[float] = None,
                   tls_program: Optional[str] = None) -> None:
    adds = ",".join(str(p) for p in additional)
    end_line = f'    <end value="{end}"/>\n' if end else ""
    lat_line = ""
    if lateral_resolution and lateral_resolution > 0:
        lat_line = f'    <lateral-resolution value="{lateral_resolution}"/>\n'
    ssm_lines = ""
    if ssm is not None:
        # SSM via device parameters (SUMO 1.21: no top-level ssmout option)
        ssm_lines = (
            f'    <device.ssm.probability value="1"/>\n'
            f'    <device.ssm.file value="{ssm}"/>\n'
            f'    <device.ssm.measures value="TTC"/>\n'
            f'    <device.ssm.thresholds value="1.5"/>\n'
        )
    xml = f"""<configuration>
  <input>
    <net-file value="{net}"/>
    <route-files value="{routes}"/>
    <additional-files value="{adds}"/>
  </input>
  <output>
    <tripinfo-output value="{tripinfo}"/>
  </output>
  <time>
    <begin value="{begin}"/>
{end_line}  </time>
  <processing>
    <time-to-teleport value="-1"/>
    <device.emissions.probability value="{emission_prob}"/>
{lat_line}{ssm_lines}  </processing>
  <report>
    <no-warnings value="true"/>
    <no-step-log value="true"/>
  </report>
</configuration>
"""
    out_cfg.write_text(xml, encoding="utf-8")


RAW_FIELDS = [
    "scenario", "controller", "seed", "emission_model", "n_departed", "n_completed",
    "total_fuel_L", "fuel_per_vehicle_L", "fuel_per_person_L", "total_CO2_kg",
    "mean_waiting_s", "mean_timeLoss_s", "person_delay_s", "mean_travel_time_s",
    "stops_per_vehicle", "idle_vehicle_seconds", "mean_queue_veh", "max_queue_veh",
    "fuel_L_by_type", "ssm_conflicts", "gridlock_flag", "wall_time_s",
]


def run_one(
    scenario: str,
    controller: str,
    seed: int,
    cfg: Optional[dict] = None,
    smoke: bool = False,
    emission_model: str = "primary",
    noise: Optional[PerceptionNoise] = None,
    demand_mult: float = 1.0,
    mix_override: Optional[Dict[str, float]] = None,
    save_timeseries: bool = False,
    model=None,
    net_path: Optional[Path] = None,
    routes_path: Optional[Path] = None,
    tls_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    cfg = cfg or load_config()
    ensure_dirs()
    sumo_home, sumo_bin = locate_sumo()

    horizon = 120 if smoke else int(cfg["simulation"]["demand_horizon_s"])
    timeout = int(horizon * cfg["simulation"]["drain_timeout_multiplier"])
    if smoke:
        timeout = 240

    net = net_path or (ROOT / "results" / "networks" / "intersection.net.xml")
    vtypes = ROOT / "results" / "networks" / "vtypes.add.xml"
    tls_add = ROOT / "results" / "networks" / "tls.add.xml"

    if routes_path is None:
        # For smoke, still generate full demand file but end sim early
        routes = generate(scenario, seed, cfg, demand_mult=demand_mult, mix_override=mix_override)
    else:
        routes = routes_path

    tag = f"{scenario}_{controller}_seed{seed}_{emission_model}"
    if smoke:
        tag = "smoke_" + tag
    raw_dir = ROOT / "results" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    tripinfo = raw_dir / f"{tag}.tripinfo.xml"
    ssm_out = raw_dir / f"{tag}.ssm.xml"
    cfg_path = raw_dir / f"{tag}.sumocfg"

    # Emission class swap for cross-check
    add_files = [vtypes, tls_add]
    if emission_model == "alternate":
        alt_vtypes = raw_dir / f"{tag}_vtypes_alt.add.xml"
        emap = load_json(ROOT / "results" / "emission_class_map.json")
        alt = emap.get("alternate", {})
        # rewrite vtypes
        text = vtypes.read_text(encoding="utf-8")
        primary = emap.get("primary", {})
        for vt, clas in primary.items():
            if vt in alt:
                text = text.replace(clas, alt[vt])
        alt_vtypes.write_text(text, encoding="utf-8")
        add_files = [alt_vtypes, tls_add]

    lat = None
    sub = load_json(ROOT / "results" / "sublane_fallback.json") if (ROOT / "results" / "sublane_fallback.json").exists() else {}
    if sub.get("used_sublane") and cfg["simulation"].get("use_sublane"):
        lat = float(cfg["simulation"].get("lateral_resolution", 0.4))

    _write_sumocfg(
        net, routes, add_files, cfg_path, tripinfo, ssm=ssm_out,
        emission_prob=1.0, end=timeout if smoke else None,
        lateral_resolution=lat,
    )

    import traci

    sumo_cmd = [sumo_bin, "-c", str(cfg_path), "--duration-log.disable", "true"]
    # For actuated, switch program
    if controller == "actuated":
        sumo_cmd += ["--tls.all-off", "false"]

    t0 = time.time()
    traci.start(sumo_cmd)

    # Select TLS program
    try:
        if controller == "actuated":
            traci.trafficlight.setProgram("C", "actuated")
        else:
            traci.trafficlight.setProgram("C", "fixed")
    except Exception:
        pass

    ctrl = make_controller(controller, cfg=cfg, scenario=scenario, noise=noise, model=model)
    # For non-actuated, take over via setPhase / setRYG each step

    idle_vehicle_seconds = 0.0
    queue_samples: List[float] = []
    max_queue = 0.0
    n_departed = 0
    ts_rows = []
    cum_fuel_mg = 0.0
    green_alloc = {p: 0 for p in ["NS_TL", "NS_R", "EW_TL", "EW_R"]}
    gridlock_flag = 0
    stuck_steps = 0

    step = 0
    while step < timeout:
        if controller != "actuated":
            ctrl.step(traci, float(step))
        else:
            ctrl.step(traci, float(step))

        traci.simulationStep()
        step += 1

        # metrics sampling
        try:
            veh_ids = traci.vehicle.getIDList()
            n_departed = max(n_departed, traci.simulation.getDepartedNumber() + n_departed)
            # better: cumulative departed
        except Exception:
            veh_ids = []

        halted = 0
        for vid in veh_ids:
            try:
                if traci.vehicle.getSpeed(vid) < 0.1:
                    idle_vehicle_seconds += 1.0
                    halted += 1
            except Exception:
                pass
        queue_samples.append(float(halted))
        max_queue = max(max_queue, float(halted))

        # green allocation
        if not ctrl.state.in_yellow and not ctrl.state.in_all_red:
            green_alloc[ctrl.current_phase_name()] = green_alloc.get(ctrl.current_phase_name(), 0) + 1

        # fuel probe cumulative (optional expensive)
        if save_timeseries and step % 5 == 0:
            fuel_now = 0.0
            for vid in veh_ids:
                try:
                    fuel_now += traci.vehicle.getFuelConsumption(vid)
                except Exception:
                    pass
            cum_fuel_mg += fuel_now  # per-step rate approx
            ts_rows.append({
                "t": step,
                "queue": halted,
                "cum_fuel_proxy": cum_fuel_mg,
                "phase": ctrl.current_phase_name(),
                "green_alloc": dict(green_alloc),
            })

        # completion / drain
        if step >= horizon:
            try:
                if traci.simulation.getMinExpectedNumber() == 0:
                    break
            except Exception:
                break
            # gridlock heuristic: many halted and no completions progress
            if halted > 40:
                stuck_steps += 1
            else:
                stuck_steps = 0
            if stuck_steps > 300:
                gridlock_flag = 1
                break

    # final departed count
    try:
        # recount from route file
        n_departed = routes.read_text(encoding="utf-8").count("<vehicle ")
    except Exception:
        pass

    traci.close()
    wall = time.time() - t0

    metrics = parse_tripinfo(tripinfo, cfg)
    ssm_conflicts = parse_ssm_conflicts(ssm_out)

    # n_departed from tripinfo + still running approx
    if metrics["n_completed"] == 0 and n_departed == 0:
        n_departed = 0

    row = {
        "scenario": scenario,
        "controller": controller,
        "seed": seed,
        "emission_model": emission_model,
        "n_departed": n_departed,
        "n_completed": metrics["n_completed"],
        "total_fuel_L": metrics["total_fuel_L"],
        "fuel_per_vehicle_L": metrics["fuel_per_vehicle_L"],
        "fuel_per_person_L": metrics["fuel_per_person_L"],
        "total_CO2_kg": metrics["total_CO2_kg"],
        "mean_waiting_s": metrics["mean_waiting_s"],
        "mean_timeLoss_s": metrics["mean_timeLoss_s"],
        "person_delay_s": metrics["person_delay_s"],
        "mean_travel_time_s": metrics["mean_travel_time_s"],
        "stops_per_vehicle": metrics["stops_per_vehicle"],
        "idle_vehicle_seconds": idle_vehicle_seconds,
        "mean_queue_veh": float(sum(queue_samples) / max(len(queue_samples), 1)),
        "max_queue_veh": max_queue,
        "fuel_L_by_type": json.dumps(metrics["fuel_L_by_type"]),
        "ssm_conflicts": ssm_conflicts,
        "gridlock_flag": gridlock_flag,
        "wall_time_s": wall,
    }

    if save_timeseries:
        ts_path = ROOT / "results" / "timeseries" / f"{tag}.json"
        save_json(ts_path, {"rows": ts_rows, "green_alloc": green_alloc})

    return row


def append_raw_row(row: Dict[str, Any], path: Optional[Path] = None) -> None:
    path = path or (ROOT / "results" / "raw_runs.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RAW_FIELDS)
        if write_header:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in RAW_FIELDS})


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--scenario", default="balanced")
    p.add_argument("--controller", default="fixed")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    # ensure network
    from sim.build_network import build as build_net
    if not (ROOT / "results" / "networks" / "intersection.net.xml").exists():
        build_net()
    row = run_one(args.scenario, args.controller, args.seed, smoke=args.smoke)
    print(json.dumps(row, indent=2, default=str))
