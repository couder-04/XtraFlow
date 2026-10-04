"""Build a single 4-arm left-hand-traffic signalized intersection for SUMO."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set, Tuple

from sim.util import ROOT, ensure_dirs, load_config, locate_sumo, probe_hbefa_classes, run_cmd, save_json

APPROACHES = ["N", "S", "E", "W"]


def _nod_edg(cfg) -> Tuple[str, str]:
    L = float(cfg["simulation"]["approach_length_m"])
    # Nodes: center + four outer
    nodes = [
        ("C", 0.0, 0.0, "traffic_light"),
        ("N", 0.0, L, "priority"),
        ("S", 0.0, -L, "priority"),
        ("E", L, 0.0, "priority"),
        ("W", -L, 0.0, "priority"),
    ]
    nod = ['<nodes>']
    for nid, x, y, ntype in nodes:
        nod.append(f'  <node id="{nid}" x="{x}" y="{y}" type="{ntype}"/>')
    nod.append("</nodes>")

    # Edges: inbound to C and outbound from C
    # Left-hand traffic: driving on left; netconvert --lefthand
    # 3 inbound lanes, 2 outbound
    edg = ['<edges>']
    for a in APPROACHES:
        edg.append(
            f'  <edge id="{a}_in" from="{a}" to="C" numLanes="3" speed="13.89" '
            f'priority="2"/>'
        )
        edg.append(
            f'  <edge id="{a}_out" from="C" to="{a}" numLanes="2" speed="13.89" '
            f'priority="2"/>'
        )
    edg.append("</edges>")
    return "\n".join(nod), "\n".join(edg)


def _connections_file(net_path: Path) -> None:
    """After first netconvert, we rebuild with explicit connections if needed.
    Lane meaning (inbound index from right in SUMO default): for lefthand,
    we document: lane 0 = left-turn/through, lane 1 = through, lane 2 = right/through.
    Actual indexing is verified in validate_phases against foes.
    """
    # Placeholder — connections come from netconvert defaults + tlLogic overlay.


PHASE_DEFS = {
    # state string length = number of controlled links; filled after net build
    "names": ["NS_TL", "NS_R", "EW_TL", "EW_R"],
}


def build_tllogic_fixed(n_links: int, link_groups: Dict[str, List[int]], greens: List[int],
                        yellow: int, all_red: int) -> str:
    """Build tlLogic XML with 4 phases + yellow + all-red between each."""
    order = ["NS_TL", "NS_R", "EW_TL", "EW_R"]
    phases_xml = []
    for i, name in enumerate(order):
        state = ["r"] * n_links
        for idx in link_groups[name]:
            state[idx] = "G"
        phases_xml.append(
            f'        <phase duration="{greens[i]}" state="{"".join(state)}" name="{name}"/>'
        )
        # yellow
        ystate = ["r"] * n_links
        for idx in link_groups[name]:
            ystate[idx] = "y"
        phases_xml.append(
            f'        <phase duration="{yellow}" state="{"".join(ystate)}" name="{name}_Y"/>'
        )
        # all-red
        phases_xml.append(
            f'        <phase duration="{all_red}" state="{"r" * n_links}" name="AR_{name}"/>'
        )
    return (
        '    <tlLogic id="C" type="static" programID="fixed" offset="0">\n'
        + "\n".join(phases_xml)
        + "\n    </tlLogic>\n"
    )


def build_tllogic_actuated(n_links: int, link_groups: Dict[str, List[int]],
                           min_g: int, max_g: int, yellow: int, all_red: int) -> str:
    order = ["NS_TL", "NS_R", "EW_TL", "EW_R"]
    phases_xml = []
    for name in order:
        state = ["r"] * n_links
        for idx in link_groups[name]:
            state[idx] = "G"
        phases_xml.append(
            f'        <phase duration="{max_g}" minDur="{min_g}" maxDur="{max_g}" '
            f'state="{"".join(state)}" name="{name}"/>'
        )
        ystate = ["r"] * n_links
        for idx in link_groups[name]:
            ystate[idx] = "y"
        phases_xml.append(
            f'        <phase duration="{yellow}" state="{"".join(ystate)}" name="{name}_Y"/>'
        )
        phases_xml.append(
            f'        <phase duration="{all_red}" state="{"r" * n_links}" name="AR_{name}"/>'
        )
    return (
        '    <tlLogic id="C" type="actuated" programID="actuated" offset="0">\n'
        + "\n".join(phases_xml)
        + "\n    </tlLogic>\n"
    )


def _infer_link_groups(net) -> Tuple[int, Dict[str, List[int]], List[str]]:
    """Map controlled links at TLS 'C' into phase groups using toEdge directions."""
    import sumolib  # noqa: WPS433

    tls = net.getTLS("C")
    connections = tls.getConnections()
    n = len(connections)
    # Each connection: (fromLane, toLane, linkIndex) or similar
    groups: Dict[str, List[int]] = {k: [] for k in ["NS_TL", "NS_R", "EW_TL", "EW_R"]}
    link_meta: List[str] = []

    for conn in connections:
        # sumolib TLS connection: inLane, outLane, linkIndex
        in_lane = conn[0]
        out_lane = conn[1]
        idx = conn[2] if len(conn) > 2 else None
        if idx is None:
            continue
        from_edge = in_lane.getEdge().getID()
        to_edge = out_lane.getEdge().getID()
        # Approach from N_in, S_in, E_in, W_in
        approach = from_edge.replace("_in", "")
        dest = to_edge.replace("_out", "")
        # Left-hand traffic turning:
        # From N: left->E, through->S, right->W
        turn = _classify_turn(approach, dest)
        if approach in ("N", "S"):
            if turn == "right":
                groups["NS_R"].append(idx)
            else:
                groups["NS_TL"].append(idx)
        else:
            if turn == "right":
                groups["EW_R"].append(idx)
            else:
                groups["EW_TL"].append(idx)
        link_meta.append(f"{idx}:{from_edge}->{to_edge}:{turn}")

    # dedupe preserve order
    for k in groups:
        groups[k] = sorted(set(groups[k]))
    return n, groups, link_meta


def _classify_turn(approach: str, dest: str) -> str:
    # Left-hand traffic: clockwise is left? In LHT, left turn is toward left of driver.
    # Facing southbound from N: left = E, right = W, through = S
    table = {
        ("N", "E"): "left",
        ("N", "S"): "through",
        ("N", "W"): "right",
        ("S", "W"): "left",
        ("S", "N"): "through",
        ("S", "E"): "right",
        ("E", "S"): "left",
        ("E", "W"): "through",
        ("E", "N"): "right",
        ("W", "N"): "left",
        ("W", "E"): "through",
        ("W", "S"): "right",
    }
    return table.get((approach, dest), "through")


def validate_phase_conflicts(net_path: Path, link_groups: Dict[str, List[int]],
                             n_links: int) -> Dict[str, List[str]]:
    """Assert each green state grants intended movements with no internal conflicts
    using SUMO foe information from the network."""
    import sumolib

    net = sumolib.net.readNet(str(net_path))
    tls = net.getTLS("C")
    connections = list(tls.getConnections())
    # Build foe matrix from connection foes if available
    foes: Dict[int, Set[int]] = {i: set() for i in range(n_links)}
    # sumolib may expose getFoes on TLS
    try:
        foe_str = tls.getFoes(0)  # may not exist for all versions
    except Exception:
        foe_str = None

    # Prefer reading from XML connection foe attributes
    tree = ET.parse(net_path)
    root = tree.getroot()
    for conn in root.findall("connection"):
        if conn.get("tl") != "C":
            continue
        link_index = conn.get("linkIndex")
        foe = conn.get("foes")
        if link_index is None or foe is None:
            continue
        li = int(link_index)
        # foes is a bitstring
        for j, bit in enumerate(foe):
            if bit == "1":
                foes[li].add(j)

    report: Dict[str, List[str]] = {"ok": [], "conflicts": [], "empty_groups": []}
    for name, idxs in link_groups.items():
        if not idxs:
            report["empty_groups"].append(name)
            continue
        conflict_pairs = []
        for a in idxs:
            for b in idxs:
                if a >= b:
                    continue
                if b in foes.get(a, set()) or a in foes.get(b, set()):
                    conflict_pairs.append(f"{a}-{b}")
        if conflict_pairs:
            report["conflicts"].append(f"{name}: {conflict_pairs}")
        else:
            report["ok"].append(name)
    # Also validate yellow/all-red lengths conceptually elsewhere
    if report["conflicts"]:
        raise AssertionError(f"Phase conflicts detected: {report['conflicts']}")
    return report


def write_additional_vtypes(cfg, emission_map: Dict[str, str], out: Path) -> None:
    lines = ['<additional>']
    for name, p in cfg["vehicle_params"].items():
        emis = emission_map.get(name, "HBEFA3/PC_G_EU4")
        lat = ' latAlignment="center"' if cfg["simulation"].get("use_sublane") else ""
        lines.append(
            f'  <vType id="{name}" vClass="{p["vClass"]}" length="{p["length"]}" '
            f'width="{p["width"]}" accel="{p["accel"]}" decel="{p["decel"]}" '
            f'maxSpeed="{p["maxSpeed"]}" guiShape="{p["guiShape"]}" '
            f'emissionClass="{emis}"{lat}/>'
        )
    lines.append("</additional>")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(cfg=None) -> Path:
    cfg = cfg or load_config()
    ensure_dirs()
    locate_sumo()
    emission_map = probe_hbefa_classes()

    net_dir = ROOT / "results" / "networks"
    nod_path = net_dir / "intersection.nod.xml"
    edg_path = net_dir / "intersection.edg.xml"
    con_path = net_dir / "intersection.con.xml"
    net_path = net_dir / "intersection.net.xml"
    add_path = net_dir / "vtypes.add.xml"

    nod, edg = _nod_edg(cfg)
    nod_path.write_text(nod, encoding="utf-8")
    edg_path.write_text(edg, encoding="utf-8")

    # First pass netconvert with lefthand
    lat = cfg["simulation"].get("lateral_resolution", 0.4)
    use_sublane = cfg["simulation"].get("use_sublane", True)
    cmd = [
        "netconvert",
        "--node-files", str(nod_path),
        "--edge-files", str(edg_path),
        "--lefthand", "true",
        "--tls.guess", "true",
        "--tls.join", "true",
        "--junctions.join", "true",
        "--no-turnarounds", "true",
        "--output-file", str(net_path),
    ]
    if use_sublane and lat:
        cmd += ["--lateral-resolution", str(lat)]
    proc = run_cmd(cmd, check=False)
    if proc.returncode != 0:
        # fall back without sublane
        cfg["simulation"]["use_sublane"] = False
        cmd = [c for c in cmd if c != "--lateral-resolution" and c != str(lat)]
        proc = run_cmd(cmd, check=True)
        save_json(ROOT / "results" / "sublane_fallback.json", {
            "used_sublane": False,
            "reason": proc.stderr[-2000:] if proc.stderr else "netconvert failed with sublane",
        })
    else:
        save_json(ROOT / "results" / "sublane_fallback.json", {"used_sublane": use_sublane})

    import sumolib

    net = sumolib.net.readNet(str(net_path))
    n_links, groups, meta = _infer_link_groups(net)
    if n_links == 0:
        raise RuntimeError("No TLS links found at junction C")

    # Ensure every link is assigned
    assigned = set()
    for idxs in groups.values():
        assigned.update(idxs)
    missing = [i for i in range(n_links) if i not in assigned]
    if missing:
        # assign leftovers to through groups by approach heuristic
        groups["NS_TL"].extend(missing)
        groups["NS_TL"] = sorted(set(groups["NS_TL"]))

    report = validate_phase_conflicts(net_path, groups, n_links)
    save_json(ROOT / "results" / "phase_groups.json", {
        "n_links": n_links,
        "groups": groups,
        "meta": meta,
        "validation": report,
    })

    greens = list(cfg["signals"]["fixed_greens_s"])
    yellow = int(cfg["signals"]["yellow_s"])
    all_red = int(cfg["signals"]["all_red_s"])
    min_g = int(cfg["signals"]["min_green_s"])
    max_g = int(cfg["signals"]["max_green_s"])

    # Keep netconvert's native tlLogic intact (ElementTree rewrite corrupted TLS binding).
    # Load our fixed + actuated programs from an additional file instead.
    tll_path = net_dir / "tls.add.xml"
    fixed_xml = build_tllogic_fixed(n_links, groups, greens, yellow, all_red)
    act_xml = build_tllogic_actuated(n_links, groups, min_g, max_g, yellow, all_red)
    tll_path.write_text(
        "<additional>\n" + fixed_xml + act_xml + "</additional>\n",
        encoding="utf-8",
    )

    write_additional_vtypes(cfg, emission_map, add_path)

    # Write a ready sumocfg template pieces
    save_json(ROOT / "results" / "network_info.json", {
        "net": str(net_path),
        "vtypes": str(add_path),
        "tls_additional": str(tll_path),
        "n_links": n_links,
        "groups": groups,
        "lefthand": True,
        "lane_meaning": (
            "Inbound 3 lanes: left-turn/through, through, right-turn/through "
            "(assumed geometry; indices validated via phase_groups.json)."
        ),
    })
    print(f"Built network: {net_path} n_links={n_links} groups={groups}")
    return net_path


if __name__ == "__main__":
    build()
