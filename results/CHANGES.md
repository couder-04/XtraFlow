# What changed

Simulation-based estimate; assumed traffic mix.

The corrected headline is the paired comparison in `results/headlines.json` after the locked TEST sweep is re-run. That sweep has not been run. `results/headlines.json` is still the pre-fix file. The pre-fix copy is `results/headlines_previous.json`. Do not quote either as the corrected result.

## What was actually re-run

- Unit tests, including a 60 s SUMO smoke per controller in `tests/test_hardening.py`.
- `experiments.sweep --smoke` on balanced, seed 1, nine controllers. Output is `results/raw_runs_smoke.csv`. It is not the TEST sweep.
- Sublane probe: 60 s, one vehicle, lateral resolution 0.4. `results/sublane_fallback.json` says `used_sublane` true.
- Demand calibration smoke: one VALIDATION seed, balanced, short horizon. `results/demand_calibration.json` has `"smoke": true`. Those veh/h figures are scaled from that short run.
- `fixed_tuned` smoke: two green plans, one VALIDATION seed, balanced only. `results/fixed_tuned.json` has `"smoke": true`.
- RL: the previous zip expected observation shape (14,) and Discrete(2). It is kept as `results/rl/ppo_best_obs14_discrete2.zip`. The zip at `results/rl/ppo_best.zip` is a 256-step smoke checkpoint. Config `rl.total_timesteps` is 200000 and was not trained. `results/rl/rl_selection.json` records `smoke: true`.
- Emission class map regenerated. Alternate bus is HBEFA3/HDV and alternate truck is HBEFA3/HDV_D_EU4. auto-rickshaw remains a passenger-car class.
- Config lock rewritten with relative paths. It hashes the smoke fixed plan and the smoke RL zip. Re-freeze after the real VALIDATION search and the config training budget.

## Claims removed

- Lateral resolution is not claimed unless `results/sublane_fallback.json` says the probe ran.
- Safety is not described as all zeros, and it is not described as "did not rise" unless the interval in `results/safety.json` says `decrease` or `no detectable change`.
- The grid is not described from the old figure. Quote `results/grid_results.json` only after a run that uses per-junction groups.
- The headline is not the gap versus the legacy equal-green plan, and that gap is not called the upper end of a plausible range.
- RL is not described as a fixed percent better than PPO. It is a baseline trained with the budget in `results/rl/rl_selection.json`.
- Detector-miss curves are not described as flat, and a missed vehicle is not described as leaving the saving intact, unless the loaded robustness rows say that.
- Degree of saturation is not stated as 70–90%. It is the measured field in `results/demand_calibration.json`, or it is absent.
- HBEFA4 is not the primary model. Config and `results/emission_class_map.json` name HBEFA3.
- Emission cross-check does not map bus and truck to a passenger car.
- INR figures stay a placeholder.

## Code corrections that change the numbers

- Perception misses are a per-vehicle Markov burst, seeded from the run, and count jitter is applied.
- SSM counts `<conflict>` elements whose `minTTC` value is below the threshold, per 1000 departed vehicles.
- Fuel per vehicle divides by departed vehicles and includes unfinished trips.
- Crashes are `status=error`. Unfinished runs stay out of the paired headline.
- `fixed_tuned` is selected on VALIDATION. Queue-pressure and max-pressure are separate controllers.
- Webster reads measured VALIDATION flows.
- The config lock is created by `make freeze_config` and the sweep only checks it.
