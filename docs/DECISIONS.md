# Design Decisions Log

All non-sourced parameters are labelled **assumed**. Choices below record engineering trade-offs.

## D001 — Python version

**Choice:** Python 3.12 (venv).  
**Rationale:** System default is 3.14; torch/SB3/ultralytics more mature on 3.12. Homebrew `python@3.12` available.

## D001b — SUMO / dependency pins

**Choice:** `eclipse-sumo==1.21.0` (1.22.0 not on PyPI); `numpy==1.26.4` (ultralytics Darwin pin `<2`); `Pillow==10.4.0` (streamlit `<11`).  
**Rationale:** Resolved from pip conflict errors at install time; locked in `requirements.lock`.

## D002 — Lane geometry

**Choice:** 3 inbound lanes per approach: (1) left-turn/through shared, (2) through-only, (3) right-turn/through shared; 2 outbound lanes.  
**Rationale:** Matches typical Indian arterial approaches with mixed turns while keeping netconvert/TraCI tractable. Documented as assumed geometry.

## D003 — Phase plan

**Choice:** 4-phase protected plan: NS through+left → NS right → EW through+left → EW right; yellow 3 s, all-red 2 s.  
**Rationale:** Separates right-turn conflicts under left-hand traffic; simplifies foe validation vs a 2-group plan with permissive rights.

## D004 — Sublane model

**Choice:** Prefer `--lateral-resolution 0.4` for two-wheeler filtering; fall back to standard lanes if smoke is unstable.  
**Rationale:** Spec requires sublane for 2W realism; stability verified in smoke before committing.

## D005 — Vehicle mix

**Choice:** two_wheeler 40%, car 30%, auto_rickshaw 10%, bus 5%, truck 15% (assumed mixed-traffic scenario).  
**Occupancy assumed:** 2W 1.3, car 2.0, auto 2.0, bus 40, truck 1.2 persons/vehicle.

## D006 — Fuel densities

**Choice:** petrol 0.74 kg/L, diesel 0.84 kg/L (assumed, typical liquid hydrocarbon densities).  
**CO2 factors for extrapolation:** petrol 2.31 kg/L, diesel 2.68 kg/L (widely cited tank-to-wheel factors; labelled simulation-based estimate when used).

## D007 — Controllers share hard constraints

**Choice:** MIN_GREEN 15 s, MAX_GREEN 90 s, yellow 3 s, all-red 2 s, starvation 120 s for adaptive controllers.  
**Rationale:** Spec hard rules; prevents unsafe short greens and unbounded phases.

## D008 — Demand horizon

**Choice:** 3600 s demand + drain until completion or 2× timeout (7200 s wall).  
**Scenarios:** balanced, peak_unbalanced (NS≈4×EW), dynamic (1200 s blocks), low_demand.

## D009 — Emission primary model

**Choice:** Runtime-probed classes that the installed SUMO accepts. On eclipse-sumo 1.21.0 this is **HBEFA3** (HBEFA4 class names are absent); cross-check uses **PHEMlight** when available. Mapping logged in `results/emission_class_map.json` and README.  
**Rationale:** Portability across SUMO installs without fabricating class names; verified by loading each candidate.

## D010 — RL reward

**Choice:** `r = -fuel_weighted_waiting - λ_switch * switch`; λ_switch tuned lightly on validation.  
**Rationale:** Aligns RL with energy-aware objective while discouraging chatter.

## D010b — RL training budget

**Choice:** Train with short episodes (600 s) up to 50k timesteps; select checkpoint by VALIDATION fuel via `run_one`.  
**Rationale:** Full 3600 s × 200k SUMO steps is wall-clock prohibitive; protocol (VAL selection, TEST untouched) preserved.

## D010c — Hyperparameter search

**Choice:** Screen tune grid on first 5 VALIDATION seeds; confirm top-3 on all 20 VALIDATION seeds.  
**Rationale:** Same seed split; reduces redundant full-grid × 20 cost while keeping selection VAL-only.

## D011 — Perception without user video

**Choice:** Synthetic smoke + assumed noise model (miss≈0.15, mild class confusion); clearly labelled assumed.  
**Rationale:** Spec allows this when `data/video/` absent.

## D012 — Fuel-price placeholder

**Choice:** INR 100/L base in config (user-editable PLACEHOLDER).  
**Rationale:** Price varies; extrapolation must not pretend a fixed market price.

## D013 — Headline fuel reduction sanity

**Choice:** If ours_fuel vs fixed >30% mean reduction, treat as bug/unfair baseline before reporting; expect ~5–20%.  
**Rationale:** Spec hard rule for scientific credibility.

## D014 — Independent demand generation

**Choice:** Demand files keyed only by scenario+seed; regenerated identically for every controller.  
**Rationale:** Spec rule 4 — fair comparison.

## D015 — Demand flow levels

**Choice:** Lower approach flows (e.g. balanced 480 veh/h, peak NS 720 / EW 180) after full-horizon runs at higher rates showed `gridlock_flag=1` and large n_completed gaps.  
**Rationale:** Target ~70–90% DoS under fixed without systemic incompletion; still labelled assumed.

## D016 — Pressure turn filtering

**Choice:** Phase pressure counts only vehicles whose route turn matches the phase (through+left vs right), not all vehicles on the approach.  
**Rationale:** Without this, NS_TL and NS_R pressures were nearly identical, starving EW and causing gridlock (observed on VAL seed 2000).

## D017 — Peak headline ~22% vs fixed

**Choice:** Report peak_unbalanced mean fuel reduction 21.76% (95% CI 20.0–23.5) despite “expect ~5–20%” guidance.  
**Rationale:** Below the 30% bug threshold; n_completed matched across controllers; no ours_fuel gridlock on TEST; strong NS/EW imbalance is where adaptive control should help most. Documented as upper end of plausible range.

## D018 — Grid underperformance

**Choice:** Report honestly that on the 2×2 grid, independent/coordinated ours_fuel underperformed fixed and actuated (higher fuel and waiting). Coordination term did not change outcomes.  
**Rationale:** Spec requires mixed/negative results; controller was tuned for single junction.
