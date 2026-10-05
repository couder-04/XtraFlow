"""Shared utilities: config, SUMO location, seeds, hashing, paths."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_config(path: Optional[Path] = None) -> Dict[str, Any]:
    path = path or (ROOT / "config.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs() -> None:
    for p in [
        ROOT / "results" / "networks",
        ROOT / "results" / "demand",
        ROOT / "results" / "tables",
        ROOT / "results" / "figures",
        ROOT / "results" / "raw",
        ROOT / "results" / "timeseries",
        ROOT / "results" / "rl",
        ROOT / "results" / "demo",
    ]:
        p.mkdir(parents=True, exist_ok=True)


def locate_sumo() -> Tuple[str, str]:
    """Return (SUMO_HOME, sumo_binary). Prefer pip eclipse-sumo package."""
    sumo_home = os.environ.get("SUMO_HOME")
    if not sumo_home:
        try:
            import sumo  # type: ignore

            sumo_home = os.path.dirname(sumo.__file__)
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(
                "SUMO not found. Install eclipse-sumo or set SUMO_HOME."
            ) from e
    os.environ["SUMO_HOME"] = sumo_home
    tools = os.path.join(sumo_home, "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    candidates = []
    which = shutil.which("sumo")
    if which:
        candidates.append(Path(which))
    candidates.extend([
        Path(sumo_home) / "bin" / "sumo",
        Path(sumo_home).resolve().parent.parent.parent / "bin" / "sumo",
        ROOT / ".venv" / "bin" / "sumo",
        Path(sys.prefix) / "bin" / "sumo",
    ])
    binary = None
    for c in candidates:
        try:
            if c is not None and Path(c).exists():
                binary = str(Path(c).resolve())
                break
        except OSError:
            continue
    if binary is None:
        raise RuntimeError(f"sumo binary not found under SUMO_HOME={sumo_home}")
    # ensure bin on PATH
    bin_dir = str(Path(binary).parent)
    if bin_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
    return sumo_home, binary


def seed_range(lo_hi: Sequence[int]) -> List[int]:
    lo, hi = int(lo_hi[0]), int(lo_hi[1])
    return list(range(lo, hi + 1))


def config_sha256(path: Optional[Path] = None) -> str:
    path = path or (ROOT / "config.yaml")
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def freeze_config(cfg_path: Optional[Path] = None, lock_path: Optional[Path] = None) -> str:
    ensure_dirs()
    cfg_path = cfg_path or (ROOT / "config.yaml")
    lock_path = lock_path or (ROOT / "results" / "config.lock")
    h = config_sha256(cfg_path)
    payload = {
        "sha256": h,
        "config_path": str(cfg_path.resolve()),
        "note": "TEST sweep must use this exact config.yaml hash",
    }
    lock_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return h


def assert_config_locked(cfg_path: Optional[Path] = None, lock_path: Optional[Path] = None) -> None:
    cfg_path = cfg_path or (ROOT / "config.yaml")
    lock_path = lock_path or (ROOT / "results" / "config.lock")
    if not lock_path.exists():
        raise RuntimeError("config.lock missing; run freeze_config before TEST sweep/analyze")
    locked = json.loads(lock_path.read_text(encoding="utf-8"))
    current = config_sha256(cfg_path)
    if locked.get("sha256") != current:
        raise RuntimeError(
            f"config.yaml hash changed after freeze: locked={locked.get('sha256')} current={current}"
        )


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_cmd(cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd or ROOT, check=check, capture_output=True, text=True)


def _emission_class_exists(class_name: str, net_path: Optional[Path] = None) -> bool:
    """Return True if SUMO accepts this emissionClass on a trivial load."""
    _, binary = locate_sumo()
    net_path = net_path or (ROOT / "results" / "networks" / "intersection.net.xml")
    if not net_path.exists():
        # Without a net, accept well-known HBEFA3 / PHEMlight names only
        return class_name.startswith(("HBEFA3/", "PHEMlight/", "Zero", "Energy/"))
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        add = td_path / "ec.add.xml"
        add.write_text(
            f'<additional><vType id="t" emissionClass="{class_name}"/></additional>\n',
            encoding="utf-8",
        )
        rou = td_path / "ec.rou.xml"
        rou.write_text(
            '<routes><vehicle id="v" type="t" depart="0">'
            '<route edges="N_in S_out"/></vehicle></routes>\n',
            encoding="utf-8",
        )
        cfg = td_path / "ec.sumocfg"
        cfg.write_text(
            f"""<configuration>
  <input>
    <net-file value="{net_path}"/>
    <route-files value="{rou}"/>
    <additional-files value="{add}"/>
  </input>
  <time><begin value="0"/><end value="1"/></time>
  <report><no-warnings value="true"/><no-step-log value="true"/></report>
