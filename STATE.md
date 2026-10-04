# STATE.md — AI-Based Smart Traffic & Fuel Optimization

Last updated: 2026-10-05

## Phase checklist

| Phase | Description | Status | Notes |
|-------|-------------|--------|-------|
| 0 | Repo scaffold, venv, deps, docs | DONE | py3.12, eclipse-sumo 1.21.0, requirements.lock |
| 1 | Network + vehicles + demand | DONE | 4-arm LHT n_links=16; grid 2x2; HBEFA3 mapping |
| 2 | Controllers + metrics + RL env | DONE | 7 controllers smoke OK |
| 3 | Tests + smoke + calibrate + tune | IN_PROGRESS | pytest 15/15; smoke all 7 OK |
| 4 | Train RL + config.lock + TEST sweep | PENDING | |
| 5 | Analyze + robustness + sensitivity + emission + safety + grid + extrapolate | PENDING | |
| 6 | Perception + demo + dashboard + deck + report + audit | PENDING | |
| 7 | Acceptance checklist + headline summary | PENDING | |

## Commands run

```
python3.12 -m venv .venv
pip install -r requirements.txt
python -m sim.build_network
python -m sim.build_grid
pytest tests/ -v   # 15 passed
smoke: all 7 controllers on balanced seed 1
```

## Open issues

- TraCI prints "Retrying in 1 seconds" once per start (non-fatal).
- n_completed can differ across controllers on short smoke; monitor on full TEST.
- RL without trained weights underperforms (expected until train_rl).
- Installed SUMO has HBEFA3/PHEMlight, not HBEFA4 (documented).

## Seed protocol (frozen)

- TRAIN: 1000–1049 (RL only)
- VALIDATION: 2000–2019 (tuning / model selection)
- TEST: 1–30 (final eval only, after config.lock)
