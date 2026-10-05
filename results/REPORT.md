# AI-Based Smart Traffic & Fuel Optimization — Research Report

**Label:** Simulation-based estimate; not a real-world deployment result. Assumed mixed-traffic scenario unless observed counts provided.

## Abstract

We evaluate an adaptive, fuel-weighted pressure traffic signal controller (ours_fuel) against fixed-time, Webster, SUMO-actuated, max-pressure, count-only ablation, and PPO baselines under mixed Indian urban traffic in SUMO (left-hand traffic, sublane-capable). 
 On scenario `balanced`, mean fuel reduction vs fixed was 8.61% (95% CI [8.23, 9.00]; flag=OK).
 On scenario `dynamic`, mean fuel reduction vs fixed was 16.50% (95% CI [15.72, 17.31]; flag=OK).
 On scenario `low_demand`, mean fuel reduction vs fixed was 14.46% (95% CI [13.98, 14.91]; flag=OK).
 On scenario `peak_unbalanced`, mean fuel reduction vs fixed was 21.76% (95% CI [20.05, 23.54]; flag=OK).


## Method

- Single 4-arm intersection + 2×2 grid; left-hand traffic; yellow 3 s; all-red 2 s.

- Seed protocol: TRAIN 1000–1049, VALIDATION 2000–2019, TEST 1–30 after config.lock.

- Metrics from tripinfo with device.emissions.probability=1; fuel mg→L via densities.

- Sublane model used: False.

- Emission class map (primary): `{"two_wheeler": "HBEFA3/LDV_G_EU4", "auto_rickshaw": "HBEFA3/PC_G_EU4", "car": "HBEFA3/PC_G_EU4", "bus": "HBEFA3/Bus", "truck": "HBEFA3/HDV"}`.


## Assumptions

| Parameter | Value | Source |
|---|---|---|

| Vehicle mix | 2W 40 / car 30 / auto 10 / bus 5 / truck 15 | assumed |

| Occupancy | 1.3 / 2.0 / 2.0 / 40 / 1.2 | assumed |

| Fuel densities | petrol 0.74, diesel 0.84 kg/L | assumed |

| Geometry | 300 m approaches, 3 in / 2 out lanes | assumed |

| Demand mode | assumed_demand | data/observed_counts.csv absent; using assumed demand from config.yaml. Flows chosen so fixed-time sits near 70-90% degree of saturation at peak. |


## Weights (measured)

```

{
  "idle_fuel_mg_per_s": {
    "two_wheeler": 448.05555555555554,
    "auto_rickshaw": 837.2222222222223,
    "car": 837.2222222222223,
    "bus": 1671.1111111111109,
    "truck": 2321.6666666666665
  },
  "w_type": {
    "two_wheeler": 0.5351692103516921,
    "auto_rickshaw": 1.0,
    "car": 1.0,
    "bus": 1.9960185799601853,
    "truck": 2.77305905773059
  },
  "reference": "car",
  "duration_s": 60.0,
  "note": "Measured via TraCI getFuelConsumption while stopped; assumed emission classes."
}

```


## Tuned parameters (VALIDATION only)

```

{
  "detection_distance_m": 150,
  "alpha_moving": 0.5,
  "hysteresis": 0.25,
  "selected_on": "VALIDATION seeds only",
  "screen_seeds": [
    2000,
    2001,
    2002,
    2003,
    2004
  ],
  "confirm_seeds": [
    2000,
    2001,
    2002,
    2003,
    2004,
    2005,
    2006,
    2007,
    2008,
    2009,
    2010,
    2011,
    2012,
    2013,
    2014,
    2015,
    2016,
    2017,
    2018,
    2019
  ],
  "scenario": "peak_unbalanced",
  "mean_fuel_per_vehicle_L": 0.12318790645640529,
  "smoke": false
}

```


## Per-scenario results (mean±std)


| scenario        | controller   |   n |   fuel_per_vehicle_L_mean |   fuel_per_vehicle_L_std |   total_CO2_kg_mean |   total_CO2_kg_std |   mean_waiting_s_mean |   mean_waiting_s_std |   mean_queue_veh_mean |   mean_queue_veh_std |   n_completed_mean |   n_completed_std |   gridlock_flag_mean |   gridlock_flag_std |   ssm_conflicts_mean |   ssm_conflicts_std |
|:----------------|:-------------|----:|--------------------------:|-------------------------:|--------------------:|-------------------:|----------------------:|---------------------:|----------------------:|---------------------:|-------------------:|------------------:|---------------------:|--------------------:|---------------------:|--------------------:|
| balanced        | fixed        |  30 |                  0.141169 |               0.0029387  |             676.915 |           21.95    |               30.1199 |             1.19357  |              15.4526  |             0.721353 |             1919.6 |           43.0682 |            0         |            0        |                    0 |                   0 |
| balanced        | webster      |  30 |                  0.140806 |               0.00256028 |             675.5   |           22.2377  |               27.9368 |             0.890794 |              14.4473  |             0.663884 |             1919.6 |           43.0682 |            0         |            0        |                    0 |                   0 |
| balanced        | actuated     |  30 |                  0.136613 |               0.00215762 |             655.336 |           17.7491  |               25.8318 |             0.459819 |              13.396   |             0.382783 |             1919.6 |           43.0682 |            0         |            0        |                    0 |                   0 |
| balanced        | maxpressure  |  30 |                  0.130644 |               0.00267534 |             627.065 |           19.4875  |               22.0118 |             0.770722 |              11.4078  |             0.466555 |             1919.6 |           43.0682 |            0         |            0        |                    0 |                   0 |
| balanced        | ours_count   |  30 |                  0.129792 |               0.00267858 |             622.978 |           20.013   |               21.1584 |             0.653478 |              10.9655  |             0.431188 |             1919.6 |           43.0682 |            0         |            0        |                    0 |                   0 |
| balanced        | ours_fuel    |  30 |                  0.129    |               0.00213502 |             618.178 |           17.6256  |               21.8567 |             0.706788 |              11.3185  |             0.3722   |             1919.6 |           43.0682 |            0         |            0        |                    0 |                   0 |
| balanced        | rl_ppo       |  30 |                  0.140806 |               0.00256028 |             675.5   |           22.2377  |               27.9368 |             0.890794 |              14.4473  |             0.663884 |             1919.6 |           43.0682 |            0         |            0        |                    0 |                   0 |
| peak_unbalanced | fixed        |  30 |                  0.158392 |               0.0118207  |             710.049 |           56.5572  |               41.7973 |             8.06152  |              19.4241  |             3.26828  |             1796.2 |           32.4573 |            0         |            0        |                    0 |                   0 |
| peak_unbalanced | webster      |  30 |                  0.139037 |               0.00311075 |             624.035 |           17.8687  |               26.8579 |             0.960235 |              13.0146  |             0.543715 |             1796.2 |           32.4573 |            0         |            0        |                    0 |                   0 |
| peak_unbalanced | actuated     |  30 |                  0.136598 |               0.0028488  |             613.11  |           16.1261  |               25.455  |             0.551707 |              12.3482  |             0.363724 |             1796.2 |           32.4573 |            0         |            0        |                    0 |                   0 |
| peak_unbalanced | maxpressure  |  30 |                  0.124827 |               0.00282739 |             560.602 |           16.3713  |               18.5289 |             0.801428 |               8.99357 |             0.417676 |             1796.2 |           32.4573 |            0         |            0        |                    0 |                   0 |
| peak_unbalanced | ours_count   |  30 |                  0.124985 |               0.0026718  |             561.485 |           15.4614  |               17.8022 |             0.739012 |               8.64743 |             0.422874 |             1796.2 |           32.4573 |            0         |            0        |                    0 |                   0 |
| peak_unbalanced | ours_fuel    |  30 |                  0.123375 |               0.00246    |             553.292 |           15.0231  |               18.1187 |             0.624917 |               8.80502 |             0.372024 |             1796.2 |           32.4573 |            0         |            0        |                    0 |                   0 |
| peak_unbalanced | rl_ppo       |  30 |                  0.271187 |               0.046093   |            1142.56  |          198.797   |              113.353  |            30.3052   |              60.8703  |            21.3476   |             1698.6 |          124.162  |            0.5       |            0.508548 |                    0 |                   0 |
| dynamic         | fixed        |  30 |                  0.149025 |               0.00546442 |             654.469 |           30.2466  |               35.5058 |             2.82236  |              16.4629  |             1.30483  |             1759.2 |           36.5885 |            0         |            0        |                    0 |                   0 |
| dynamic         | webster      |  30 |                  0.168141 |               0.0281838  |             738.216 |          122.45    |               46.2875 |            19.4124   |              21.3374  |             6.37385  |             1759.2 |           36.5885 |            0         |            0        |                    0 |                   0 |
| dynamic         | actuated     |  30 |                  0.13649  |               0.00258493 |             600.068 |           17.9222  |               25.4648 |             0.487867 |              12.112   |             0.343319 |             1759.2 |           36.5885 |            0         |            0        |                    0 |                   0 |
| dynamic         | maxpressure  |  30 |                  0.125129 |               0.00276454 |             550.443 |           18.2357  |               18.7768 |             0.601557 |               8.92663 |             0.355655 |             1759.2 |           36.5885 |            0         |            0        |                    0 |                   0 |
| dynamic         | ours_count   |  30 |                  0.125085 |               0.00282584 |             550.338 |           18.6845  |               18.0982 |             0.553457 |               8.60387 |             0.352087 |             1759.2 |           36.5885 |            0         |            0        |                    0 |                   0 |
| dynamic         | ours_fuel    |  30 |                  0.12434  |               0.00277639 |             546.049 |           18.6438  |               18.9957 |             0.913776 |               9.03525 |             0.498367 |             1759.2 |           36.5885 |            0         |            0        |                    0 |                   0 |
| dynamic         | rl_ppo       |  30 |                  0.179564 |               0.0182211  |             786.25  |           82.4286  |               53.4149 |            11.8556   |              25.5582  |             9.27232  |             1755   |           38.2262 |            0.0333333 |            0.182574 |                    0 |                   0 |
| low_demand      | fixed        |  30 |                  0.134646 |               0.0041531  |             201.852 |           10.3253  |               27.2516 |             1.18588  |               4.4181  |             0.23784  |              599.8 |           24.0106 |            0         |            0        |                    0 |                   0 |
| low_demand      | webster      |  30 |                  0.132008 |               0.00415294 |             197.986 |           10.6006  |               24.1058 |             0.879206 |               3.92553 |             0.254691 |              599.8 |           24.0106 |            0         |            0        |                    0 |                   0 |
| low_demand      | actuated     |  30 |                  0.130663 |               0.00418988 |             195.88  |            9.57219 |               23.4617 |             0.931351 |               3.81008 |             0.208033 |              599.8 |           24.0106 |            0         |            0        |                    0 |                   0 |
| low_demand      | maxpressure  |  30 |                  0.117315 |               0.00375983 |             176.087 |            9.76869 |               15.4504 |             0.931256 |               2.52077 |             0.205702 |              599.8 |           24.0106 |            0         |            0        |                    0 |                   0 |
| low_demand      | ours_count   |  30 |                  0.118236 |               0.00420807 |             177.417 |            9.53385 |               15.1824 |             0.961428 |               2.47884 |             0.186092 |              599.8 |           24.0106 |            0         |            0        |                    0 |                   0 |
| low_demand      | ours_fuel    |  30 |                  0.115168 |               0.00362755 |             172.216 |            9.26048 |               15.9156 |             0.955137 |               2.60169 |             0.212963 |              599.8 |           24.0106 |            0         |            0        |                    0 |                   0 |
| low_demand      | rl_ppo       |  30 |                  0.132008 |               0.00415294 |             197.986 |           10.6006  |               24.1058 |             0.879206 |               3.92553 |             0.254691 |              599.8 |           24.0106 |            0         |            0        |                    0 |                   0 |


