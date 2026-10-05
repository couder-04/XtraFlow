"""2x2 grid: independent XtraFlow vs fixed/actuated vs coordinated neighbor-pressure."""
from __future__ import annotations

import time
from pathlib import Path

from sim.gen_demand import generate_grid
from sim.util import ROOT, ensure_dirs, load_config, load_json, locate_sumo, save_json


def run_grid(controller: str, seed: int, smoke: bool = False) -> dict:
    cfg = load_config()
    ensure_dirs()
    _, sumo_bin = locate_sumo()
    net = ROOT / "results" / "networks" / "grid2x2.net.xml"
    if not net.exists():
        from sim.build_grid import build
        build()
    vtypes = ROOT / "results" / "networks" / "vtypes.add.xml"
    routes = generate_grid("balanced", seed, cfg)
    horizon = 120 if smoke else 1800
    tag = f"grid_{controller}_seed{seed}"
    raw = ROOT / "results" / "raw"
    tripinfo = raw / f"{tag}.tripinfo.xml"
    sumocfg = raw / f"{tag}.sumocfg"
    # Prefer routes that already embed types; omit vtypes if routes define them.
    # duarouter output may already include vType definitions — only attach vtypes.add.xml
    # when the route file lacks <vType>.
    route_text = Path(routes).read_text(encoding="utf-8", errors="ignore")
    add_line = f'    <additional-files value="{vtypes}"/>\n' if "<vType" not in route_text else ""
    sumocfg.write_text(
        f"""<configuration>
  <input>
    <net-file value="{net}"/>
    <route-files value="{routes}"/>
{add_line}  </input>
  <output>
    <tripinfo-output value="{tripinfo}"/>
  </output>
  <time><begin value="0"/><end value="{horizon}"/></time>
  <processing><device.emissions.probability value="1"/><time-to-teleport value="-1"/></processing>
  <report><no-warnings value="true"/><no-step-log value="true"/></report>
</configuration>
""",
        encoding="utf-8",
    )
    import traci
    from sim.controllers import FixedController, OursFuelController, OursFuelCoordController, ActuatedExternalController
    from sim.metrics import parse_tripinfo

    traci.start([sumo_bin, "-c", str(sumocfg), "--duration-log.disable", "true"])
    info = load_json(ROOT / "results" / "grid_info.json")
    tls_ids = info.get("tls_ids", [])
    controllers = {}
    for tid in tls_ids:
        if controller == "fixed":
            c = FixedController(cfg=cfg)
            c.tls_id = tid
        elif controller == "actuated":
            c = ActuatedExternalController(cfg=cfg)
            c.tls_id = tid
            try:
                traci.trafficlight.setProgram(tid, "0")
            except Exception:
                pass
        elif controller == "XtraFlow":
            c = OursFuelController(cfg=cfg)
            c.tls_id = tid
        elif controller == "XtraFlow_coord":
            nbs = [x for x in tls_ids if x != tid]
            c = OursFuelCoordController(tid, nbs, cfg=cfg)
        else:
            raise ValueError(controller)
        controllers[tid] = c

    t0 = time.time()
    for step in range(horizon):
        if controller != "actuated":
            for c in controllers.values():
                c.step(traci, float(step))
        traci.simulationStep()
    traci.close()
    m = parse_tripinfo(tripinfo, cfg)
    return {
        "controller": controller,
        "seed": seed,
        "fuel_per_vehicle_L": m["fuel_per_vehicle_L"],
        "mean_waiting_s": m["mean_waiting_s"],
        "n_completed": m["n_completed"],
        "wall_time_s": time.time() - t0,
    }


def main(smoke: bool = False) -> None:
    seeds = [1] if smoke else [1, 2, 3, 4, 5]
    controllers = ["fixed", "actuated", "XtraFlow", "XtraFlow_coord"]
    rows = []
    for ctrl in controllers:
        for seed in seeds:
            try:
                rows.append(run_grid(ctrl, seed, smoke=smoke))
            except Exception as e:  # noqa: BLE001
                rows.append({"controller": ctrl, "seed": seed, "error": str(e),
                             "fuel_per_vehicle_L": float("nan"), "mean_waiting_s": float("nan"),
                             "n_completed": 0})

    import numpy as np
    import pandas as pd

    df = pd.DataFrame(rows)
    summary = df.groupby("controller")[["fuel_per_vehicle_L", "mean_waiting_s", "n_completed"]].mean().to_dict()
    # coordination benefit
    indep = df[df.controller == "XtraFlow"]["fuel_per_vehicle_L"].mean()
    coord = df[df.controller == "XtraFlow_coord"]["fuel_per_vehicle_L"].mean()
    coord_helps = bool(np.isfinite(coord) and np.isfinite(indep) and coord < indep)
    out = {
        "rows": rows,
        "summary_means": summary,
        "coordination_reduces_fuel": coord_helps,
        "label": "Simulation-based estimate",
    }
    save_json(ROOT / "results" / "grid_results.json", out)

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4))
    g = df.groupby("controller")["fuel_per_vehicle_L"].mean()
    ax.bar(g.index.astype(str), g.values)
    ax.set_ylabel("fuel_per_vehicle_L")
    ax.set_title("Grid 2x2 results")
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "figures" / "x_grid_results.png", dpi=200)
    plt.close(fig)
    print(out["coordination_reduces_fuel"])


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    main(smoke=args.smoke)
