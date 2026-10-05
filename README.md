# XtraFlow

Fuel-weighted traffic signals. Reproducible SUMO study for an IndianOil presentation.

**Label:** Simulation-based estimate; not a real-world deployment result.  
**Traffic mix:** assumed mixed-traffic scenario unless you supply observed counts.

![Same demand, fixed time beside XtraFlow](results/demo/demo.gif)

## Results

Test seeds 1–30, after the config lock. Fuel per completed vehicle versus fixed time:

![Percent fuel reduction of XtraFlow versus fixed time, with bootstrap 95% intervals](results/figures/ii_pct_reduction.png)

Fuel, CO₂, waiting, and queue for every controller:

![Mean fuel, CO2, waiting time, and queue by scenario and controller](results/figures/i_grouped_bars.png)

The fuel saving holds when the detector misses vehicles (peak scenario):

![Fuel per vehicle as the detection miss rate rises from 0 to 30 percent](results/figures/vii_robustness.png)

On a 2×2 grid the same controller uses more fuel than fixed time and actuated. Coordination does not change that:

![Mean fuel per vehicle on the 2x2 grid](results/figures/x_grid_results.png)

## One-command reproduction

```bash
python3.12 -m venv .venv
source .venv/bin/activate
make setup
make all
```

Or with Docker:

```bash
docker build -t xtraflow .
docker run --rm -v "$PWD/results:/app/results" xtraflow
```

## Expected runtime


| Stage                          | Approx.                |
| ------------------------------ | ---------------------- |
| setup + networks + pytest      | 10–20 min              |
| smoke (7 controllers)          | 5–15 min               |
| calibrate + tune (VALIDATION)  | 1–3 h                  |
| train_rl                       | 2–8 h                  |
| TEST sweep (7×4×30)            | 8–20 h (CPU-dependent) |
| analyze + extras + demo + deck | 1–3 h                  |




## Folder guide

- `sim/` — network, demand, controllers, RL env, metrics
- `experiments/` — calibrate, tune, train, sweep, analyze, robustness, …
- `perception/` — YOLO counting + noise model
- `demo/` — side-by-side MP4 + Streamlit dashboard
- `deck/` — auto-filled pptx
- `results/` — raw_runs.csv, summary.json, figures, REPORT.md, deck.pptx
- `docs/DECISIONS.md` — design choices
- `STATE.md` — pipeline checklist / resume point



## Seed protocol

- TRAIN `1000–1049` (RL only)
- VALIDATION `2000–2019` (tuning / model selection)
- TEST `1–30` (once, after `results/config.lock`)



## Supply real video and counts

1. Place videos in `data/video/`
2. Place manual counts/boxes in `data/video_labels/`
3. `python -m perception.yolo_counts --video data/video/YOUR.mp4 --roi perception/roi.yaml`
4. `python -m perception.evaluate_detector` → writes `perception/noise_model.json`

For demand calibration: place `data/observed_counts.csv` with columns `approach,count_veh_h`.

**Licensing:** only use datasets you have rights to; do not download unlicensed content.

## Emission class mapping

Runtime probe writes `results/emission_class_map.json`. On `eclipse-sumo==1.21.0` the wheel provides **HBEFA3** and **PHEMlight** (not HBEFA4). Primary mapping uses HBEFA3; emission cross-check uses PHEMlight when available.

## Makefile targets

`setup test smoke calibrate tune train_rl sweep analyze robustness sensitivity emission_xcheck safety perception grid extrapolate demo dashboard deck report audit all`