## Statistical tests (ours_fuel vs baselines)


| scenario        | baseline    | metric             |   pct_reduction_mean |   pct_reduction_ci_lo |   pct_reduction_ci_hi |   wilcoxon_stat |       p_raw |   cohens_dz |   n_pairs |      p_holm |
|:----------------|:------------|:-------------------|---------------------:|----------------------:|----------------------:|----------------:|------------:|------------:|----------:|------------:|
| balanced        | fixed       | fuel_per_vehicle_L |             8.60644  |              8.22502  |              8.99744  |               0 | 1.86265e-09 |   -7.05272  |        30 | 4.47035e-08 |
| balanced        | webster     | fuel_per_vehicle_L |             8.37264  |              7.9115   |              8.84512  |               0 | 1.86265e-09 |   -5.94868  |        30 | 4.47035e-08 |
| balanced        | actuated    | fuel_per_vehicle_L |             5.569    |              5.24303  |              5.89154  |               0 | 1.86265e-09 |   -5.84537  |        30 | 4.47035e-08 |
| balanced        | maxpressure | fuel_per_vehicle_L |             1.24649  |              0.901382 |              1.60427  |              14 | 2.04891e-07 |   -1.24561  |        30 | 1.43424e-06 |
| balanced        | ours_count  | fuel_per_vehicle_L |             0.59857  |              0.276763 |              0.943536 |              84 | 0.00158328  |   -0.628937 |        30 | 0.00474985  |
| balanced        | rl_ppo      | fuel_per_vehicle_L |             8.37264  |              7.9115   |              8.84512  |               0 | 1.86265e-09 |   -5.94868  |        30 | 4.47035e-08 |
| dynamic         | fixed       | fuel_per_vehicle_L |            16.5005   |             15.7215   |             17.3068   |               0 | 1.86265e-09 |   -5.88864  |        30 | 4.47035e-08 |
| dynamic         | webster     | fuel_per_vehicle_L |            24.7916   |             22.3321   |             27.9838   |               0 | 1.86265e-09 |   -1.57466  |        30 | 4.47035e-08 |
| dynamic         | actuated    | fuel_per_vehicle_L |             8.90099  |              8.49399  |              9.30014  |               0 | 1.86265e-09 |   -7.54931  |        30 | 4.47035e-08 |
| dynamic         | maxpressure | fuel_per_vehicle_L |             0.624322 |              0.219586 |              1.0281   |             105 | 0.00761214  |   -0.539318 |        30 | 0.00806359  |
| dynamic         | ours_count  | fuel_per_vehicle_L |             0.590258 |              0.258025 |              0.954554 |              96 | 0.00403179  |   -0.59719  |        30 | 0.00806359  |
| dynamic         | rl_ppo      | fuel_per_vehicle_L |            30.1643   |             28.0346   |             32.3621   |               0 | 1.86265e-09 |   -3.10167  |        30 | 4.47035e-08 |
| low_demand      | fixed       | fuel_per_vehicle_L |            14.4582   |             13.9839   |             14.9079   |               0 | 1.86265e-09 |   -9.79892  |        30 | 4.47035e-08 |
| low_demand      | webster     | fuel_per_vehicle_L |            12.741    |             12.1536   |             13.358    |               0 | 1.86265e-09 |   -6.66068  |        30 | 4.47035e-08 |
| low_demand      | actuated    | fuel_per_vehicle_L |            11.8417   |             11.2361   |             12.4384   |               0 | 1.86265e-09 |   -6.37297  |        30 | 4.47035e-08 |
| low_demand      | maxpressure | fuel_per_vehicle_L |             1.81716  |              1.25765  |              2.35725  |              22 | 9.98378e-07 |   -1.17635  |        30 | 4.16301e-06 |
| low_demand      | ours_count  | fuel_per_vehicle_L |             2.5738   |              2.10363  |              3.02517  |               2 | 5.58794e-09 |   -1.88426  |        30 | 4.47035e-08 |
| low_demand      | rl_ppo      | fuel_per_vehicle_L |            12.741    |             12.1536   |             13.358    |               0 | 1.86265e-09 |   -6.66068  |        30 | 4.47035e-08 |
| peak_unbalanced | fixed       | fuel_per_vehicle_L |            21.7596   |             20.0481   |             23.5385   |               0 | 1.86265e-09 |   -3.21574  |        30 | 4.47035e-08 |
| peak_unbalanced | webster     | fuel_per_vehicle_L |            11.2536   |             10.8826   |             11.6369   |               0 | 1.86265e-09 |   -9.17751  |        30 | 4.47035e-08 |
| peak_unbalanced | actuated    | fuel_per_vehicle_L |             9.67431  |              9.3721   |              9.98495  |               0 | 1.86265e-09 |  -10.0638   |        30 | 4.47035e-08 |
| peak_unbalanced | maxpressure | fuel_per_vehicle_L |             1.15304  |              0.820211 |              1.49334  |              17 | 3.85568e-07 |   -1.19057  |        30 | 2.31341e-06 |
| peak_unbalanced | ours_count  | fuel_per_vehicle_L |             1.27991  |              0.9015   |              1.64624  |              21 | 8.32602e-07 |   -1.18112  |        30 | 4.16301e-06 |
| peak_unbalanced | rl_ppo      | fuel_per_vehicle_L |            53.3305   |             50.6473   |             55.8845   |               0 | 1.86265e-09 |   -3.25268  |        30 | 4.47035e-08 |



## Where ours_fuel loses or ties


No non-positive mean fuel reductions found against listed baselines in loaded runs.


## Ablations


| scenario        |   pct_reduction_fuel_vs_count_mean |    ci_lo |    ci_hi |
|:----------------|-----------------------------------:|---------:|---------:|
| balanced        |                           0.59857  | 0.276763 | 0.943536 |
| dynamic         |                           0.590258 | 0.258025 | 0.954554 |
| low_demand      |                           2.5738   | 2.10363  | 3.02517  |
| peak_unbalanced |                           1.27991  | 0.9015   | 1.64624  |



## RL comparison


RL selected on VALIDATION: `{"selected_on": "VALIDATION seeds", "confirm_seeds": [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019], "best_path": "/Users/par_04/code_playground/energy_hackathon/results/rl/ppo_best.zip", "best_val_fuel_per_vehicle_L": 0.14054192781091826, "fuels": [0.13778186558313338, 0.14475136100664854, 0.1422604947379443, 0.13727005318522195, 0.1387308904741657, 0.13832981558301768, 0.13630073085460376, 0.1388412717943669, 0.14070995857927754, 0.1420681128651021, 0.14339000560338883, 0.14726891456061725, 0.14077461501748376, 0.14176600660923588, 0.1395943082612321, 0.14027819270704772, 0.13823100367183688, 0.1428328530378117, 0.14232536536795087, 0.1373327367182782]}`.

| scenario        | baseline   | metric             |   pct_reduction_mean |   pct_reduction_ci_lo |   pct_reduction_ci_hi |   wilcoxon_stat |       p_raw |   cohens_dz |   n_pairs |      p_holm |
|:----------------|:-----------|:-------------------|---------------------:|----------------------:|----------------------:|----------------:|------------:|------------:|----------:|------------:|
| balanced        | rl_ppo     | fuel_per_vehicle_L |              8.37264 |                7.9115 |               8.84512 |               0 | 1.86265e-09 |    -5.94868 |        30 | 4.47035e-08 |
| dynamic         | rl_ppo     | fuel_per_vehicle_L |             30.1643  |               28.0346 |              32.3621  |               0 | 1.86265e-09 |    -3.10167 |        30 | 4.47035e-08 |
| low_demand      | rl_ppo     | fuel_per_vehicle_L |             12.741   |               12.1536 |              13.358   |               0 | 1.86265e-09 |    -6.66068 |        30 | 4.47035e-08 |
| peak_unbalanced | rl_ppo     | fuel_per_vehicle_L |             53.3305  |               50.6473 |              55.8845  |               0 | 1.86265e-09 |    -3.25268 |        30 | 4.47035e-08 |



## Sensitivity