</configuration>
""",
            encoding="utf-8",
        )
        proc = subprocess.run([binary, "-c", str(cfg)], capture_output=True, text=True)
        err = (proc.stderr or "") + (proc.stdout or "")
        return "emissionClass" not in err and "Quitting" not in err


def probe_hbefa_classes() -> Dict[str, str]:
    """Map our vehicle types to emission classes that exist in the installed SUMO."""
    preferred = {
        "two_wheeler": ["HBEFA3/LDV_G_EU4", "HBEFA3/PC_G_EU4", "PHEMlight/PC_G_EU4"],
        "auto_rickshaw": ["HBEFA3/PC_G_EU4", "PHEMlight/PC_G_EU4"],
        "car": ["HBEFA3/PC_G_EU4", "PHEMlight/PC_G_EU4"],
        "bus": ["HBEFA3/Bus", "PHEMlight/PC_G_EU4"],
        "truck": ["HBEFA3/HDV", "HBEFA3/Bus"],
    }
    # This eclipse-sumo 1.21 wheel ships HBEFA3 + PHEMlight, not HBEFA4.
    mapping: Dict[str, str] = {}
    tested: Dict[str, bool] = {}
    net = ROOT / "results" / "networks" / "intersection.net.xml"
    for vtype, cands in preferred.items():
        chosen = None
        for c in cands:
            if c not in tested:
                tested[c] = _emission_class_exists(c, net if net.exists() else None)
            if tested[c]:
                chosen = c
                break
        mapping[vtype] = chosen or "HBEFA3/PC_G_EU4"

    # Alternate for cross-check: PHEMlight where available else different HBEFA3 petrol/diesel
    alt_cands = {
        "two_wheeler": ["PHEMlight/PC_G_EU4", "HBEFA3/PC_G_EU3"],
        "auto_rickshaw": ["PHEMlight/PC_G_EU4", "HBEFA3/PC_G_EU3"],
        "car": ["PHEMlight/PC_G_EU4", "HBEFA3/PC_G_EU3"],
        "bus": ["PHEMlight/PC_G_EU4", "HBEFA3/HDV"],
        "truck": ["PHEMlight/PC_G_EU4", "HBEFA3/Bus"],
    }
    alt: Dict[str, str] = {}
    for vtype, cands in alt_cands.items():
        chosen = None
        for c in cands:
            if c not in tested:
                tested[c] = _emission_class_exists(c, net if net.exists() else None)
            if tested[c] and c != mapping.get(vtype):
                chosen = c
                break
        alt[vtype] = chosen or mapping[vtype]

    out = {
        "primary": mapping,
        "alternate": alt,
        "tested": tested,
        "note": "Installed SUMO 1.21: HBEFA3/PHEMlight available; HBEFA4 not present in this build.",
    }
    ensure_dirs()
    save_json(ROOT / "results" / "emission_class_map.json", out)
    return mapping


def mg_to_litres(fuel_mg: float, density_kg_per_L: float) -> float:
    """fuel_mg (milligrams) -> litres using density kg/L."""
    # mg -> kg: /1e6; kg / (kg/L) = L
    if density_kg_per_L <= 0:
        raise ValueError("density must be positive")
    return (fuel_mg / 1e6) / density_kg_per_L


def mg_to_kg(mass_mg: float) -> float:
    return mass_mg / 1e6


def kmh_to_ms(kmh: float) -> float:
    return kmh / 3.6


CONTROLLER_NAMES = [
    "fixed",
    "webster",
    "actuated",
    "maxpressure",
    "ours_count",
    "ours_fuel",
    "rl_ppo",
]

SCENARIOS = ["balanced", "peak_unbalanced", "dynamic", "low_demand"]
