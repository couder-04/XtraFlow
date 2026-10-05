# STATE.md — XtraFlow

Last updated: 2026-10-05

## What this study is

Simulation-based estimate. The traffic mix is assumed. Controllers default to an oracle detector (SUMO speed, class, and route turn). Emission classes are proxies: auto-rickshaw uses a passenger-car class, two-wheeler uses LDV_G_EU4 when that class loads. Nothing here is a field result.

## Seed protocol

- TRAIN 1000–1049
- VALIDATION 2000–2019 (tuning, fixed-plan search, RL checkpoint)
- TEST 1–30 once, after `make freeze_config`

## Caveats

- `results/sublane_fallback.json` records `used_sublane` true after a 60 s, one-vehicle probe at lateral resolution 0.4. Full-demand stability under that setting has not been re-run.
- Safety counts are SSM minTTC conflicts per 1000 departed vehicles. The verdict string is the sign of the bootstrap interval in `results/safety.json`.
- Fuel per vehicle includes departed vehicles that did not finish. Runs with `n_unfinished > 0` stay in the tables and stay out of the paired headline.
- Crashes are `status=error`, not gridlock. A sweep with error rows fails.
- The headline baseline is the best of fixed_tuned, actuated, queue_pressure, and maxpressure. Legacy fixed is secondary.
- The grid claim is whatever `results/grid_results.json` contains after a run that uses per-junction groups. Do not quote an older grid figure.
- The noise model `source` is `assumed` until paired labels exist. The deck has to say so.
- RL is a baseline trained with the budget in `results/rl/rl_selection.json`. A missing `ppo_best.zip` is an error, not an always-keep policy.
- INR figures in the extrapolation are a placeholder. Scenario weights are an assumption in config.yaml.

## Still to re-run before quoting numbers

Networks (if the sublane probe has not been written), weights, demand calibration, tune, fixed_tuned, RL training at the config budget, freeze, one TEST sweep, then analyze, robustness, sensitivity, emission cross-check, safety, grid, extrapolate, demo, deck, audit.