```
{
  "rows": [
    {
      "kind": "demand_mult",
      "mult": 0.5,
      "controller": "fixed",
      "seed": 1,
      "fuel_per_vehicle_L": 0.1340920127897403,
      "mean_waiting_s": 28.19453207150368
    },
    {
      "kind": "demand_mult",
      "mult": 0.5,
      "controller": "ours_fuel",
      "seed": 1,
      "fuel_per_vehicle_L": 0.11898033791396488,
      "mean_waiting_s": 18.19558359621451
    },
    {
      "kind": "demand_mult",
      "mult": 0.5,
      "controller": "fixed",
      "seed": 2,
      "fuel_per_vehicle_L": 0.1332660070053294,
      "mean_waiting_s": 28.19468085106383
    },
    {
      "kind": "demand_mult",
      "mult": 0.5,
      "controller": "ours_fuel",
      "seed": 2,
      "fuel_per_vehicle_L": 0.11697579378665464,
      "mean_waiting_s": 18.28404255319149
    },
    {
      "kind": "demand_mult",
      "mult": 0.5,
      "controller": "fixed",
      "seed": 3,
      "fuel_per_vehicle_L": 0.131196206202634,
      "mean_waiting_s": 27.13936170212766
    },
    {
      "kind": "demand_mult",
      "mult": 0.5,
      "controller": "ours_fuel",
      "seed": 3,
      "fuel_per_vehicle_L": 0.11981457837031627,
      "mean_waiting_s": 18.961702127659574
    },
    {
      "kind": "demand_mult",
      "mult": 0.5,
      "controller": "fixed",
      "seed": 4,
      "fuel_per_vehicle_L": 0.1368575661966303,
      "mean_waiting_s": 27.9188376753507
    },
    {
      "kind": "demand_mult",
      "mult": 0.5,
      "controller": "ours_fuel",
      "seed": 4,
      "fuel_per_vehicle_L": 0.1239293863855108,
      "mean_waiting_s": 20.52304609218437
    },
    {
      "kind": "demand_mult",
      "mult": 0.5,
      "controller": "fixed",
      "seed": 5,
      "fuel_per_vehicle_L": 0.13469280452392998,
      "mean_waiting_s": 27.922600619195048
    },
    {
      "kind": "demand_mult",
      "mult": 0.5,
      "controller": "ours_fuel",
      "seed": 5,
      "fuel_per_vehicle_L": 0.1193586822611547,
      "mean_waiting_s": 17.977296181630546
    },
    {
      "kind": "demand_mult",
      "mult": 0.75,
      "controller": "fixed",
      "seed": 1,
      "fuel_per_vehicle_L": 0.14319508042437418,
      "mean_waiting_s": 27.844889206576127
    },
    {
      "kind": "demand_mult",
      "mult": 0.75,
      "controller": "ours_fuel",
      "seed": 1,
      "fuel_per_vehicle_L": 0.12798327587257172,
      "mean_waiting_s": 19.04288777698356
    },
    {
      "kind": "demand_mult",
      "mult": 0.75,
      "controller": "fixed",
      "seed": 2,
      "fuel_per_vehicle_L": 0.13807183605801504,
      "mean_waiting_s": 28.80516759776536
    },
    {
      "kind": "demand_mult",
      "mult": 0.75,
      "controller": "ours_fuel",
      "seed": 2,
      "fuel_per_vehicle_L": 0.12757366243696558,
      "mean_waiting_s": 20.88896648044693
    },
    {
      "kind": "demand_mult",
      "mult": 0.75,
      "controller": "fixed",
      "seed": 3,
      "fuel_per_vehicle_L": 0.14145490024528945,
      "mean_waiting_s": 29.2534435261708
    },
    {
      "kind": "demand_mult",
      "mult": 0.75,
      "controller": "ours_fuel",
      "seed": 3,
      "fuel_per_vehicle_L": 0.12885533920528958,
      "mean_waiting_s": 20.922865013774103
    },
    {
      "kind": "demand_mult",
      "mult": 0.75,
      "controller": "fixed",
      "seed": 4,
      "fuel_per_vehicle_L": 0.13622520865999513,
      "mean_waiting_s": 28.63528591352859
    },
    {
      "kind": "demand_mult",
      "mult": 0.75,
      "controller": "ours_fuel",
      "seed": 4,
      "fuel_per_vehicle_L": 0.12549268634186347,
      "mean_waiting_s": 20.880753138075313
    },
    {
      "kind": "demand_mult",
      "mult": 0.75,
      "controller": "fixed",
      "seed": 5,
      "fuel_per_vehicle_L": 0.13675487514407444,
      "mean_waiting_s": 27.07284299858557
    },
    {
      "kind": "demand_mult",
      "mult": 0.75,
      "controller": "ours_fuel",
      "seed": 5,
      "fuel_per_vehicle_L": 0.12648845687127203,
      "mean_waiting_s": 21.075671852899575
    },
    {
      "kind": "demand_mult",
      "mult": 1.0,
      "controller": "fixed",
      "seed": 1,
      "fuel_per_vehicle_L": 0.1408789939783435,
      "mean_waiting_s": 30.653072033898304
    },
    {
      "kind": "demand_mult",
      "mult": 1.0,
      "controller": "ours_fuel",
      "seed": 1,
      "fuel_per_vehicle_L": 0.12960714537091242,
      "mean_waiting_s": 23.14936440677966
    },
    {
      "kind": "demand_mult",
      "mult": 1.0,
      "controller": "fixed",
      "seed": 2,
      "fuel_per_vehicle_L": 0.14222775663220727,
      "mean_waiting_s": 29.111053450960043
    },
    {
      "kind": "demand_mult",
      "mult": 1.0,
      "controller": "ours_fuel",
      "seed": 2,
      "fuel_per_vehicle_L": 0.1292250013288761,
      "mean_waiting_s": 21.080435910742086
    },
    {
      "kind": "demand_mult",
      "mult": 1.0,
      "controller": "fixed",
      "seed": 3,
      "fuel_per_vehicle_L": 0.145543171289666,
      "mean_waiting_s": 31.563287947554212
    },
    {
      "kind": "demand_mult",
      "mult": 1.0,
      "controller": "ours_fuel",
      "seed": 3,
      "fuel_per_vehicle_L": 0.1328204821189694,
      "mean_waiting_s": 22.157337367624812
    },
    {
      "kind": "demand_mult",
      "mult": 1.0,
      "controller": "fixed",
      "seed": 4,
      "fuel_per_vehicle_L": 0.14688927368248983,
      "mean_waiting_s": 31.360798362333675
    },
    {
      "kind": "demand_mult",
      "mult": 1.0,
      "controller": "ours_fuel",
      "seed": 4,
      "fuel_per_vehicle_L": 0.13099166338867016,
      "mean_waiting_s": 20.921187308085976
    },
    {
      "kind": "demand_mult",
      "mult": 1.0,
      "controller": "fixed",
      "seed": 5,
      "fuel_per_vehicle_L": 0.13738750439132089,
      "mean_waiting_s": 28.853326348873757
    },
    {
      "kind": "demand_mult",
      "mult": 1.0,
      "controller": "ours_fuel",
      "seed": 5,
      "fuel_per_vehicle_L": 0.1278548323827615,
      "mean_waiting_s": 21.400209533787322
    },
    {
      "kind": "demand_mult",
      "mult": 1.25,
      "controller": "fixed",
      "seed": 1,
      "fuel_per_vehicle_L": 0.15170727398215952,
      "mean_waiting_s": 36.68561872909699
    },
    {
      "kind": "demand_mult",
      "mult": 1.25,
      "controller": "ours_fuel",
      "seed": 1,
      "fuel_per_vehicle_L": 0.13702236997625922,
      "mean_waiting_s": 26.835284280936456
    },
    {
      "kind": "demand_mult",
      "mult": 1.25,
      "controller": "fixed",
      "seed": 2,
      "fuel_per_vehicle_L": 0.1494513605464451,
      "mean_waiting_s": 36.088003320880034
    },
    {
      "kind": "demand_mult",
      "mult": 1.25,
      "controller": "ours_fuel",
      "seed": 2,
      "fuel_per_vehicle_L": 0.1340184861046731,
      "mean_waiting_s": 24.33167289331673
    },
    {
      "kind": "demand_mult",
      "mult": 1.25,
      "controller": "fixed",
      "seed": 3,
      "fuel_per_vehicle_L": 0.15389388848122962,
      "mean_waiting_s": 37.312197092084006
    },
    {
      "kind": "demand_mult",
      "mult": 1.25,
      "controller": "ours_fuel",
      "seed": 3,
      "fuel_per_vehicle_L": 0.1379412607020046,
      "mean_waiting_s": 25.299273021001614
    },
    {
      "kind": "demand_mult",
      "mult": 1.25,
      "controller": "fixed",
      "seed": 4,
      "fuel_per_vehicle_L": 0.16506826130067778,
      "mean_waiting_s": 46.54047322540473
    },
    {
      "kind": "demand_mult",
      "mult": 1.25,
      "controller": "ours_fuel",
      "seed": 4,
      "fuel_per_vehicle_L": 0.1403361810459649,
      "mean_waiting_s": 28.46367787463678
    },
    {
      "kind": "demand_mult",
      "mult": 1.25,
      "controller": "fixed",
      "seed": 5,
      "fuel_per_vehicle_L": 0.14076554323708054,
      "mean_waiting_s": 31.671075085324233
    },
    {
      "kind": "demand_mult",
      "mult": 1.25,
      "controller": "ours_fuel",
      "seed": 5,
      "fuel_per_vehicle_L": 0.12935548832454338,
      "mean_waiting_s": 23.113054607508534
    },
    {
      "kind": "demand_mult",
      "mult": 1.5,
      "controller": "fixed",
      "seed": 1,
      "fuel_per_vehicle_L": 0.16221066020199823,
      "mean_waiting_s": 44.3966303966304
    },
    {
      "kind": "demand_mult",
      "mult": 1.5,
      "controller": "ours_fuel",
      "seed": 1,
      "fuel_per_vehicle_L": 0.14303084865524957,
      "mean_waiting_s": 30.108459108459108
    },
    {
      "kind": "demand_mult",
      "mult": 1.5,
      "controller": "fixed",
      "seed": 2,
      "fuel_per_vehicle_L": 0.15802299363050107,
      "mean_waiting_s": 42.65236942234521
    },
    {
      "kind": "demand_mult",
      "mult": 1.5,
      "controller": "ours_fuel",
      "seed": 2,
      "fuel_per_vehicle_L": 0.14037142971436073,
      "mean_waiting_s": 29.269111034244204
    },
    {
      "kind": "demand_mult",
      "mult": 1.5,
      "controller": "fixed",
      "seed": 3,
      "fuel_per_vehicle_L": 0.17349661743649597,
      "mean_waiting_s": 53.870383275261325
    },
    {
      "kind": "demand_mult",
      "mult": 1.5,
      "controller": "ours_fuel",
      "seed": 3,
      "fuel_per_vehicle_L": 0.1446311236757915,
      "mean_waiting_s": 31.193728222996516
    },
    {
      "kind": "demand_mult",
      "mult": 1.5,
      "controller": "fixed",
      "seed": 4,
      "fuel_per_vehicle_L": 0.19362997211443947,
      "mean_waiting_s": 68.48244382022472
    },
    {
      "kind": "demand_mult",
      "mult": 1.5,
      "controller": "ours_fuel",
      "seed": 4,
      "fuel_per_vehicle_L": 0.14595701832706698,
      "mean_waiting_s": 33.26825842696629
    },
    {
      "kind": "demand_mult",
      "mult": 1.5,
      "controller": "fixed",
      "seed": 5,
      "fuel_per_vehicle_L": 0.16230910715602567,
      "mean_waiting_s": 44.69252271139064
    },
    {
      "kind": "demand_mult",
      "mult": 1.5,
      "controller": "ours_fuel",
      "seed": 5,
      "fuel_per_vehicle_L": 0.14087572680499236,
      "mean_waiting_s": 28.63067784765898
    },
    {
      "kind": "mix_lhs",
      "mix_id": 0,
      "mix": {
        "two_wheeler": 0.4790500449399903,
        "car": 0.3544947901159641,
        "auto_rickshaw": 0.062666638024849,
        "bus": 0.019969052559119536,
        "truck": 0.08381947436007701
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.11287872134371556
    },
    {
      "kind": "mix_lhs",
      "mix_id": 0,
      "mix": {
        "two_wheeler": 0.4790500449399903,
        "car": 0.3544947901159641,
        "auto_rickshaw": 0.062666638024849,
        "bus": 0.019969052559119536,
        "truck": 0.08381947436007701
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.10386091138094876
    },
    {
      "kind": "mix_lhs",
      "mix_id": 1,
      "mix": {
        "two_wheeler": 0.4579174365352388,
        "car": 0.2601250058555112,
        "auto_rickshaw": 0.09687927451136373,
        "bus": 0.05345232799556214,
        "truck": 0.1316259551023241
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.1357165597789324
    },
    {
      "kind": "mix_lhs",
      "mix_id": 1,
      "mix": {
        "two_wheeler": 0.4579174365352388,
        "car": 0.2601250058555112,
        "auto_rickshaw": 0.09687927451136373,
        "bus": 0.05345232799556214,
        "truck": 0.1316259551023241
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.1239161462711969
    },
    {
      "kind": "mix_lhs",
      "mix_id": 2,
      "mix": {
        "two_wheeler": 0.3559101682459436,
        "car": 0.18678888409321986,
        "auto_rickshaw": 0.13939503624592436,
        "bus": 0.05710139947637041,
        "truck": 0.26080451193854187
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.18077224071498438
    },
    {
      "kind": "mix_lhs",
      "mix_id": 2,
      "mix": {
        "two_wheeler": 0.3559101682459436,
        "car": 0.18678888409321986,
        "auto_rickshaw": 0.13939503624592436,
        "bus": 0.05710139947637041,
        "truck": 0.26080451193854187
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.16320619178550722
    },
    {
      "kind": "mix_lhs",
      "mix_id": 3,
      "mix": {
        "two_wheeler": 0.26505820865982943,
        "car": 0.34372672232533774,
        "auto_rickshaw": 0.20403131053121198,
        "bus": 0.08899099023544356,
        "truck": 0.09819276824817723
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.14264803442152166
    },
    {
      "kind": "mix_lhs",
      "mix_id": 3,
      "mix": {
        "two_wheeler": 0.26505820865982943,
        "car": 0.34372672232533774,
        "auto_rickshaw": 0.20403131053121198,
        "bus": 0.08899099023544356,
        "truck": 0.09819276824817723
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.12860169597546345
    },
    {
      "kind": "mix_lhs",
      "mix_id": 4,
      "mix": {
        "two_wheeler": 0.438753450885188,
        "car": 0.21193870146176025,
        "auto_rickshaw": 0.1456073026196952,
        "bus": 0.03490943701096463,
        "truck": 0.16879110802239192
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.13841233107550716
    },
    {
      "kind": "mix_lhs",
      "mix_id": 4,
      "mix": {
        "two_wheeler": 0.438753450885188,
        "car": 0.21193870146176025,
        "auto_rickshaw": 0.1456073026196952,
        "bus": 0.03490943701096463,
        "truck": 0.16879110802239192
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.12951182041315418
    },
    {
      "kind": "mix_lhs",
      "mix_id": 5,
      "mix": {
        "two_wheeler": 0.38783328226635205,
        "car": 0.3173674201034499,
        "auto_rickshaw": 0.0628520857399665,
        "bus": 0.0646372664745872,
        "truck": 0.1673099454156444
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.1497150313281698
    },
    {
      "kind": "mix_lhs",
      "mix_id": 5,
      "mix": {
        "two_wheeler": 0.38783328226635205,
        "car": 0.3173674201034499,
        "auto_rickshaw": 0.0628520857399665,
        "bus": 0.0646372664745872,
        "truck": 0.1673099454156444
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.1388272056580339
    },
    {
      "kind": "mix_lhs",
      "mix_id": 6,
      "mix": {
        "two_wheeler": 0.3610331169039355,
        "car": 0.3117256180086687,
        "auto_rickshaw": 0.14498002190395795,
        "bus": 0.10260241070557422,
        "truck": 0.07965883247786351
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.13309230854603996
    },
    {
      "kind": "mix_lhs",
      "mix_id": 6,
      "mix": {
        "two_wheeler": 0.3610331169039355,
        "car": 0.3117256180086687,
        "auto_rickshaw": 0.14498002190395795,
        "bus": 0.10260241070557422,
        "truck": 0.07965883247786351
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.12401578440434148
    },
    {
      "kind": "mix_lhs",
      "mix_id": 7,
      "mix": {
        "two_wheeler": 0.3759750336356286,
        "car": 0.28417799392770615,
        "auto_rickshaw": 0.19524898743538924,
        "bus": 0.07116422585173585,
        "truck": 0.07343375914954016
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.12058702958296819
    },
    {
      "kind": "mix_lhs",
      "mix_id": 7,
      "mix": {
        "two_wheeler": 0.3759750336356286,
        "car": 0.28417799392770615,
        "auto_rickshaw": 0.19524898743538924,
        "bus": 0.07116422585173585,
        "truck": 0.07343375914954016
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.11212566788030957
    },
    {
      "kind": "mix_lhs",
      "mix_id": 8,
      "mix": {
        "two_wheeler": 0.31212306382123883,
        "car": 0.43353536848809754,
        "auto_rickshaw": 0.1473571657747223,
        "bus": 0.029314385259374468,
        "truck": 0.07767001665656682
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.11591715102857639
    },
    {
      "kind": "mix_lhs",
      "mix_id": 8,
      "mix": {
        "two_wheeler": 0.31212306382123883,
        "car": 0.43353536848809754,
        "auto_rickshaw": 0.1473571657747223,
        "bus": 0.029314385259374468,
        "truck": 0.07767001665656682
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.10496406780264206
    },
    {
      "kind": "mix_lhs",
      "mix_id": 9,
      "mix": {
        "two_wheeler": 0.37556626500312745,
        "car": 0.22515426513873876,
        "auto_rickshaw": 0.10770750429590638,
        "bus": 0.09514852560943775,
        "truck": 0.19642343995278952
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.16392458498948373
    },
    {
      "kind": "mix_lhs",
      "mix_id": 9,
      "mix": {
        "two_wheeler": 0.37556626500312745,
        "car": 0.22515426513873876,
        "auto_rickshaw": 0.10770750429590638,
        "bus": 0.09514852560943775,
        "truck": 0.19642343995278952
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.1502865972403595
    },
    {
      "kind": "mix_lhs",
      "mix_id": 10,
      "mix": {
        "two_wheeler": 0.3667689466326771,
        "car": 0.22269437718735985,
        "auto_rickshaw": 0.11836449018467854,
        "bus": 0.051688127038861525,
        "truck": 0.240484058956423
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.16462893441514984
    },
    {
      "kind": "mix_lhs",
      "mix_id": 10,
      "mix": {
        "two_wheeler": 0.3667689466326771,
        "car": 0.22269437718735985,
        "auto_rickshaw": 0.11836449018467854,
        "bus": 0.051688127038861525,
        "truck": 0.240484058956423
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.1527018590075583
    },
    {
      "kind": "mix_lhs",
      "mix_id": 11,
      "mix": {
        "two_wheeler": 0.37395986756348387,
        "car": 0.275894097177123,
        "auto_rickshaw": 0.07427188334835215,
        "bus": 0.07311855915266842,
        "truck": 0.2027555927583726
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.16012313848782656
    },
    {
      "kind": "mix_lhs",
      "mix_id": 11,
      "mix": {
        "two_wheeler": 0.37395986756348387,
        "car": 0.275894097177123,
        "auto_rickshaw": 0.07427188334835215,
        "bus": 0.07311855915266842,
        "truck": 0.2027555927583726
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.14747963576275397
    },
    {
      "kind": "mix_lhs",
      "mix_id": 12,
      "mix": {
        "two_wheeler": 0.38441707779861983,
        "car": 0.20575198733607075,
        "auto_rickshaw": 0.1563671696567344,
        "bus": 0.0806327884143243,
        "truck": 0.1728309767942508
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.1550449732892946
    },
    {
      "kind": "mix_lhs",
      "mix_id": 12,
      "mix": {
        "two_wheeler": 0.38441707779861983,
        "car": 0.20575198733607075,
        "auto_rickshaw": 0.1563671696567344,
        "bus": 0.0806327884143243,
        "truck": 0.1728309767942508
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.14207398767244495
    },
    {
      "kind": "mix_lhs",
      "mix_id": 13,
      "mix": {
        "two_wheeler": 0.47011492733712523,
        "car": 0.3270124230733235,
        "auto_rickshaw": 0.06741278144131524,
        "bus": 0.03397783336421716,
        "truck": 0.10148203478401893
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.12460942136183448
    },
    {
      "kind": "mix_lhs",
      "mix_id": 13,
      "mix": {
        "two_wheeler": 0.47011492733712523,
        "car": 0.3270124230733235,
        "auto_rickshaw": 0.06741278144131524,
        "bus": 0.03397783336421716,
        "truck": 0.10148203478401893
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.11456289096888442
    },
    {
      "kind": "mix_lhs",
      "mix_id": 14,
      "mix": {
        "two_wheeler": 0.48936936838201495,
        "car": 0.15151023796442797,
        "auto_rickshaw": 0.15140358810735308,
        "bus": 0.07110236044248244,
        "truck": 0.13661444510372142
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.1386555672695958
    },
    {
      "kind": "mix_lhs",
      "mix_id": 14,
      "mix": {
        "two_wheeler": 0.48936936838201495,
        "car": 0.15151023796442797,
        "auto_rickshaw": 0.15140358810735308,
        "bus": 0.07110236044248244,
        "truck": 0.13661444510372142
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.12836520538986806
    },
    {
      "kind": "mix_lhs",
      "mix_id": 15,
      "mix": {
        "two_wheeler": 0.4628635829844354,
        "car": 0.18578964713663235,
        "auto_rickshaw": 0.09025454454351017,
        "bus": 0.06891189836955368,
        "truck": 0.19218032696586845
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.15771669876323183
    },
    {
      "kind": "mix_lhs",
      "mix_id": 15,
      "mix": {
        "two_wheeler": 0.4628635829844354,
        "car": 0.18578964713663235,
        "auto_rickshaw": 0.09025454454351017,
        "bus": 0.06891189836955368,
        "truck": 0.19218032696586845
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.14561829524971953
    },
    {
      "kind": "mix_lhs",
      "mix_id": 16,
      "mix": {
        "two_wheeler": 0.43832838022962345,
        "car": 0.24303971784577752,
        "auto_rickshaw": 0.1612941642322598,
        "bus": 0.06422414023833808,
        "truck": 0.09311359745400115
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.12436840845715838
    },
    {
      "kind": "mix_lhs",
      "mix_id": 16,
      "mix": {
        "two_wheeler": 0.43832838022962345,
        "car": 0.24303971784577752,
        "auto_rickshaw": 0.1612941642322598,
        "bus": 0.06422414023833808,
        "truck": 0.09311359745400115
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.11457100220948892
    },
    {
      "kind": "mix_lhs",
      "mix_id": 17,
      "mix": {
        "two_wheeler": 0.33029632274984894,
        "car": 0.27691572070821424,
        "auto_rickshaw": 0.1395354428856814,
        "bus": 0.07095061760269473,
        "truck": 0.1823018960535607
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.16055854646188758
    },
    {
      "kind": "mix_lhs",
      "mix_id": 17,
      "mix": {
        "two_wheeler": 0.33029632274984894,
        "car": 0.27691572070821424,
        "auto_rickshaw": 0.1395354428856814,
        "bus": 0.07095061760269473,
        "truck": 0.1823018960535607
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.1442260877181922
    },
    {
      "kind": "mix_lhs",
      "mix_id": 18,
      "mix": {
        "two_wheeler": 0.4232767998970235,
        "car": 0.2840205085733944,
        "auto_rickshaw": 0.14273687128531426,
        "bus": 0.03853931970160648,
        "truck": 0.11142650054266141
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.1258116285020269
    },
    {
      "kind": "mix_lhs",
      "mix_id": 18,
      "mix": {
        "two_wheeler": 0.4232767998970235,
        "car": 0.2840205085733944,
        "auto_rickshaw": 0.14273687128531426,
        "bus": 0.03853931970160648,
        "truck": 0.11142650054266141
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.11593529339515317
    },
    {
      "kind": "mix_lhs",
      "mix_id": 19,
      "mix": {
        "two_wheeler": 0.34589163100514714,
        "car": 0.33808163310960637,
        "auto_rickshaw": 0.08336846363600271,
        "bus": 0.02442910258121678,
        "truck": 0.2082291696680271
      },
      "controller": "fixed",
      "fuel_per_vehicle_L": 0.1516568439213413
    },
    {
      "kind": "mix_lhs",
      "mix_id": 19,
      "mix": {
        "two_wheeler": 0.34589163100514714,
        "car": 0.33808163310960637,
        "auto_rickshaw": 0.08336846363600271,
        "bus": 0.02442910258121678,
        "truck": 0.2082291696680271
      },
      "controller": "ours_fuel",
      "fuel_per_vehicle_L": 0.140154693376269
    }
  ],
  "gains": [
    {
      "demand_mult": 0.5,
      "dos_proxy": 0.5,
      "pct_fuel_reduction": 10.602198276000301
    },
    {
      "demand_mult": 0.75,
      "dos_proxy": 0.75,
      "pct_fuel_reduction": 8.52498458872319
    },
    {
      "demand_mult": 1.0,
      "dos_proxy": 1.0,
      "pct_fuel_reduction": 8.756520885823504
    },
    {
      "demand_mult": 1.25,
      "dos_proxy": 1.25,
      "pct_fuel_reduction": 10.804838833039106
    },
    {
      "demand_mult": 1.5,
      "dos_proxy": 1.5,
      "pct_fuel_reduction": 15.865372015174115
    }
  ],
  "mix_ranges_assumed": {
    "two_wheeler": [
      0.25,
      0.55
    ],
    "car": [
      0.15,
      0.4
    ],
    "auto_rickshaw": [
      0.05,
      0.2
    ],
    "bus": [
      0.02,
      0.1
    ],
    "truck": [
      0.05,
      0.25
    ]
  },
  "label": "assumed"
}
```


