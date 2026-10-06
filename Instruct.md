# Two-MacBook split

This split is not the active run. The study is running on this Mac only. The coarse fixed-green screen is 900 seconds. Finalist plans are still scored on the full 3600 seconds.

Machine A is this Mac. Machine B is the other M4. Both stay plugged in, lids open, and awake until that machine's command prints that it finished.

Already finished on A. Do not run these again:

- Networks and idle-fuel weights
- Demand calibration (`results/demand_calibration.json`, validation, not smoke)
- Controller tuning (`results/tuned_params.json`)
- Balanced fixed-green plan, saved in `results/shards/fixed_tuned_balanced.json`  
  Greens `[25, 15, 20, 15]`

The single long job that was running peak unbalanced has been stopped. Peak starts over on A. That scenario had only just begun.

Replace `USER` and `MAC_B` with the login and hostname of the other Mac (System Settings → General → Sharing → Local hostname).

## Phase 1 — fixed-green search (start both now)

A runs the slow scenario. B runs the other two. About 6 hours.

### Machine A

```bash
cd ~/code_playground/XtraFlow
source .venv/bin/activate
export PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p results/raw results/shards
caffeinate -dims .venv/bin/python -m experiments.fixed_tuned \
  --scenarios peak_unbalanced --workers 8 \
  --out results/shards/fixed_tuned_peak.json \
  2>&1 | tee results/raw/phase7_a_peak.log
```

### Machine B, one-time setup

On A:

```bash
cd ~/code_playground/XtraFlow
rsync -a --delete \
  --exclude '.venv/' \
  --exclude 'results/raw/' \
  --exclude 'results/rl/' \
  --exclude 'results/raw_runs.csv' \
  --exclude 'results/raw_runs_smoke.csv' \
  ./ USER@MAC_B:~/code_playground/XtraFlow/
```

On B:

```bash
cd ~/code_playground/XtraFlow
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
.venv/bin/python -c "import sumolib,traci; print('sumo ok')"
export PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p results/raw results/shards
caffeinate -dims .venv/bin/python -m experiments.fixed_tuned \
  --scenarios dynamic low_demand --workers 8 \
  --out results/shards/fixed_tuned_dyn_low.json \
  2>&1 | tee results/raw/phase7_b_fixed.log
```

Wait until A has written `results/shards/fixed_tuned_peak.json` and B has written `results/shards/fixed_tuned_dyn_low.json`.

## Phase 2 — merge, train RL, freeze (A only)

B waits during this phase. About 2 hours, one SUMO environment.

On B, send the file back:

```bash
scp ~/code_playground/XtraFlow/results/shards/fixed_tuned_dyn_low.json \
  USER@MAC_A:~/code_playground/XtraFlow/results/shards/
```

On A:

```bash
cd ~/code_playground/XtraFlow
source .venv/bin/activate
export PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
.venv/bin/python -m experiments.fixed_tuned --merge \
  results/shards/fixed_tuned_balanced.json \
  results/shards/fixed_tuned_peak.json \
  results/shards/fixed_tuned_dyn_low.json \
  --out results/fixed_tuned.json
.venv/bin/python -c "import json; p=json.load(open('results/fixed_tuned.json')); assert not p['smoke']; assert set(p['plans'])=={'balanced','peak_unbalanced','dynamic','low_demand'}; print('fixed_tuned merged', {k:v['greens'] for k,v in p['plans'].items()})"
caffeinate -dims .venv/bin/python -m experiments.train_rl \
  2>&1 | tee results/raw/phase7_a_rl.log
.venv/bin/python -c "from sim.util import freeze_config; freeze_config(); print('freeze_config ok')"
test ! -f results/rl/rl_selection.json || .venv/bin/python -c "import json; m=json.load(open('results/rl/rl_selection.json')); assert m.get('smoke') is False; assert m.get('timesteps_budget')==200000; print(m.get('sha256'))"
```

`results/fixed_tuned.json` must list all four scenarios and `"smoke": false`. `results/rl/rl_selection.json` must show 200000 steps and `"smoke": false`.

## Phase 3 — TEST sweep (both)

Copy the lock and the RL model to B before either sweep starts. On A:

```bash
cd ~/code_playground/XtraFlow
rsync -a config.yaml USER@MAC_B:~/code_playground/XtraFlow/config.yaml
rsync -a results/config.lock results/fixed_tuned.json results/tuned_params.json \
  results/weights.json results/demand_calibration.json results/emission_class_map.json \
  USER@MAC_B:~/code_playground/XtraFlow/results/
ssh USER@MAC_B 'mkdir -p ~/code_playground/XtraFlow/results/rl'
rsync -a results/rl/ppo_best.zip results/rl/rl_selection.json \
  USER@MAC_B:~/code_playground/XtraFlow/results/rl/
```

Archive the old pre-fix sweep on A so the new sweep does not resume it. On A and on B:

