"""Parse tripinfo/emissions and aggregate run metrics."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

from sim.util import load_config, mg_to_kg, mg_to_litres


def parse_tripinfo(tripinfo_path: Path, cfg: Optional[dict] = None) -> Dict[str, Any]:
    cfg = cfg or load_config()
    densities = cfg["fuel"]["density_kg_per_L"]
    fuel_type = cfg["fuel"]["type"]
    occupancy = cfg["occupancy_persons"]

    if not tripinfo_path.exists():
        return _empty()

    tree = ET.parse(tripinfo_path)
    root = tree.getroot()
    n_completed = 0
    total_fuel_L = 0.0
    total_CO2_kg = 0.0
    total_wait = 0.0
    total_timeloss = 0.0
    total_travel = 0.0
    total_stops = 0.0
    person_delay = 0.0
    fuel_by_type: Dict[str, float] = {}
    persons_total = 0.0

    for ti in root.findall("tripinfo"):
        n_completed += 1
        vtype = ti.get("vType") or ti.get("type") or "car"
        wait = float(ti.get("waitingTime", 0) or 0)
        timeloss = float(ti.get("timeLoss", 0) or 0)
        duration = float(ti.get("duration", 0) or 0)
        stops = float(ti.get("waitingCount", 0) or 0)
        total_wait += wait
        total_timeloss += timeloss
        total_travel += duration
        total_stops += stops
        occ = float(occupancy.get(vtype, 1.0))
        persons_total += occ
        person_delay += wait * occ

        # emissions child
        emis = ti.find("emissions")
        fuel_mg = 0.0
        co2_mg = 0.0
        if emis is not None:
            fuel_mg = float(emis.get("fuel_abs", emis.get("fuel", 0)) or 0)
            co2_mg = float(emis.get("CO2_abs", emis.get("CO2", 0)) or 0)
        ftype = fuel_type.get(vtype, "petrol")
        dens = float(densities[ftype])
        fuel_L = mg_to_litres(fuel_mg, dens)
        co2_kg = mg_to_kg(co2_mg)
        total_fuel_L += fuel_L
        total_CO2_kg += co2_kg
        fuel_by_type[vtype] = fuel_by_type.get(vtype, 0.0) + fuel_L

    n = max(n_completed, 1)
    return {
        "n_completed": n_completed,
        "total_fuel_L": total_fuel_L,
        "fuel_per_vehicle_L": total_fuel_L / n,
        "fuel_per_person_L": total_fuel_L / max(persons_total, 1.0),
        "total_CO2_kg": total_CO2_kg,
        "mean_waiting_s": total_wait / n,
        "mean_timeLoss_s": total_timeloss / n,
        "person_delay_s": person_delay / max(persons_total, 1.0),
        "mean_travel_time_s": total_travel / n,
        "stops_per_vehicle": total_stops / n,
        "fuel_L_by_type": fuel_by_type,
        "persons_total": persons_total,
    }


def parse_ssm_conflicts(ssm_path: Path, ttc_threshold: float = 1.5) -> int:
    if not ssm_path.exists():
        return 0
    try:
        tree = ET.parse(ssm_path)
    except ET.ParseError:
        return 0
    count = 0
    for conflict in tree.iter():
        # SUMO SSM output varies; count minTTC below threshold
        for attr in ("minTTC", "TTC", "ttc"):
            if attr in conflict.attrib:
                try:
                    if float(conflict.attrib[attr]) < ttc_threshold:
                        count += 1
                except ValueError:
                    pass
    return count


def _empty() -> Dict[str, Any]:
    return {
        "n_completed": 0,
        "total_fuel_L": 0.0,
        "fuel_per_vehicle_L": 0.0,
        "fuel_per_person_L": 0.0,
        "total_CO2_kg": 0.0,
        "mean_waiting_s": 0.0,
        "mean_timeLoss_s": 0.0,
        "person_delay_s": 0.0,
        "mean_travel_time_s": 0.0,
        "stops_per_vehicle": 0.0,
        "fuel_L_by_type": {},
        "persons_total": 0.0,
    }