## Emission cross-check

```
{
  "rows": [
    {
      "emission_model": "primary",
      "controller": "fixed",
      "seed": 1,
      "fuel_per_vehicle_L": 0.16825387050122914,
      "total_CO2_kg": 751.8771439596112
    },
    {
      "emission_model": "primary",
      "controller": "fixed",
      "seed": 2,
      "fuel_per_vehicle_L": 0.15099963849732415,
      "total_CO2_kg": 679.3207429065964
    },
    {
      "emission_model": "primary",
      "controller": "fixed",
      "seed": 3,
      "fuel_per_vehicle_L": 0.16772013985952372,
      "total_CO2_kg": 762.3523173808147
    },
    {
      "emission_model": "primary",
      "controller": "fixed",
      "seed": 4,
      "fuel_per_vehicle_L": 0.1561927492002893,
      "total_CO2_kg": 692.386601408719
    },
    {
      "emission_model": "primary",
      "controller": "fixed",
      "seed": 5,
      "fuel_per_vehicle_L": 0.15262784972880303,
      "total_CO2_kg": 687.9709162363774
    },
    {
      "emission_model": "primary",
      "controller": "fixed",
      "seed": 6,
      "fuel_per_vehicle_L": 0.1590617929584818,
      "total_CO2_kg": 717.6026889894295
    },
    {
      "emission_model": "primary",
      "controller": "fixed",
      "seed": 7,
      "fuel_per_vehicle_L": 0.15990351562377178,
      "total_CO2_kg": 730.1288267486499
    },
    {
      "emission_model": "primary",
      "controller": "fixed",
      "seed": 8,
      "fuel_per_vehicle_L": 0.15273262554837067,
      "total_CO2_kg": 681.6008669634178
    },
    {
      "emission_model": "primary",
      "controller": "fixed",
      "seed": 9,
      "fuel_per_vehicle_L": 0.15020884272010745,
      "total_CO2_kg": 677.9738856881638
    },
    {
      "emission_model": "primary",
      "controller": "fixed",
      "seed": 10,
      "fuel_per_vehicle_L": 0.1448182008912697,
      "total_CO2_kg": 646.342034987363
    },
    {
      "emission_model": "primary",
      "controller": "ours_fuel",
      "seed": 1,
      "fuel_per_vehicle_L": 0.12618845659970995,
      "total_CO2_kg": 564.3295659810955
    },
    {
      "emission_model": "primary",
      "controller": "ours_fuel",
      "seed": 2,
      "fuel_per_vehicle_L": 0.12250448310524238,
      "total_CO2_kg": 551.4742889253793
    },
    {
      "emission_model": "primary",
      "controller": "ours_fuel",
      "seed": 3,
      "fuel_per_vehicle_L": 0.12194778332190839,
      "total_CO2_kg": 556.0678849473564
    },
    {
      "emission_model": "primary",
      "controller": "ours_fuel",
      "seed": 4,
      "fuel_per_vehicle_L": 0.12602694810995943,
      "total_CO2_kg": 559.6325485755278
    },
    {
      "emission_model": "primary",
      "controller": "ours_fuel",
      "seed": 5,
      "fuel_per_vehicle_L": 0.12366168549966675,
      "total_CO2_kg": 557.9063579381044
    },
    {
      "emission_model": "primary",
      "controller": "ours_fuel",
      "seed": 6,
      "fuel_per_vehicle_L": 0.12437603246507771,
      "total_CO2_kg": 561.7565732305302
    },
    {
      "emission_model": "primary",
      "controller": "ours_fuel",
      "seed": 7,
      "fuel_per_vehicle_L": 0.12312805647124193,
      "total_CO2_kg": 562.7190578233187
    },
    {
      "emission_model": "primary",
      "controller": "ours_fuel",
      "seed": 8,
      "fuel_per_vehicle_L": 0.12113360542286047,
      "total_CO2_kg": 540.5569248398649
    },
    {
      "emission_model": "primary",
      "controller": "ours_fuel",
      "seed": 9,
      "fuel_per_vehicle_L": 0.12098158925839972,
      "total_CO2_kg": 546.5543405455395
    },
    {
      "emission_model": "primary",
      "controller": "ours_fuel",
      "seed": 10,
      "fuel_per_vehicle_L": 0.12102346823277664,
      "total_CO2_kg": 540.4697430294964
    },
    {
      "emission_model": "alternate",
      "controller": "fixed",
      "seed": 1,
      "fuel_per_vehicle_L": 0.06955783308340464,
      "total_CO2_kg": 297.36519197858433
    },
    {
      "emission_model": "alternate",
      "controller": "fixed",
      "seed": 2,
      "fuel_per_vehicle_L": 0.0665556053411234,
      "total_CO2_kg": 286.75040090340565
    },
    {
      "emission_model": "alternate",
      "controller": "fixed",
      "seed": 3,
      "fuel_per_vehicle_L": 0.07223158722324723,
      "total_CO2_kg": 315.2522726356729
    },
    {
      "emission_model": "alternate",
      "controller": "fixed",
      "seed": 4,
      "fuel_per_vehicle_L": 0.06698924965224079,
      "total_CO2_kg": 284.0970412068856
    },
    {
      "emission_model": "alternate",
      "controller": "fixed",
      "seed": 5,
      "fuel_per_vehicle_L": 0.06651634680588074,
      "total_CO2_kg": 286.8120881181041
    },
    {
      "emission_model": "alternate",
      "controller": "fixed",
      "seed": 6,
      "fuel_per_vehicle_L": 0.06738488125633045,
      "total_CO2_kg": 290.7549973169825
    },
    {
      "emission_model": "alternate",
      "controller": "fixed",
      "seed": 7,
      "fuel_per_vehicle_L": 0.06878842926011872,
      "total_CO2_kg": 300.8357374017696
    },
    {
      "emission_model": "alternate",
      "controller": "fixed",
      "seed": 8,
      "fuel_per_vehicle_L": 0.06646511621443624,
      "total_CO2_kg": 283.918924500982
    },
    {
      "emission_model": "alternate",
      "controller": "fixed",
      "seed": 9,
      "fuel_per_vehicle_L": 0.06641771497452081,
      "total_CO2_kg": 287.006315770587
    },
    {
      "emission_model": "alternate",
      "controller": "fixed",
      "seed": 10,
      "fuel_per_vehicle_L": 0.0649548777719682,
      "total_CO2_kg": 277.48044866367854
    },
    {
      "emission_model": "alternate",
      "controller": "ours_fuel",
      "seed": 1,
      "fuel_per_vehicle_L": 0.05854692794684487,
      "total_CO2_kg": 249.9705228002175
    },
    {
      "emission_model": "alternate",
      "controller": "ours_fuel",
      "seed": 2,
      "fuel_per_vehicle_L": 0.058824041165999034,
      "total_CO2_kg": 253.16883061836631
    },
    {
      "emission_model": "alternate",
      "controller": "ours_fuel",
      "seed": 3,
      "fuel_per_vehicle_L": 0.05912079544595832,
      "total_CO2_kg": 257.85334637732774
    },
    {
      "emission_model": "alternate",
      "controller": "ours_fuel",
      "seed": 4,
      "fuel_per_vehicle_L": 0.05869439357718391,
      "total_CO2_kg": 248.81449638835988
    },
    {
      "emission_model": "alternate",
      "controller": "ours_fuel",
      "seed": 5,
      "fuel_per_vehicle_L": 0.058931122118537245,
      "total_CO2_kg": 253.87918406131524
    },
    {
      "emission_model": "alternate",
      "controller": "ours_fuel",
      "seed": 6,
      "fuel_per_vehicle_L": 0.05811069969572346,
      "total_CO2_kg": 250.53919673959206
    },
    {
      "emission_model": "alternate",
      "controller": "ours_fuel",
      "seed": 7,
      "fuel_per_vehicle_L": 0.05883646773140492,
      "total_CO2_kg": 256.98457873170594
    },
    {
      "emission_model": "alternate",
      "controller": "ours_fuel",
      "seed": 8,
      "fuel_per_vehicle_L": 0.05844457065729735,
      "total_CO2_kg": 249.30355417493513
    },
    {
      "emission_model": "alternate",
      "controller": "ours_fuel",
      "seed": 9,
      "fuel_per_vehicle_L": 0.05845595797535595,
      "total_CO2_kg": 252.38554214632293
    },
    {
      "emission_model": "alternate",
      "controller": "ours_fuel",
      "seed": 10,
      "fuel_per_vehicle_L": 0.058483074019490704,
      "total_CO2_kg": 249.6330095799201
    }
  ],
  "pct_reduction_primary": 21.083717799671348,
  "pct_reduction_alternate": 13.163225668508568,
  "verdict": "unchanged_direction",
  "emission_map": {
    "primary": {
      "two_wheeler": "HBEFA3/LDV_G_EU4",
      "auto_rickshaw": "HBEFA3/PC_G_EU4",
      "car": "HBEFA3/PC_G_EU4",
      "bus": "HBEFA3/Bus",
      "truck": "HBEFA3/HDV"
    },
    "alternate": {
      "two_wheeler": "PHEMlight/PC_G_EU4",
      "auto_rickshaw": "PHEMlight/PC_G_EU4",
      "car": "PHEMlight/PC_G_EU4",
      "bus": "PHEMlight/PC_G_EU4",
      "truck": "PHEMlight/PC_G_EU4"
    },
    "tested": {
      "HBEFA3/LDV_G_EU4": true,
      "HBEFA3/PC_G_EU4": true,
      "HBEFA3/Bus": true,
      "HBEFA3/HDV": true,
      "PHEMlight/PC_G_EU4": true
    },
    "note": "Installed SUMO 1.21: HBEFA3/PHEMlight available; HBEFA4 not present in this build."
  },
  "note": "Alternate uses HBEFA3 fallback set if PHEMlight unavailable."
}
```


