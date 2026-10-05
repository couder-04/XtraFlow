# STATE.md — XtraFlow

Last updated: 2026-10-05

## Phase checklist

| Phase | Description | Status | Notes |
|-------|-------------|--------|-------|
| 0 | Repo scaffold, venv, deps, docs | DONE | |
| 1 | Network + vehicles + demand | DONE | |
| 2 | Controllers + metrics + RL env | DONE | |
| 3 | Tests + smoke + calibrate + tune | DONE | |
| 4 | Train RL + config.lock + TEST sweep | DONE | 840/840 rows, 0 NaN |
| 5 | Analyze + robustness + sensitivity + emission + safety + grid + extrapolate | DONE | |
| 6 | Perception + demo + dashboard + deck + report + audit | DONE | |
| 7 | Acceptance checklist | DONE | |

## Key artifacts

- `results/raw_runs.csv` — 7×4×30 complete
- `results/weights.json`, `results/tuned_params.json`, `results/config.lock`
- `results/summary.json`, `results/headlines.json`, `results/REPORT.md`
- `results/figures/` — 11 figures
- `results/demo/demo.mp4`, `results/deck.pptx`
- `perception/noise_model.json` (ASSUMED without user video)

## Caveats discovered

- HBEFA3/PHEMlight only (no HBEFA4 in SUMO 1.21 wheel)
- SSM conflict counts all zero (device output may be empty / under-sensitive)
- RL underperforms XtraFlow; 13.3% RL gridlock rate on TEST
- 2×2 grid: XtraFlow worse than fixed/actuated; coordination adds nothing
- Peak fuel reduction ~22% (above 20% band, below 30% sanity threshold)
- Perception noise model assumed without user video
- Assumed vehicle mix / not Indian-vehicle-calibrated emissions
- config.lock refreshed after the project name change to XtraFlow; simulation parameters unchanged
