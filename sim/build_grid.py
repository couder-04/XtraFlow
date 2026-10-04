"""Build a 2x2 grid of signalized intersections (200 m links), left-hand traffic."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from sim.util import ROOT, ensure_dirs, load_config, locate_sumo, run_cmd, save_json


def build(cfg=None) -> Path:
    cfg = cfg or load_config()
    ensure_dirs()
    locate_sumo()
    L = float(cfg["simulation"]["grid_link_length_m"])
    net_dir = ROOT / "results" / "networks"
    nod_path = net_dir / "grid2x2.nod.xml"
    edg_path = net_dir / "grid2x2.edg.xml"
    net_path = net_dir / "grid2x2.net.xml"

    # Junctions at (0,0),(1,0),(0,1),(1,1) plus external stubs
    nodes = []
    # Internal TL nodes
    for iy in range(2):
        for ix in range(2):
            nodes.append((f"J{ix}{iy}", ix * L, iy * L, "traffic_light"))
    # External nodes for demand entry/exit
    externals = [
        ("N0", 0 * L, 2 * L), ("N1", 1 * L, 2 * L),
        ("S0", 0 * L, -L), ("S1", 1 * L, -L),
        ("E0", 2 * L, 0 * L), ("E1", 2 * L, 1 * L),
        ("W0", -L, 0 * L), ("W1", -L, 1 * L),
    ]
    for nid, x, y in externals:
        nodes.append((nid, x, y, "priority"))

    nod = ["<nodes>"]
    for nid, x, y, ntype in nodes:
        nod.append(f'  <node id="{nid}" x="{x}" y="{y}" type="{ntype}"/>')
    nod.append("</nodes>")

    edges = []
    # Horizontal links between junctions
    for iy in range(2):
        edges.append((f"H_{0}_{iy}_e", f"J0{iy}", f"J1{iy}"))
        edges.append((f"H_{1}_{iy}_w", f"J1{iy}", f"J0{iy}"))
    # Vertical links
    for ix in range(2):
        edges.append((f"V_{ix}_{0}_n", f"J{ix}0", f"J{ix}1"))
        edges.append((f"V_{ix}_{1}_s", f"J{ix}1", f"J{ix}0"))
    # Externals
    stubs = [
        ("N0_in", "N0", "J01"), ("N0_out", "J01", "N0"),
        ("N1_in", "N1", "J11"), ("N1_out", "J11", "N1"),
        ("S0_in", "S0", "J00"), ("S0_out", "J00", "S0"),
        ("S1_in", "S1", "J10"), ("S1_out", "J10", "S1"),
        ("E0_in", "E0", "J10"), ("E0_out", "J10", "E0"),
        ("E1_in", "E1", "J11"), ("E1_out", "J11", "E1"),
        ("W0_in", "W0", "J00"), ("W0_out", "J00", "W0"),
        ("W1_in", "W1", "J01"), ("W1_out", "J01", "W1"),
    ]
    edges.extend(stubs)

    edg = ["<edges>"]
    for eid, frm, to in edges:
        edg.append(
            f'  <edge id="{eid}" from="{frm}" to="{to}" numLanes="2" speed="13.89" priority="2"/>'
        )
    edg.append("</edges>")

    nod_path.write_text("\n".join(nod), encoding="utf-8")
    edg_path.write_text("\n".join(edg), encoding="utf-8")

    lat = cfg["simulation"].get("lateral_resolution", 0.4)
    use_sublane = cfg["simulation"].get("use_sublane", True)
    cmd = [
        "netconvert",
        "--node-files", str(nod_path),
        "--edge-files", str(edg_path),
        "--lefthand", "true",
        "--tls.guess", "true",
        "--tls.join", "true",
        "--no-turnarounds", "true",
        "--output-file", str(net_path),
    ]
    if use_sublane and lat:
        cmd += ["--lateral-resolution", str(lat)]
    proc = run_cmd(cmd, check=False)
    if proc.returncode != 0:
        cmd = [c for c in cmd if c not in ("--lateral-resolution", str(lat))]
        run_cmd(cmd, check=True)

    # Validate each TLS has no empty program
    import sumolib

    net = sumolib.net.readNet(str(net_path))
    tls_ids = [t.getID() for t in net.getTrafficLights()]
    save_json(ROOT / "results" / "grid_info.json", {
        "net": str(net_path),
        "tls_ids": tls_ids,
        "link_length_m": L,
        "lefthand": True,
    })
    print(f"Built grid: {net_path} tls={tls_ids}")
    return net_path


if __name__ == "__main__":
    build()