## Safety

```
{
  "by_controller": [
    {
      "controller": "actuated",
      "mean": 0.0,
      "std": 0.0,
      "count": 120
    },
    {
      "controller": "fixed",
      "mean": 0.0,
      "std": 0.0,
      "count": 120
    },
    {
      "controller": "maxpressure",
      "mean": 0.0,
      "std": 0.0,
      "count": 120
    },
    {
      "controller": "ours_count",
      "mean": 0.0,
      "std": 0.0,
      "count": 120
    },
    {
      "controller": "ours_fuel",
      "mean": 0.0,
      "std": 0.0,
      "count": 120
    },
    {
      "controller": "rl_ppo",
      "mean": 0.0,
      "std": 0.0,
      "count": 120
    },
    {
      "controller": "webster",
      "mean": 0.0,
      "std": 0.0,
      "count": 120
    }
  ],
  "ours_minus_fixed_mean_conflicts": 0.0,
  "verdict": "no_increase",
  "note": "SSM TTC<1.5s counts from SUMO device; model-based."
}
```


## Robustness

```
{
  "scenario": "peak_unbalanced",
  "rows": [
    {
      "kind": "reference",
      "controller": "fixed",
      "miss": 0.0,
      "seed": 1,
      "fuel_per_vehicle_L": 0.16825387050122914,
      "mean_waiting_s": 46.83668903803132
    },
    {
      "kind": "reference",
      "controller": "fixed",
      "miss": 0.0,
      "seed": 2,
      "fuel_per_vehicle_L": 0.15099963849732415,
      "mean_waiting_s": 38.357142857142854
    },
    {
      "kind": "reference",
      "controller": "fixed",
      "miss": 0.0,
      "seed": 3,
      "fuel_per_vehicle_L": 0.16772013985952372,
      "mean_waiting_s": 52.94374658656472
    },
    {
      "kind": "reference",
      "controller": "fixed",
      "miss": 0.0,
      "seed": 4,
      "fuel_per_vehicle_L": 0.1561927492002893,
      "mean_waiting_s": 39.88169014084507
    },
    {
      "kind": "reference",
      "controller": "fixed",
      "miss": 0.0,
      "seed": 5,
      "fuel_per_vehicle_L": 0.15262784972880303,
      "mean_waiting_s": 37.64416159380188
    },
    {
      "kind": "reference",
      "controller": "fixed",
      "miss": 0.0,
      "seed": 6,
      "fuel_per_vehicle_L": 0.1590617929584818,
      "mean_waiting_s": 41.10077519379845
    },
    {
      "kind": "reference",
      "controller": "fixed",
      "miss": 0.0,
      "seed": 7,
      "fuel_per_vehicle_L": 0.15990351562377178,
      "mean_waiting_s": 43.998908296943235
    },
    {
      "kind": "reference",
      "controller": "fixed",
      "miss": 0.0,
      "seed": 8,
      "fuel_per_vehicle_L": 0.15273262554837067,
      "mean_waiting_s": 38.439106145251394
    },
    {
      "kind": "reference",
      "controller": "fixed",
      "miss": 0.0,
      "seed": 9,
      "fuel_per_vehicle_L": 0.15020884272010745,
      "mean_waiting_s": 37.94867549668874
    },
    {
      "kind": "reference",
      "controller": "fixed",
      "miss": 0.0,
      "seed": 10,
      "fuel_per_vehicle_L": 0.1448182008912697,
      "mean_waiting_s": 33.48687883863763
    },
    {
      "kind": "reference",
      "controller": "actuated",
      "miss": 0.0,
      "seed": 1,
      "fuel_per_vehicle_L": 0.13902627211881358,
      "mean_waiting_s": 25.772930648769574
    },
    {
      "kind": "reference",
      "controller": "actuated",
      "miss": 0.0,
      "seed": 2,
      "fuel_per_vehicle_L": 0.13383754020467642,
      "mean_waiting_s": 24.83997785160576
    },
    {
      "kind": "reference",
      "controller": "actuated",
      "miss": 0.0,
      "seed": 3,
      "fuel_per_vehicle_L": 0.13390227466252141,
      "mean_waiting_s": 25.836701256144185
    },
    {
      "kind": "reference",
      "controller": "actuated",
      "miss": 0.0,
      "seed": 4,
      "fuel_per_vehicle_L": 0.1377809291526477,
      "mean_waiting_s": 24.899154929577463
    },
    {
      "kind": "reference",
      "controller": "actuated",
      "miss": 0.0,
      "seed": 5,
      "fuel_per_vehicle_L": 0.1360377232913059,
      "mean_waiting_s": 25.729385722191477
    },
    {
      "kind": "reference",
      "controller": "actuated",
      "miss": 0.0,
      "seed": 6,
      "fuel_per_vehicle_L": 0.1374850260564838,
      "mean_waiting_s": 25.579180509413067
    },
    {
      "kind": "reference",
      "controller": "actuated",
      "miss": 0.0,
      "seed": 7,
      "fuel_per_vehicle_L": 0.13600132878592536,
      "mean_waiting_s": 25.415393013100438
    },
    {
      "kind": "reference",
      "controller": "actuated",
      "miss": 0.0,
      "seed": 8,
      "fuel_per_vehicle_L": 0.13475542830815102,
      "mean_waiting_s": 24.556424581005587
    },
    {
      "kind": "reference",
      "controller": "actuated",
      "miss": 0.0,
      "seed": 9,
      "fuel_per_vehicle_L": 0.13353561824083107,
      "mean_waiting_s": 24.78532008830022
    },
    {
      "kind": "reference",
      "controller": "actuated",
      "miss": 0.0,
      "seed": 10,
      "fuel_per_vehicle_L": 0.13606116681854882,
      "mean_waiting_s": 26.12897822445561
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.0,
      "seed": 1,
      "fuel_per_vehicle_L": 0.12618845659970995,
      "mean_waiting_s": 18.48937360178971
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.0,
      "seed": 2,
      "fuel_per_vehicle_L": 0.12250448310524238,
      "mean_waiting_s": 18.841638981173865
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.0,
      "seed": 3,
      "fuel_per_vehicle_L": 0.12194778332190839,
      "mean_waiting_s": 19.33151283451666
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.0,
      "seed": 4,
      "fuel_per_vehicle_L": 0.12602694810995943,
      "mean_waiting_s": 18.60450704225352
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.0,
      "seed": 5,
      "fuel_per_vehicle_L": 0.12366168549966675,
      "mean_waiting_s": 17.893746541228555
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.0,
      "seed": 6,
      "fuel_per_vehicle_L": 0.12437603246507771,
      "mean_waiting_s": 17.688815060908084
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.0,
      "seed": 7,
      "fuel_per_vehicle_L": 0.12312805647124193,
      "mean_waiting_s": 18.695960698689955
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.0,
      "seed": 8,
      "fuel_per_vehicle_L": 0.12113360542286047,
      "mean_waiting_s": 17.9463687150838
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.0,
      "seed": 9,
      "fuel_per_vehicle_L": 0.12098158925839972,
      "mean_waiting_s": 18.01766004415011
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.0,
      "seed": 10,
      "fuel_per_vehicle_L": 0.12102346823277664,
      "mean_waiting_s": 17.858738135120046
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.1,
      "seed": 1,
      "fuel_per_vehicle_L": 0.12618845659970995,
      "mean_waiting_s": 18.48937360178971
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.1,
      "seed": 2,
      "fuel_per_vehicle_L": 0.12250448310524238,
      "mean_waiting_s": 18.841638981173865
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.1,
      "seed": 3,
      "fuel_per_vehicle_L": 0.12194778332190839,
      "mean_waiting_s": 19.33151283451666
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.1,
      "seed": 4,
      "fuel_per_vehicle_L": 0.12602694810995943,
      "mean_waiting_s": 18.60450704225352
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.1,
      "seed": 5,
      "fuel_per_vehicle_L": 0.12366168549966675,
      "mean_waiting_s": 17.893746541228555
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.1,
      "seed": 6,
      "fuel_per_vehicle_L": 0.12437603246507771,
      "mean_waiting_s": 17.688815060908084
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.1,
      "seed": 7,
      "fuel_per_vehicle_L": 0.12312805647124193,
      "mean_waiting_s": 18.695960698689955
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.1,
      "seed": 8,
      "fuel_per_vehicle_L": 0.12113360542286047,
      "mean_waiting_s": 17.9463687150838
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.1,
      "seed": 9,
      "fuel_per_vehicle_L": 0.12098158925839972,
      "mean_waiting_s": 18.01766004415011
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.1,
      "seed": 10,
      "fuel_per_vehicle_L": 0.12102346823277664,
      "mean_waiting_s": 17.858738135120046
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.2,
      "seed": 1,
      "fuel_per_vehicle_L": 0.12618845659970995,
      "mean_waiting_s": 18.48937360178971
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.2,
      "seed": 2,
      "fuel_per_vehicle_L": 0.12250448310524238,
      "mean_waiting_s": 18.841638981173865
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.2,
      "seed": 3,
      "fuel_per_vehicle_L": 0.12194778332190839,
      "mean_waiting_s": 19.33151283451666
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.2,
      "seed": 4,
      "fuel_per_vehicle_L": 0.1263956010676082,
      "mean_waiting_s": 18.545352112676056
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.2,
      "seed": 5,
      "fuel_per_vehicle_L": 0.12366168549966675,
      "mean_waiting_s": 17.893746541228555
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.2,
      "seed": 6,
      "fuel_per_vehicle_L": 0.12533601760568658,
      "mean_waiting_s": 18.02934662236988
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.2,
      "seed": 7,
      "fuel_per_vehicle_L": 0.1229993013153315,
      "mean_waiting_s": 18.487991266375545
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.2,
      "seed": 8,
      "fuel_per_vehicle_L": 0.12113360542286047,
      "mean_waiting_s": 17.9463687150838
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.2,
      "seed": 9,
      "fuel_per_vehicle_L": 0.12098158925839972,
      "mean_waiting_s": 18.01766004415011
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.2,
      "seed": 10,
      "fuel_per_vehicle_L": 0.12102346823277664,
      "mean_waiting_s": 17.858738135120046
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.3,
      "seed": 1,
      "fuel_per_vehicle_L": 0.1284732628707323,
      "mean_waiting_s": 20.575503355704697
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.3,
      "seed": 2,
      "fuel_per_vehicle_L": 0.12152031144974157,
      "mean_waiting_s": 18.284606866002214
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.3,
      "seed": 3,
      "fuel_per_vehicle_L": 0.12094352821451865,
      "mean_waiting_s": 18.255051884216275
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.3,
      "seed": 4,
      "fuel_per_vehicle_L": 0.12561322799520533,
      "mean_waiting_s": 18.11830985915493
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.3,
      "seed": 5,
      "fuel_per_vehicle_L": 0.12254703634471373,
      "mean_waiting_s": 17.40066408411732
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.3,
      "seed": 6,
      "fuel_per_vehicle_L": 0.12477539064665415,
      "mean_waiting_s": 17.630121816168327
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.3,
      "seed": 7,
      "fuel_per_vehicle_L": 0.12270675299617279,
      "mean_waiting_s": 18.441593886462883
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.3,
      "seed": 8,
      "fuel_per_vehicle_L": 0.12196996027616502,
      "mean_waiting_s": 18.573184357541898
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.3,
      "seed": 9,
      "fuel_per_vehicle_L": 0.12149254557729332,
      "mean_waiting_s": 18.236754966887418
    },
    {
      "kind": "ours_fuel",
      "controller": "ours_fuel",
      "miss": 0.3,
      "seed": 10,
      "fuel_per_vehicle_L": 0.12009051398776388,
      "mean_waiting_s": 16.829704075935233
    },
    {
      "kind": "empirical_noise",
      "controller": "ours_fuel",
      "miss": 0.15,
      "seed": 1,
      "fuel_per_vehicle_L": 0.12692682879109668,
      "mean_waiting_s": 18.614093959731544
    },
    {
      "kind": "empirical_noise",
      "controller": "ours_fuel",
      "miss": 0.15,
      "seed": 2,
      "fuel_per_vehicle_L": 0.12275296958142415,
      "mean_waiting_s": 18.642857142857142
    },
    {
      "kind": "empirical_noise",
      "controller": "ours_fuel",
      "miss": 0.15,
      "seed": 3,
      "fuel_per_vehicle_L": 0.12277198539982055,
      "mean_waiting_s": 18.39759694156199
    },
    {
      "kind": "empirical_noise",
      "controller": "ours_fuel",
      "miss": 0.15,
      "seed": 4,
      "fuel_per_vehicle_L": 0.1255861824463012,
      "mean_waiting_s": 17.310422535211266
    },
    {
      "kind": "empirical_noise",
      "controller": "ours_fuel",
      "miss": 0.15,
      "seed": 5,
      "fuel_per_vehicle_L": 0.12551446731127758,
      "mean_waiting_s": 18.085777531820696
    },
    {
      "kind": "empirical_noise",
      "controller": "ours_fuel",
      "miss": 0.15,
      "seed": 6,
      "fuel_per_vehicle_L": 0.12470462365454357,
      "mean_waiting_s": 17.45736434108527
    },
    {
      "kind": "empirical_noise",
      "controller": "ours_fuel",
      "miss": 0.15,
      "seed": 7,
      "fuel_per_vehicle_L": 0.1224807844233206,
      "mean_waiting_s": 17.699235807860262
    },
    {
      "kind": "empirical_noise",
      "controller": "ours_fuel",
      "miss": 0.15,
      "seed": 8,
      "fuel_per_vehicle_L": 0.1250545497642355,
      "mean_waiting_s": 18.577653631284917
    },
    {
      "kind": "empirical_noise",
      "controller": "ours_fuel",
      "miss": 0.15,
      "seed": 9,
      "fuel_per_vehicle_L": 0.12269001089244436,
      "mean_waiting_s": 18.297461368653423
    },
    {
      "kind": "empirical_noise",
      "controller": "ours_fuel",
      "miss": 0.15,
      "seed": 10,
      "fuel_per_vehicle_L": 0.12181939424168316,
      "mean_waiting_s": 17.559463986599663
    }
  ],
  "label": "Simulation-based"
}
```


