# STATE.md — XtraFlow

Last updated: 2026-10-06

## Status

Published time-cut study is on `main` (commit after this sync). Simulation-based estimate; assumed traffic mix. Controllers use an oracle detector unless `info_mode` is camera. Emission classes are proxies.

## What was published

| Artifact | State |
|---|---|
| `results/demand_calibration.json` | Real VALIDATION, `smoke: false` |
| `results/tuned_params.json` | Real VALIDATION tune, `smoke: false` |
| `results/fixed_tuned.json` | All four scenarios, `smoke: false` |
| `results/rl/ppo_best.zip` | Trained to ≥200000 steps (`smoke: false` in selection meta) |
| `results/rl/rl_selection.json` | Final zip kept; VALIDATION scoring stopped for time |
| `results/config.lock` | Frozen after the real fixed plan and 200k zip |
| `results/raw_runs.csv` | Locked TEST: 8 controllers × 4 scenarios × seeds 1–5 (160 ok rows). No `rl_ppo` |
| `results/headlines.json` | From that TEST sweep |
| `results/robustness.json` | Seeds 1–3 |
| `results/sensitivity.json` | Demand mult + 4 mix samples, seeds 1–2 |
| `results/emission_xcheck.json` | Seeds 1–2 |
| `results/safety.json` | From `raw_runs.csv` |
| `results/grid_results.json` | Not scored; note explains TLS mismatch |
| `results/REPORT.md`, figures, deck | Regenerated from the files above |

## Seed protocol (config)

- TRAIN 1000–1049
- VALIDATION 2000–2019 (tuning and fixed-plan search)
- TEST in config is still 1–30; **this publish used TEST seeds 1–5** after the lock

## Caveats

- PPO was trained to the config budget and is on disk. It was not scored on VALIDATION or TEST, so `rl_ppo` is absent from `raw_runs.csv` and the headline tables.
- The 2×2 grid was not scored in this publish. See the note in `results/grid_results.json`.
- Sublane: `results/sublane_fallback.json` records a 60 s one-vehicle probe with `used_sublane` true. Full-demand stability under that setting has not been re-run.
- Safety is SSM minTTC conflicts per 1000 departed vehicles; quote the verdict in `results/safety.json`.
- Fuel per vehicle includes departed vehicles that did not finish. Unfinished runs stay out of the paired headline.
- The headline baseline is the best of fixed_tuned, actuated, queue_pressure, and maxpressure. Legacy fixed is secondary.
- INR figures in the extrapolation are a placeholder.

## Not done in this publish

- Full TEST seeds 1–30
- VALIDATION scoring of PPO checkpoints and a TEST column for `rl_ppo`
- A working 2×2 grid sweep with per-junction TLS programs