```bash
cd ~/code_playground/XtraFlow
mkdir -p results/raw
if [ -f results/raw_runs.csv ]; then
  mv results/raw_runs.csv results/raw/raw_runs_pre_split.csv
fi
```

### Machine A — 5 controllers, 600 runs

```bash
cd ~/code_playground/XtraFlow
source .venv/bin/activate
export PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
caffeinate -dims .venv/bin/python -m experiments.sweep --workers 8 \
  --controllers fixed fixed_tuned webster actuated queue_pressure \
  2>&1 | tee results/raw/phase7_a_sweep.log
```

### Machine B — 4 controllers, 480 runs

```bash
cd ~/code_playground/XtraFlow
source .venv/bin/activate
export PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
caffeinate -dims .venv/bin/python -m experiments.sweep --workers 8 \
  --controllers maxpressure ours_count XtraFlow rl_ppo \
  2>&1 | tee results/raw/phase7_b_sweep.log
```

About 2–2.5 hours. Seeds are 1–30 and all four scenarios on both machines. The controller lists must not overlap.

## Phase 4 — other studies (both, after both sweeps finish)

These do not read each other's files.

### Machine A

```bash
cd ~/code_playground/XtraFlow
source .venv/bin/activate
export PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
caffeinate -dims .venv/bin/python -m experiments.robustness \
  2>&1 | tee results/raw/phase7_a_robustness.log
caffeinate -dims .venv/bin/python -m experiments.grid_sweep \
  2>&1 | tee results/raw/phase7_a_grid.log
```

### Machine B

```bash
cd ~/code_playground/XtraFlow
source .venv/bin/activate
export PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
caffeinate -dims .venv/bin/python -m experiments.emission_xcheck \
  2>&1 | tee results/raw/phase7_b_emission.log
caffeinate -dims .venv/bin/python -m experiments.sensitivity \
  2>&1 | tee results/raw/phase7_b_sensitivity.log
```

## Phase 5 — combine on A, then finish

On A, create the incoming folders:

```bash
mkdir -p ~/code_playground/XtraFlow/results/from_b ~/code_playground/XtraFlow/results/figures
```

On B:

```bash
cd ~/code_playground/XtraFlow
scp results/raw_runs.csv USER@MAC_A:~/code_playground/XtraFlow/results/from_b/raw_runs.csv
scp results/emission_xcheck.json USER@MAC_A:~/code_playground/XtraFlow/results/emission_xcheck.json
scp results/sensitivity.json USER@MAC_A:~/code_playground/XtraFlow/results/sensitivity.json
scp results/figures/vi_gain_vs_saturation.png USER@MAC_A:~/code_playground/XtraFlow/results/figures/
```

On A, merge the two sweep CSVs. A's file is `results/raw_runs.csv`. B's copy is `results/from_b/raw_runs.csv`.

```bash
cd ~/code_playground/XtraFlow
source .venv/bin/activate
.venv/bin/python - << 'PY'
import csv
from pathlib import Path
from sim.run_sim import RAW_FIELDS

a = Path("results/raw_runs.csv")
b = Path("results/from_b/raw_runs.csv")
rows = []
seen = set()
for path in (a, b):
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if list(reader.fieldnames) != list(RAW_FIELDS):
            raise SystemExit(f"schema mismatch: {path}")
        for row in reader:
            key = (row["scenario"], row["controller"], row["seed"], row["emission_model"])
            if key in seen:
                raise SystemExit(f"duplicate {key}")
            seen.add(key)
            rows.append(row)
out = Path("results/raw_runs.csv")
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(RAW_FIELDS), extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
print(f"merged {len(rows)} rows")
need = {
    "fixed", "fixed_tuned", "webster", "actuated", "queue_pressure",
    "maxpressure", "ours_count", "XtraFlow", "rl_ppo",
}
have = {r["controller"] for r in rows}
missing = need - have
if missing:
    raise SystemExit(f"missing controllers: {missing}")
PY
.venv/bin/python -m experiments.analyze
.venv/bin/python -m experiments.safety
.venv/bin/python -m experiments.extrapolate
.venv/bin/python -m perception.evaluate_detector
.venv/bin/python -m demo.make_demo
.venv/bin/python -m deck.build_deck
.venv/bin/python -m tools.audit
.venv/bin/python -m pytest tests/ -q --tb=line
```

Analyze, safety, the report, figures, the deck, the audit, and pytest run only on A, after the merge. Commit and push from A after pytest is clean.

## Rules

- TEST seeds 1–30 run only in phase 3, after `freeze_config` on A.
- Do not freeze on B.
- Do not train a second RL model on B.
- Do not copy B's `raw_runs.csv` onto A's `results/raw_runs.csv`. It goes to `results/from_b/raw_runs.csv`.
- The old `results/raw_runs.csv` is a pre-fix sweep. Phase 3 moves it aside. Do not merge it back in.