## Grid study

```
{
  "rows": [
    {
      "controller": "fixed",
      "seed": 1,
      "fuel_per_vehicle_L": 0.18038311514752287,
      "mean_waiting_s": 40.01086956521739,
      "n_completed": 184,
      "wall_time_s": 0.4088277816772461
    },
    {
      "controller": "fixed",
      "seed": 2,
      "fuel_per_vehicle_L": 0.19571375043476683,
      "mean_waiting_s": 45.38164251207729,
      "n_completed": 207,
      "wall_time_s": 0.41196393966674805
    },
    {
      "controller": "fixed",
      "seed": 3,
      "fuel_per_vehicle_L": 0.17200010066812443,
      "mean_waiting_s": 43.6875,
      "n_completed": 192,
      "wall_time_s": 0.40558600425720215
    },
    {
      "controller": "fixed",
      "seed": 4,
      "fuel_per_vehicle_L": 0.18225459931391746,
      "mean_waiting_s": 40.56603773584906,
      "n_completed": 159,
      "wall_time_s": 0.3892688751220703
    },
    {
      "controller": "fixed",
      "seed": 5,
      "fuel_per_vehicle_L": 0.18534411166336426,
      "mean_waiting_s": 43.36040609137056,
      "n_completed": 197,
      "wall_time_s": 0.4092719554901123
    },
    {
      "controller": "actuated",
      "seed": 1,
      "fuel_per_vehicle_L": 0.14853727812552173,
      "mean_waiting_s": 19.128342245989305,
      "n_completed": 187,
      "wall_time_s": 0.1568138599395752
    },
    {
      "controller": "actuated",
      "seed": 2,
      "fuel_per_vehicle_L": 0.15045234445512923,
      "mean_waiting_s": 17.578199052132703,
      "n_completed": 211,
      "wall_time_s": 0.16177105903625488
    },
    {
      "controller": "actuated",
      "seed": 3,
      "fuel_per_vehicle_L": 0.13174738948202958,
      "mean_waiting_s": 17.237623762376238,
      "n_completed": 202,
      "wall_time_s": 0.15846610069274902
    },
    {
      "controller": "actuated",
      "seed": 4,
      "fuel_per_vehicle_L": 0.14191593952604145,
      "mean_waiting_s": 17.26993865030675,
      "n_completed": 163,
      "wall_time_s": 0.15192389488220215
    },
    {
      "controller": "actuated",
      "seed": 5,
      "fuel_per_vehicle_L": 0.15158022894460368,
      "mean_waiting_s": 19.587064676616915,
      "n_completed": 201,
      "wall_time_s": 0.16217923164367676
    },
    {
      "controller": "ours_fuel",
      "seed": 1,
      "fuel_per_vehicle_L": 0.2714619232611139,
      "mean_waiting_s": 114.61581920903954,
      "n_completed": 177,
      "wall_time_s": 1.9202568531036377
    },
    {
      "controller": "ours_fuel",
      "seed": 2,
      "fuel_per_vehicle_L": 0.2722023018005137,
      "mean_waiting_s": 125.1875,
      "n_completed": 192,
      "wall_time_s": 1.829901933670044
    },
    {
      "controller": "ours_fuel",
      "seed": 3,
      "fuel_per_vehicle_L": 0.2691155565445909,
      "mean_waiting_s": 127.02173913043478,
      "n_completed": 184,
      "wall_time_s": 1.799536943435669
    },
    {
      "controller": "ours_fuel",
      "seed": 4,
      "fuel_per_vehicle_L": 0.2650722384469183,
      "mean_waiting_s": 110.61073825503355,
      "n_completed": 149,
      "wall_time_s": 1.7747387886047363
    },
    {
      "controller": "ours_fuel",
      "seed": 5,
      "fuel_per_vehicle_L": 0.2689299050190488,
      "mean_waiting_s": 116.19021739130434,
      "n_completed": 184,
      "wall_time_s": 1.7851362228393555
    },
    {
      "controller": "ours_fuel_coord",
      "seed": 1,
      "fuel_per_vehicle_L": 0.2714619232611139,
      "mean_waiting_s": 114.61581920903954,
      "n_completed": 177,
      "wall_time_s": 1.8435909748077393
    },
    {
      "controller": "ours_fuel_coord",
      "seed": 2,
      "fuel_per_vehicle_L": 0.2722023018005137,
      "mean_waiting_s": 125.1875,
      "n_completed": 192,
      "wall_time_s": 1.8013279438018799
    },
    {
      "controller": "ours_fuel_coord",
      "seed": 3,
      "fuel_per_vehicle_L": 0.2691155565445909,
      "mean_waiting_s": 127.02173913043478,
      "n_completed": 184,
      "wall_time_s": 1.8755676746368408
    },
    {
      "controller": "ours_fuel_coord",
      "seed": 4,
      "fuel_per_vehicle_L": 0.2650722384469183,
      "mean_waiting_s": 110.61073825503355,
      "n_completed": 149,
      "wall_time_s": 1.7674212455749512
    },
    {
      "controller": "ours_fuel_coord",
      "seed": 5,
      "fuel_per_vehicle_L": 0.2689299050190488,
      "mean_waiting_s": 116.19021739130434,
      "n_completed": 184,
      "wall_time_s": 2.020195245742798
    }
  ],
  "summary_means": {
    "fuel_per_vehicle_L": {
      "actuated": 0.14484663610666512,
      "fixed": 0.18313913544553917,
      "ours_fuel": 0.2693563850144371,
      "ours_fuel_coord": 0.2693563850144371
    },
    "mean_waiting_s": {
      "actuated": 18.16023367748438,
      "fixed": 42.60129118090286,
      "ours_fuel": 118.72520279716245,
      "ours_fuel_coord": 118.72520279716245
    },
    "n_completed": {
      "actuated": 192.8,
      "fixed": 187.8,
      "ours_fuel": 177.2,
      "ours_fuel_coord": 177.2
    }
  },
  "coordination_reduces_fuel": false,
  "label": "Simulation-based estimate"
}
```


## Extrapolation

```
{
  "label": "Simulation-based estimate; not a real-world deployment result",
  "scenario_basis": "peak_unbalanced",
  "measured_saving_L_per_veh": {
    "mean": 0.03501746060996848,
    "p05": 0.031876198162417345,
    "p95": 0.03825006931643624
  },
  "annual_litres": {
    "median": 27737080.86558083,
    "p05": 8997338.18625999,
    "p95": 66756793.494768
  },
  "annual_INR_PLACEHOLDER_price": {
    "median": 2771289723.9756203,
    "p05": 889032470.6741536,
    "p95": 6643839880.766568
  },
  "annual_tonnes_CO2": {
    "median": 67151.4727755712,
    "p05": 21782.555748935436,
    "p95": 161618.19705083338
  },
  "fuel_price_note": "INR/L is a user-editable PLACEHOLDER in config.yaml",
  "headlines_ref": [
    {
      "scenario": "balanced",
      "pct_fuel_reduction_vs_fixed": 8.606437261931198,
      "ci_lo": 8.22501997578311,
      "ci_hi": 8.997435659549451,
      "sanity_flag": "OK"
    },
    {
      "scenario": "dynamic",
      "pct_fuel_reduction_vs_fixed": 16.50048788855564,
      "ci_lo": 15.72146557801056,
      "ci_hi": 17.30676814742321,
      "sanity_flag": "OK"
    },
    {
      "scenario": "low_demand",
      "pct_fuel_reduction_vs_fixed": 14.458181031777709,
      "ci_lo": 13.983862977178838,
      "ci_hi": 14.907851787963828,
      "sanity_flag": "OK"
    },
    {
      "scenario": "peak_unbalanced",
      "pct_fuel_reduction_vs_fixed": 21.759596013455283,
      "ci_lo": 20.048127006637706,
      "ci_hi": 23.538508826993734,
      "sanity_flag": "OK"
    }
  ]
}
```


## Limitations


- Simulation-to-reality gap; emission model not calibrated to Indian vehicles.

- Assumed vehicle mix unless observed counts provided.

- No pedestrians; simplified turning/phase plan; single-city context.

- Perception noise without user video is assumed.


## Threats to validity


- Internal: seed leakage prevented by config.lock; demand independent of controller.

- Construct: HBEFA proxies idle/fuel; SSM conflicts are model-based.

- External: Indian arterial heterogeneity not fully represented.


## Q&A cheat sheet


**How is fuel computed?** SUMO emission devices (HBEFA classes mapped at runtime); mg converted to litres via petrol/diesel densities in config.


**Is it AI?** Perception path uses YOLO; controller is fuel-weighted pressure (interpretable). RL-PPO is an additional baseline.


**Why not RL?** See RL comparison tables; PPO is trained/selected on TRAIN/VALIDATION and reported honestly if it underperforms ours_fuel.


**What about deployment?** Requires detectors (or camera+YOLO), TraCI/edge controller, and local calibration; results are simulation-based estimates.


**What about Indian traffic?** Assumed mix with 2W/auto; sublane model when stable; left-hand traffic.


**Biggest limitation?** Emission classes and mix are not field-calibrated.


**Did you tune on test data?** No. Tuning and RL selection use VALIDATION seeds only; TEST seeds touched after config.lock.

