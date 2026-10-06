# XtraFlow — Research Report

**Label:** Simulation-based estimate; not a real-world deployment result. Assumed mixed-traffic scenario unless observed counts provided.

## Abstract

We evaluate an adaptive, fuel-weighted pressure traffic signal controller (XtraFlow) against legacy fixed-time, a validation-tuned fixed plan, Webster, SUMO-actuated, queue-pressure, max-pressure, and a count-only ablation. PPO was trained to the configured step budget and is not in this TEST comparison. Controllers use an oracle detector (SUMO speed, class, and route turn) unless info_mode is camera. Emission classes are proxies. Simulation-based estimate; assumed traffic mix. 
Sublane actually used: True. 
 On `balanced`, mean fuel change versus `maxpressure` was 0.30% (95% CI [-0.38, 1.01]; flag=OK).
 On `dynamic`, mean fuel change versus `maxpressure` was 1.09% (95% CI [0.65, 1.70]; flag=OK).
 On `low_demand`, mean fuel change versus `maxpressure` was 1.91% (95% CI [0.51, 3.04]; flag=OK).
 On `peak_unbalanced`, mean fuel change versus `maxpressure` was 0.69% (95% CI [-0.35, 1.77]; flag=OK).


## Method

- Single 4-arm intersection; left-hand traffic; yellow 3 s; all-red 2 s. Grid numbers are reported only from results/grid_results.json.

- Seed protocol: TRAIN 1000–1049, VALIDATION 2000–2019, TEST 1–5 (5 seeds in raw_runs.csv) after config.lock.

- Metrics from tripinfo with device.emissions.probability=1; fuel mg→L via densities.

- Sublane model used: True.

- Emission class map (primary): `{"two_wheeler": "HBEFA3/LDV_G_EU4", "auto_rickshaw": "HBEFA3/PC_G_EU4", "car": "HBEFA3/PC_G_EU4", "bus": "HBEFA3/Bus", "truck": "HBEFA3/HDV"}`.


## Assumptions

| Parameter | Value | Source |
|---|---|---|

| Vehicle mix | 2W 40 / car 30 / auto 10 / bus 5 / truck 15 | assumed |

| Occupancy | 1.3 / 2.0 / 2.0 / 40 / 1.2 | assumed |

| Fuel densities | petrol 0.74, diesel 0.84 kg/L | assumed |

| Geometry | 300 m approaches, 3 in / 2 out lanes | assumed |

| Demand mode | measured_on_validation | Approach veh/h are counts of vehicles seen on each incoming edge, scaled to an hour from the simulated duration. Degree of saturation uses an assumed 1800 veh/h/lane and the green fraction served. The config demand table is not copied into measured_approach_veh_h. |


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
  "note": "Measured via TraCI getFuelConsumption while stopped. auto-rickshaw uses a passenger-car emission class and two-wheeler uses LDV_G_EU4 when that class loads; these idle-fuel weights inherit those proxies. Simulation-based estimate; assumed traffic mix."
}

```


## Tuned parameters (VALIDATION only)

```

{
  "detection_distance_m": 150,
  "alpha_moving": 0.5,
  "hysteresis": 0.25,
  "selected_on": "VALIDATION seeds only",
  "scenarios": [
    "balanced",
    "peak_unbalanced",
    "dynamic",
    "low_demand"
  ],
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
  "mean_fuel_per_vehicle_L": 0.12327643280361333,
  "screen_relative_span": 0.013761764847601068,
  "n_screen_combos": 27,
  "smoke": false
}

```


## Per-scenario results (mean±std)


| scenario        | controller     |   n |   fuel_per_vehicle_L_mean |   fuel_per_vehicle_L_std |   total_CO2_kg_mean |   total_CO2_kg_std |   mean_waiting_s_mean |   mean_waiting_s_std |   p95_waiting_s_mean |   p95_waiting_s_std |   mean_queue_veh_mean |   mean_queue_veh_std |   n_completed_mean |   n_completed_std |   n_unfinished_mean |   n_unfinished_std |   gridlock_flag_mean |   gridlock_flag_std |   ssm_conflicts_mean |   ssm_conflicts_std |
|:----------------|:---------------|----:|--------------------------:|-------------------------:|--------------------:|-------------------:|----------------------:|---------------------:|---------------------:|--------------------:|----------------------:|---------------------:|-------------------:|------------------:|--------------------:|-------------------:|---------------------:|--------------------:|---------------------:|--------------------:|
| balanced        | fixed          |   5 |                  0.141919 |               0.00371389 |             685.837 |           31.1984  |               30.0277 |             1.26806  |                 73.8 |            4.43847  |              15.333   |             0.925331 |             1932.2 |           37.3323 |                   0 |                  0 |                    0 |                   0 |               2992   |            126.493  |
| balanced        | fixed_tuned    |   5 |                  0.141359 |               0.00283377 |             683.303 |           26.287   |               28.7274 |             0.559475 |                 67.2 |            0.447214 |              14.9333  |             0.492688 |             1932.2 |           37.3323 |                   0 |                  0 |                    0 |                   0 |               3069.2 |            151.759  |
| balanced        | actuated       |   5 |                  0.13723  |               0.00177556 |             663.123 |           21.1561  |               26.1047 |             0.445988 |                 62.2 |            0.83666  |              13.6325  |             0.354022 |             1932.2 |           37.3323 |                   0 |                  0 |                    0 |                   0 |               2928.8 |            133.618  |
| balanced        | webster        |   5 |                  0.143443 |               0.00281791 |             693.587 |           27.1856  |               28.8671 |             0.448629 |                 61   |            0.707107 |              15.0257  |             0.457958 |             1932.2 |           37.3323 |                   0 |                  0 |                    0 |                   0 |               3266.8 |            116.076  |
| balanced        | queue_pressure |   5 |                  0.131003 |               0.00179025 |             633.489 |           20.7878  |               21.3651 |             0.448953 |                 77.2 |            3.34664  |              11.1353  |             0.245167 |             1932.2 |           37.3323 |                   0 |                  0 |                    0 |                   0 |               2538.8 |            101.08   |
| balanced        | maxpressure    |   5 |                  0.131003 |               0.00179025 |             633.489 |           20.7878  |               21.3651 |             0.448953 |                 77.2 |            3.34664  |              11.1353  |             0.245167 |             1932.2 |           37.3323 |                   0 |                  0 |                    0 |                   0 |               2538.8 |            101.08   |
| balanced        | ours_count     |   5 |                  0.131089 |               0.00216344 |             633.928 |           21.5611  |               21.3428 |             0.436245 |                 78   |            2.54951  |              11.1094  |             0.306849 |             1932.2 |           37.3323 |                   0 |                  0 |                    0 |                   0 |               2546.8 |             94.7059 |
| balanced        | XtraFlow       |   5 |                  0.130612 |               0.0017711  |             631.069 |           21.5792  |               21.7883 |             0.424012 |                 73.4 |            1.34164  |              11.3502  |             0.348273 |             1932.2 |           37.3323 |                   0 |                  0 |                    0 |                   0 |               2591.6 |             82.0658 |
| peak_unbalanced | fixed          |   5 |                  0.151162 |               0.00591313 |             679.431 |           26.9478  |               36.9526 |             3.39836  |                110.2 |           27.3624   |              17.4575  |             1.46347  |             1801.4 |           21.2438 |                   0 |                  0 |                    0 |                   0 |               3125.8 |             96.9211 |
| peak_unbalanced | fixed_tuned    |   5 |                  0.137858 |               0.00366985 |             619.991 |           12.0939  |               28.141  |             1.22182  |                 77.6 |            2.07364  |              13.6022  |             0.559678 |             1801.4 |           21.2438 |                   0 |                  0 |                    0 |                   0 |               2728   |             56.9517 |
| peak_unbalanced | actuated       |   5 |                  0.13611  |               0.00190695 |             612.856 |            9.24416 |               25.3208 |             0.920304 |                 61.4 |            0.547723 |              12.314   |             0.538097 |             1801.4 |           21.2438 |                   0 |                  0 |                    0 |                   0 |               2792.4 |            102.478  |
| peak_unbalanced | webster        |   5 |                  0.138243 |               0.00246212 |             622.258 |            7.33637 |               26.4179 |             0.517538 |                 61.8 |            1.09545  |              12.8414  |             0.263676 |             1801.4 |           21.2438 |                   0 |                  0 |                    0 |                   0 |               2920.2 |            136.023  |
| peak_unbalanced | queue_pressure |   5 |                  0.125404 |               0.00292329 |             564.675 |            7.84695 |               18.1115 |             0.779773 |                 68.8 |            4.08656  |               8.82277 |             0.285753 |             1801.4 |           21.2438 |                   0 |                  0 |                    0 |                   0 |               2208.4 |             29.7456 |
| peak_unbalanced | maxpressure    |   5 |                  0.125404 |               0.00292329 |             564.675 |            7.84695 |               18.1115 |             0.779773 |                 68.8 |            4.08656  |               8.82277 |             0.285753 |             1801.4 |           21.2438 |                   0 |                  0 |                    0 |                   0 |               2208.4 |             29.7456 |
| peak_unbalanced | ours_count     |   5 |                  0.125603 |               0.00271913 |             565.715 |            7.02358 |               18.2265 |             0.507003 |                 70   |            2.54951  |               8.88026 |             0.17991  |             1801.4 |           21.2438 |                   0 |                  0 |                    0 |                   0 |               2168   |             62.8172 |
| peak_unbalanced | XtraFlow       |   5 |                  0.124543 |               0.00351481 |             560.185 |           11.5141  |               18.3722 |             0.774463 |                 70.6 |            1.81659  |               8.95535 |             0.356174 |             1801.4 |           21.2438 |                   0 |                  0 |                    0 |                   0 |               2244.4 |             65.2403 |
| dynamic         | fixed          |   5 |                  0.143904 |               0.00298723 |             631.549 |           22.1963  |               32.1862 |             1.12618  |                 81.4 |            6.10737  |              15.1496  |             0.578419 |             1757.2 |           29.201  |                   0 |                  0 |                    0 |                   0 |               2874.2 |            106.516  |
| dynamic         | fixed_tuned    |   5 |                  0.150542 |               0.0029684  |             660.433 |           22.0436  |               36.9068 |             2.3681   |                 99   |            8        |              17.3349  |             0.994355 |             1757.2 |           29.201  |                   0 |                  0 |                    0 |                   0 |               2977.2 |             78.6174 |
| dynamic         | actuated       |   5 |                  0.13643  |               0.00348899 |             599.261 |           26.2932  |               25.8703 |             0.632416 |                 61.2 |            1.09545  |              12.3169  |             0.389739 |             1757.2 |           29.201  |                   0 |                  0 |                    0 |                   0 |               2766.4 |             95.5945 |
| dynamic         | webster        |   5 |                  0.151002 |               0.005122   |             663.016 |           34.1332  |               34.7427 |             2.04246  |                 83.8 |           13.3679   |              16.4352  |             1.16926  |             1757.2 |           29.201  |                   0 |                  0 |                    0 |                   0 |               3244.8 |            189.97   |
| dynamic         | queue_pressure |   5 |                  0.126232 |               0.00317047 |             554.993 |           23.3084  |               18.5589 |             0.310273 |                 68.2 |            3.11448  |               8.82322 |             0.23784  |             1757.2 |           29.201  |                   0 |                  0 |                    0 |                   0 |               2139.6 |             70.5429 |
| dynamic         | maxpressure    |   5 |                  0.126232 |               0.00317047 |             554.993 |           23.3084  |               18.5589 |             0.310273 |                 68.2 |            3.11448  |               8.82322 |             0.23784  |             1757.2 |           29.201  |                   0 |                  0 |                    0 |                   0 |               2139.6 |             70.5429 |
| dynamic         | ours_count     |   5 |                  0.125022 |               0.00333375 |             549.221 |           23.4025  |               18.4312 |             0.592162 |                 68.8 |            4.91935  |               8.74413 |             0.32188  |             1757.2 |           29.201  |                   0 |                  0 |                    0 |                   0 |               2102.8 |             70.6767 |
| dynamic         | XtraFlow       |   5 |                  0.124853 |               0.00325591 |             548.053 |           23.8466  |               18.81   |             0.332752 |                 70.6 |            1.81659  |               8.94317 |             0.175767 |             1757.2 |           29.201  |                   0 |                  0 |                    0 |                   0 |               2139.2 |            108.077  |
| low_demand      | fixed          |   5 |                  0.136329 |               0.00535827 |             205.464 |            9.07916 |               27.2225 |             1.44494  |                 69   |            1.22474  |               4.44159 |             0.230881 |              602.8 |           30.3266 |                   0 |                  0 |                    0 |                   0 |                417.6 |             60.6201 |
| low_demand      | fixed_tuned    |   5 |                  0.133118 |               0.0048656  |             200.781 |           12.2775  |               24.5415 |             1.16478  |                 60   |            1        |               4.02138 |             0.379656 |              602.8 |           30.3266 |                   0 |                  0 |                    0 |                   0 |                382.8 |             59.6423 |
| low_demand      | actuated       |   5 |                  0.131084 |               0.00570023 |             197.746 |           13.7797  |               23.1748 |             1.03395  |                 56.4 |            0.547723 |               3.78633 |             0.317689 |              602.8 |           30.3266 |                   0 |                  0 |                    0 |                   0 |                397   |             54.1756 |
| low_demand      | webster        |   5 |                  0.132538 |               0.00388561 |             199.775 |            9.71825 |               24.0416 |             0.921683 |                 57.6 |            0.547723 |               3.93945 |             0.298008 |              602.8 |           30.3266 |                   0 |                  0 |                    0 |                   0 |                394   |             61.3677 |
| low_demand      | queue_pressure |   5 |                  0.119356 |               0.00581493 |             179.986 |           10.1886  |               15.2287 |             1.05288  |                 57.6 |            7.63544  |               2.50079 |             0.212638 |              602.8 |           30.3266 |                   0 |                  0 |                    0 |                   0 |                238   |             48.3529 |
| low_demand      | maxpressure    |   5 |                  0.119356 |               0.00581493 |             179.986 |           10.1886  |               15.2287 |             1.05288  |                 57.6 |            7.63544  |               2.50079 |             0.212638 |              602.8 |           30.3266 |                   0 |                  0 |                    0 |                   0 |                238   |             48.3529 |
| low_demand      | ours_count     |   5 |                  0.11951  |               0.0059792  |             180.208 |           10.3066  |               15.3518 |             1.05277  |                 58.4 |            7.95613  |               2.52017 |             0.202433 |              602.8 |           30.3266 |                   0 |                  0 |                    0 |                   0 |                237.2 |             49.5702 |
| low_demand      | XtraFlow       |   5 |                  0.11702  |               0.00460451 |             175.992 |           10.0836  |               16.1693 |             0.667017 |                 59.4 |            1.14018  |               2.65471 |             0.23351  |              602.8 |           30.3266 |                   0 |                  0 |                    0 |                   0 |                234   |             38.704  |


## Statistical tests (XtraFlow vs baselines)


| scenario        | baseline       | metric             |   pct_reduction_mean |   pct_reduction_ci_lo |   pct_reduction_ci_hi |   wilcoxon_stat |   p_raw |   cohens_dz |   n_pairs |   p_holm |
|:----------------|:---------------|:-------------------|---------------------:|----------------------:|----------------------:|----------------:|--------:|------------:|----------:|---------:|
| balanced        | fixed          | fuel_per_vehicle_L |             7.93819  |              6.71058  |               9.08539 |               0 |  0.0625 |   -4.65124  |         5 |        1 |
| balanced        | fixed_tuned    | fuel_per_vehicle_L |             7.58857  |              6.65048  |               8.42523 |               0 |  0.0625 |   -5.89147  |         5 |        1 |
| balanced        | webster        | fuel_per_vehicle_L |             8.93394  |              8.43444  |               9.71167 |               0 |  0.0625 |   -8.73082  |         5 |        1 |
| balanced        | actuated       | fuel_per_vehicle_L |             4.82153  |              4.29527  |               5.25047 |               0 |  0.0625 |   -7.80534  |         5 |        1 |
| balanced        | queue_pressure | fuel_per_vehicle_L |             0.295165 |             -0.380924 |               1.0131  |               5 |  0.625  |   -0.332978 |         5 |        1 |
| balanced        | maxpressure    | fuel_per_vehicle_L |             0.295165 |             -0.380924 |               1.0131  |               5 |  0.625  |   -0.332978 |         5 |        1 |
| balanced        | ours_count     | fuel_per_vehicle_L |             0.353543 |             -0.755788 |               1.24958 |               5 |  0.625  |   -0.285252 |         5 |        1 |
| dynamic         | fixed          | fuel_per_vehicle_L |            13.2395   |             12.3303   |              14.308   |               0 |  0.0625 |  -10.3006   |         5 |        1 |
| dynamic         | fixed_tuned    | fuel_per_vehicle_L |            17.0438   |             15.0953   |              18.9426  |               0 |  0.0625 |   -6.35245  |         5 |        1 |
| dynamic         | webster        | fuel_per_vehicle_L |            17.2855   |             15.8235   |              18.7444  |               0 |  0.0625 |   -7.72593  |         5 |        1 |
| dynamic         | actuated       | fuel_per_vehicle_L |             8.48254  |              7.76617  |               9.21374 |               0 |  0.0625 |   -8.28822  |         5 |        1 |
| dynamic         | queue_pressure | fuel_per_vehicle_L |             1.09237  |              0.647048 |               1.70239 |               0 |  0.0625 |   -1.61694  |         5 |        1 |
| dynamic         | maxpressure    | fuel_per_vehicle_L |             1.09237  |              0.647048 |               1.70239 |               0 |  0.0625 |   -1.61694  |         5 |        1 |
| dynamic         | ours_count     | fuel_per_vehicle_L |             0.132786 |             -0.359609 |               0.62518 |               6 |  0.8125 |   -0.21331  |         5 |        1 |
| low_demand      | fixed          | fuel_per_vehicle_L |            14.1478   |             12.715    |              15.4877  |               0 |  0.0625 |   -6.87583  |         5 |        1 |
| low_demand      | fixed_tuned    | fuel_per_vehicle_L |            12.0972   |             11.3836   |              12.8108  |               0 |  0.0625 |  -12.7132   |         5 |        1 |
| low_demand      | webster        | fuel_per_vehicle_L |            11.7264   |             10.9117   |              12.7308  |               0 |  0.0625 |  -11.7439   |         5 |        1 |
| low_demand      | actuated       | fuel_per_vehicle_L |            10.6947   |              8.95637  |              12.433   |               0 |  0.0625 |   -4.21333  |         5 |        1 |
| low_demand      | queue_pressure | fuel_per_vehicle_L |             1.91393  |              0.50983  |               3.03893 |               1 |  0.125  |   -1.14308  |         5 |        1 |
| low_demand      | maxpressure    | fuel_per_vehicle_L |             1.91393  |              0.50983  |               3.03893 |               1 |  0.125  |   -1.14308  |         5 |        1 |
| low_demand      | ours_count     | fuel_per_vehicle_L |             2.03332  |              0.50983  |               3.27372 |               1 |  0.125  |   -1.13313  |         5 |        1 |
| peak_unbalanced | fixed          | fuel_per_vehicle_L |            17.5162   |             14.4282   |              20.3266  |               0 |  0.0625 |   -3.97228  |         5 |        1 |
| peak_unbalanced | fixed_tuned    | fuel_per_vehicle_L |             9.64293  |              8.03889  |              11.247   |               0 |  0.0625 |   -4.37266  |         5 |        1 |
| peak_unbalanced | webster        | fuel_per_vehicle_L |             9.92109  |              8.87416  |              10.5582  |               0 |  0.0625 |   -9.12175  |         5 |        1 |
| peak_unbalanced | actuated       | fuel_per_vehicle_L |             8.50188  |              6.64144  |              10.0216  |               0 |  0.0625 |   -4.11111  |         5 |        1 |
| peak_unbalanced | queue_pressure | fuel_per_vehicle_L |             0.689012 |             -0.354357 |               1.76514 |               3 |  0.3125 |   -0.491294 |         5 |        1 |
| peak_unbalanced | maxpressure    | fuel_per_vehicle_L |             0.689012 |             -0.354357 |               1.76514 |               3 |  0.3125 |   -0.491294 |         5 |        1 |
| peak_unbalanced | ours_count     | fuel_per_vehicle_L |             0.85079  |             -0.13364  |               1.77265 |               3 |  0.3125 |   -0.655749 |         5 |        1 |



## Where XtraFlow loses or ties


- p95_waiting_s vs `fixed_tuned` on `balanced`: -9.24% (CI [-11.04, -7.11])

- p95_waiting_s vs `webster` on `balanced`: -20.35% (CI [-22.78, -17.87])

- p95_waiting_s vs `actuated` on `balanced`: -18.03% (CI [-20.40, -15.66])

- mean_waiting_s vs `queue_pressure` on `balanced`: -2.00% (CI [-3.39, -0.19])

- mean_waiting_s vs `maxpressure` on `balanced`: -2.00% (CI [-3.39, -0.19])

- mean_waiting_s vs `ours_count` on `balanced`: -2.14% (CI [-4.88, 0.39])

- p95_waiting_s vs `actuated` on `dynamic`: -15.41% (CI [-18.50, -12.31])

- mean_waiting_s vs `queue_pressure` on `dynamic`: -1.36% (CI [-2.50, 0.16])

- p95_waiting_s vs `queue_pressure` on `dynamic`: -3.74% (CI [-8.43, 1.49])

- mean_waiting_s vs `maxpressure` on `dynamic`: -1.36% (CI [-2.50, 0.16])

- p95_waiting_s vs `maxpressure` on `dynamic`: -3.74% (CI [-8.43, 1.49])

- mean_waiting_s vs `ours_count` on `dynamic`: -2.12% (CI [-4.32, 0.36])

- p95_waiting_s vs `ours_count` on `dynamic`: -3.06% (CI [-9.39, 3.27])

- p95_waiting_s vs `webster` on `low_demand`: -3.14% (CI [-5.25, -1.38])

- p95_waiting_s vs `actuated` on `low_demand`: -5.31% (CI [-6.33, -4.29])

- mean_waiting_s vs `queue_pressure` on `low_demand`: -6.42% (CI [-10.48, -2.16])

- p95_waiting_s vs `queue_pressure` on `low_demand`: -4.40% (CI [-13.69, 5.28])

- mean_waiting_s vs `maxpressure` on `low_demand`: -6.42% (CI [-10.48, -2.16])

- p95_waiting_s vs `maxpressure` on `low_demand`: -4.40% (CI [-13.69, 5.28])

- mean_waiting_s vs `ours_count` on `low_demand`: -5.58% (CI [-9.96, -1.20])

- p95_waiting_s vs `ours_count` on `low_demand`: -3.08% (CI [-13.23, 6.45])

- p95_waiting_s vs `webster` on `peak_unbalanced`: -14.24% (CI [-15.86, -12.60])

- p95_waiting_s vs `actuated` on `peak_unbalanced`: -14.98% (CI [-16.60, -13.11])

- mean_waiting_s vs `queue_pressure` on `peak_unbalanced`: -1.52% (CI [-4.91, 1.87])

- p95_waiting_s vs `queue_pressure` on `peak_unbalanced`: -3.02% (CI [-10.10, 3.68])

- mean_waiting_s vs `maxpressure` on `peak_unbalanced`: -1.52% (CI [-4.91, 1.87])

- p95_waiting_s vs `maxpressure` on `peak_unbalanced`: -3.02% (CI [-10.10, 3.68])

- mean_waiting_s vs `ours_count` on `peak_unbalanced`: -0.81% (CI [-3.54, 2.10])

- p95_waiting_s vs `ours_count` on `peak_unbalanced`: -1.01% (CI [-5.81, 2.52])


## Ablations


| scenario        |   pct_reduction_fuel_vs_count_mean |     ci_lo |   ci_hi | statement                |
|:----------------|-----------------------------------:|----------:|--------:|:-------------------------|
| balanced        |                           0.353543 | -0.755788 | 1.24958 | no_detectable_difference |
| dynamic         |                           0.132786 | -0.359609 | 0.62518 | no_detectable_difference |
| low_demand      |                           2.03332  |  0.50983  | 3.27372 | fuel_weights_lower_fuel  |
| peak_unbalanced |                           0.85079  | -0.13364  | 1.77265 | no_detectable_difference |



## RL comparison


RL selected on VALIDATION: `{"selected_on": "Final checkpoint at 200704 steps. VALIDATION scoring was stopped before it finished.", "train_seeds": [1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010, 1011, 1012, 1013, 1014, 1015, 1016, 1017, 1018, 1019, 1020, 1021, 1022, 1023, 1024, 1025, 1026, 1027, 1028, 1029, 1030, 1031, 1032, 1033, 1034, 1035, 1036, 1037, 1038, 1039, 1040, 1041, 1042, 1043, 1044, 1045, 1046, 1047, 1048, 1049], "confirm_seeds": [], "scenarios": ["balanced", "peak_unbalanced", "dynamic", "low_demand"], "best_path": "results/rl/ppo_best.zip", "best_val_fuel_per_vehicle_L": null, "smoke": false, "timesteps_budget": 200704, "config_total_timesteps": 200000, "sha256": "277f555ade8cefea0e3ef9519b209ce495907cf9823d1f0e114a9dd1132c4280", "scored_checkpoints": [], "note": "Time cut. This zip is the 200000-step model. It was not scored on VALIDATION or TEST, so rl_ppo is not in raw_runs.csv."}`.




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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
      "seed": 1,
      "fuel_per_vehicle_L": 0.12618845659970995,
      "total_CO2_kg": 564.3295659810955
    },
    {
      "emission_model": "primary",
      "controller": "XtraFlow",
      "seed": 2,
      "fuel_per_vehicle_L": 0.12250448310524238,
      "total_CO2_kg": 551.4742889253793
    },
    {
      "emission_model": "primary",
      "controller": "XtraFlow",
      "seed": 3,
      "fuel_per_vehicle_L": 0.12194778332190839,
      "total_CO2_kg": 556.0678849473564
    },
    {
      "emission_model": "primary",
      "controller": "XtraFlow",
      "seed": 4,
      "fuel_per_vehicle_L": 0.12602694810995943,
      "total_CO2_kg": 559.6325485755278
    },
    {
      "emission_model": "primary",
      "controller": "XtraFlow",
      "seed": 5,
      "fuel_per_vehicle_L": 0.12366168549966675,
      "total_CO2_kg": 557.9063579381044
    },
    {
      "emission_model": "primary",
      "controller": "XtraFlow",
      "seed": 6,
      "fuel_per_vehicle_L": 0.12437603246507771,
      "total_CO2_kg": 561.7565732305302
    },
    {
      "emission_model": "primary",
      "controller": "XtraFlow",
      "seed": 7,
      "fuel_per_vehicle_L": 0.12312805647124193,
      "total_CO2_kg": 562.7190578233187
    },
    {
      "emission_model": "primary",
      "controller": "XtraFlow",
      "seed": 8,
      "fuel_per_vehicle_L": 0.12113360542286047,
      "total_CO2_kg": 540.5569248398649
    },
    {
      "emission_model": "primary",
      "controller": "XtraFlow",
      "seed": 9,
      "fuel_per_vehicle_L": 0.12098158925839972,
      "total_CO2_kg": 546.5543405455395
    },
    {
      "emission_model": "primary",
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
      "seed": 1,
      "fuel_per_vehicle_L": 0.05854692794684487,
      "total_CO2_kg": 249.9705228002175
    },
    {
      "emission_model": "alternate",
      "controller": "XtraFlow",
      "seed": 2,
      "fuel_per_vehicle_L": 0.058824041165999034,
      "total_CO2_kg": 253.16883061836631
    },
    {
      "emission_model": "alternate",
      "controller": "XtraFlow",
      "seed": 3,
      "fuel_per_vehicle_L": 0.05912079544595832,
      "total_CO2_kg": 257.85334637732774
    },
    {
      "emission_model": "alternate",
      "controller": "XtraFlow",
      "seed": 4,
      "fuel_per_vehicle_L": 0.05869439357718391,
      "total_CO2_kg": 248.81449638835988
    },
    {
      "emission_model": "alternate",
      "controller": "XtraFlow",
      "seed": 5,
      "fuel_per_vehicle_L": 0.058931122118537245,
      "total_CO2_kg": 253.87918406131524
    },
    {
      "emission_model": "alternate",
      "controller": "XtraFlow",
      "seed": 6,
      "fuel_per_vehicle_L": 0.05811069969572346,
      "total_CO2_kg": 250.53919673959206
    },
    {
      "emission_model": "alternate",
      "controller": "XtraFlow",
      "seed": 7,
      "fuel_per_vehicle_L": 0.05883646773140492,
      "total_CO2_kg": 256.98457873170594
    },
    {
      "emission_model": "alternate",
      "controller": "XtraFlow",
      "seed": 8,
      "fuel_per_vehicle_L": 0.05844457065729735,
      "total_CO2_kg": 249.30355417493513
    },
    {
      "emission_model": "alternate",
      "controller": "XtraFlow",
      "seed": 9,
      "fuel_per_vehicle_L": 0.05845595797535595,
      "total_CO2_kg": 252.38554214632293
    },
    {
      "emission_model": "alternate",
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
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
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.0,
      "seed": 1,
      "fuel_per_vehicle_L": 0.12618845659970995,
      "mean_waiting_s": 18.48937360178971
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.0,
      "seed": 2,
      "fuel_per_vehicle_L": 0.12250448310524238,
      "mean_waiting_s": 18.841638981173865
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.0,
      "seed": 3,
      "fuel_per_vehicle_L": 0.12194778332190839,
      "mean_waiting_s": 19.33151283451666
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.0,
      "seed": 4,
      "fuel_per_vehicle_L": 0.12602694810995943,
      "mean_waiting_s": 18.60450704225352
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.0,
      "seed": 5,
      "fuel_per_vehicle_L": 0.12366168549966675,
      "mean_waiting_s": 17.893746541228555
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.0,
      "seed": 6,
      "fuel_per_vehicle_L": 0.12437603246507771,
      "mean_waiting_s": 17.688815060908084
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.0,
      "seed": 7,
      "fuel_per_vehicle_L": 0.12312805647124193,
      "mean_waiting_s": 18.695960698689955
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.0,
      "seed": 8,
      "fuel_per_vehicle_L": 0.12113360542286047,
      "mean_waiting_s": 17.9463687150838
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.0,
      "seed": 9,
      "fuel_per_vehicle_L": 0.12098158925839972,
      "mean_waiting_s": 18.01766004415011
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.0,
      "seed": 10,
      "fuel_per_vehicle_L": 0.12102346823277664,
      "mean_waiting_s": 17.858738135120046
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.1,
      "seed": 1,
      "fuel_per_vehicle_L": 0.12618845659970995,
      "mean_waiting_s": 18.48937360178971
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.1,
      "seed": 2,
      "fuel_per_vehicle_L": 0.12250448310524238,
      "mean_waiting_s": 18.841638981173865
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.1,
      "seed": 3,
      "fuel_per_vehicle_L": 0.12194778332190839,
      "mean_waiting_s": 19.33151283451666
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.1,
      "seed": 4,
      "fuel_per_vehicle_L": 0.12602694810995943,
      "mean_waiting_s": 18.60450704225352
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.1,
      "seed": 5,
      "fuel_per_vehicle_L": 0.12366168549966675,
      "mean_waiting_s": 17.893746541228555
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.1,
      "seed": 6,
      "fuel_per_vehicle_L": 0.12437603246507771,
      "mean_waiting_s": 17.688815060908084
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.1,
      "seed": 7,
      "fuel_per_vehicle_L": 0.12312805647124193,
      "mean_waiting_s": 18.695960698689955
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.1,
      "seed": 8,
      "fuel_per_vehicle_L": 0.12113360542286047,
      "mean_waiting_s": 17.9463687150838
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.1,
      "seed": 9,
      "fuel_per_vehicle_L": 0.12098158925839972,
      "mean_waiting_s": 18.01766004415011
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.1,
      "seed": 10,
      "fuel_per_vehicle_L": 0.12102346823277664,
      "mean_waiting_s": 17.858738135120046
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.2,
      "seed": 1,
      "fuel_per_vehicle_L": 0.12618845659970995,
      "mean_waiting_s": 18.48937360178971
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.2,
      "seed": 2,
      "fuel_per_vehicle_L": 0.12250448310524238,
      "mean_waiting_s": 18.841638981173865
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.2,
      "seed": 3,
      "fuel_per_vehicle_L": 0.12194778332190839,
      "mean_waiting_s": 19.33151283451666
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.2,
      "seed": 4,
      "fuel_per_vehicle_L": 0.1263956010676082,
      "mean_waiting_s": 18.545352112676056
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.2,
      "seed": 5,
      "fuel_per_vehicle_L": 0.12366168549966675,
      "mean_waiting_s": 17.893746541228555
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.2,
      "seed": 6,
      "fuel_per_vehicle_L": 0.12533601760568658,
      "mean_waiting_s": 18.02934662236988
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.2,
      "seed": 7,
      "fuel_per_vehicle_L": 0.1229993013153315,
      "mean_waiting_s": 18.487991266375545
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.2,
      "seed": 8,
      "fuel_per_vehicle_L": 0.12113360542286047,
      "mean_waiting_s": 17.9463687150838
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.2,
      "seed": 9,
      "fuel_per_vehicle_L": 0.12098158925839972,
      "mean_waiting_s": 18.01766004415011
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.2,
      "seed": 10,
      "fuel_per_vehicle_L": 0.12102346823277664,
      "mean_waiting_s": 17.858738135120046
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.3,
      "seed": 1,
      "fuel_per_vehicle_L": 0.1284732628707323,
      "mean_waiting_s": 20.575503355704697
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.3,
      "seed": 2,
      "fuel_per_vehicle_L": 0.12152031144974157,
      "mean_waiting_s": 18.284606866002214
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.3,
      "seed": 3,
      "fuel_per_vehicle_L": 0.12094352821451865,
      "mean_waiting_s": 18.255051884216275
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.3,
      "seed": 4,
      "fuel_per_vehicle_L": 0.12561322799520533,
      "mean_waiting_s": 18.11830985915493
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.3,
      "seed": 5,
      "fuel_per_vehicle_L": 0.12254703634471373,
      "mean_waiting_s": 17.40066408411732
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.3,
      "seed": 6,
      "fuel_per_vehicle_L": 0.12477539064665415,
      "mean_waiting_s": 17.630121816168327
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.3,
      "seed": 7,
      "fuel_per_vehicle_L": 0.12270675299617279,
      "mean_waiting_s": 18.441593886462883
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.3,
      "seed": 8,
      "fuel_per_vehicle_L": 0.12196996027616502,
      "mean_waiting_s": 18.573184357541898
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.3,
      "seed": 9,
      "fuel_per_vehicle_L": 0.12149254557729332,
      "mean_waiting_s": 18.236754966887418
    },
    {
      "kind": "XtraFlow",
      "controller": "XtraFlow",
      "miss": 0.3,
      "seed": 10,
      "fuel_per_vehicle_L": 0.12009051398776388,
      "mean_waiting_s": 16.829704075935233
    },
    {
      "kind": "empirical_noise",
      "controller": "XtraFlow",
      "miss": 0.15,
      "seed": 1,
      "fuel_per_vehicle_L": 0.12692682879109668,
      "mean_waiting_s": 18.614093959731544
    },
    {
      "kind": "empirical_noise",
      "controller": "XtraFlow",
      "miss": 0.15,
      "seed": 2,
      "fuel_per_vehicle_L": 0.12275296958142415,
      "mean_waiting_s": 18.642857142857142
    },
    {
      "kind": "empirical_noise",
      "controller": "XtraFlow",
      "miss": 0.15,
      "seed": 3,
      "fuel_per_vehicle_L": 0.12277198539982055,
      "mean_waiting_s": 18.39759694156199
    },
    {
      "kind": "empirical_noise",
      "controller": "XtraFlow",
      "miss": 0.15,
      "seed": 4,
      "fuel_per_vehicle_L": 0.1255861824463012,
      "mean_waiting_s": 17.310422535211266
    },
    {
      "kind": "empirical_noise",
      "controller": "XtraFlow",
      "miss": 0.15,
      "seed": 5,
      "fuel_per_vehicle_L": 0.12551446731127758,
      "mean_waiting_s": 18.085777531820696
    },
    {
      "kind": "empirical_noise",
      "controller": "XtraFlow",
      "miss": 0.15,
      "seed": 6,
      "fuel_per_vehicle_L": 0.12470462365454357,
      "mean_waiting_s": 17.45736434108527
    },
    {
      "kind": "empirical_noise",
      "controller": "XtraFlow",
      "miss": 0.15,
      "seed": 7,
      "fuel_per_vehicle_L": 0.1224807844233206,
      "mean_waiting_s": 17.699235807860262
    },
    {
      "kind": "empirical_noise",
      "controller": "XtraFlow",
      "miss": 0.15,
      "seed": 8,
      "fuel_per_vehicle_L": 0.1250545497642355,
      "mean_waiting_s": 18.577653631284917
    },
    {
      "kind": "empirical_noise",
      "controller": "XtraFlow",
      "miss": 0.15,
      "seed": 9,
      "fuel_per_vehicle_L": 0.12269001089244436,
      "mean_waiting_s": 18.297461368653423
    },
    {
      "kind": "empirical_noise",
      "controller": "XtraFlow",
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
      "controller": "XtraFlow",
      "seed": 1,
      "fuel_per_vehicle_L": 0.2714619232611139,
      "mean_waiting_s": 114.61581920903954,
      "n_completed": 177,
      "wall_time_s": 1.9202568531036377
    },
    {
      "controller": "XtraFlow",
      "seed": 2,
      "fuel_per_vehicle_L": 0.2722023018005137,
      "mean_waiting_s": 125.1875,
      "n_completed": 192,
      "wall_time_s": 1.829901933670044
    },
    {
      "controller": "XtraFlow",
      "seed": 3,
      "fuel_per_vehicle_L": 0.2691155565445909,
      "mean_waiting_s": 127.02173913043478,
      "n_completed": 184,
      "wall_time_s": 1.799536943435669
    },
    {
      "controller": "XtraFlow",
      "seed": 4,
      "fuel_per_vehicle_L": 0.2650722384469183,
      "mean_waiting_s": 110.61073825503355,
      "n_completed": 149,
      "wall_time_s": 1.7747387886047363
    },
    {
      "controller": "XtraFlow",
      "seed": 5,
      "fuel_per_vehicle_L": 0.2689299050190488,
      "mean_waiting_s": 116.19021739130434,
      "n_completed": 184,
      "wall_time_s": 1.7851362228393555
    },
    {
      "controller": "XtraFlow_coord",
      "seed": 1,
      "fuel_per_vehicle_L": 0.2714619232611139,
      "mean_waiting_s": 114.61581920903954,
      "n_completed": 177,
      "wall_time_s": 1.8435909748077393
    },
    {
      "controller": "XtraFlow_coord",
      "seed": 2,
      "fuel_per_vehicle_L": 0.2722023018005137,
      "mean_waiting_s": 125.1875,
      "n_completed": 192,
      "wall_time_s": 1.8013279438018799
    },
    {
      "controller": "XtraFlow_coord",
      "seed": 3,
      "fuel_per_vehicle_L": 0.2691155565445909,
      "mean_waiting_s": 127.02173913043478,
      "n_completed": 184,
      "wall_time_s": 1.8755676746368408
    },
    {
      "controller": "XtraFlow_coord",
      "seed": 4,
      "fuel_per_vehicle_L": 0.2650722384469183,
      "mean_waiting_s": 110.61073825503355,
      "n_completed": 149,
      "wall_time_s": 1.7674212455749512
    },
    {
      "controller": "XtraFlow_coord",
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
      "XtraFlow": 0.2693563850144371,
      "XtraFlow_coord": 0.2693563850144371
    },
    "mean_waiting_s": {
      "actuated": 18.16023367748438,
      "fixed": 42.60129118090286,
      "XtraFlow": 118.72520279716245,
      "XtraFlow_coord": 118.72520279716245
    },
    "n_completed": {
      "actuated": 192.8,
      "fixed": 187.8,
      "XtraFlow": 177.2,
      "XtraFlow_coord": 177.2
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


## Tuning landscape


Relative span of screened hyperparameter means, (max-min)/min, was 0.0138. Selection used VALIDATION seeds across the scenarios listed in tuned_params.json.


## Q&A


**How is fuel computed?** SUMO emission devices using the classes in results/emission_class_map.json; milligrams converted with the densities in config. Fuel per vehicle uses departed vehicles, including unfinished trips.


**What do the controllers see?** Default info_mode is oracle: SUMO speed, class, and route turn. Camera mode applies perception/noise_model.json. The noise source field says whether that model is empirical or assumed.


**What is the headline comparison?** XtraFlow versus the lowest-fuel controller among fixed_tuned, actuated, queue_pressure, and maxpressure, with a paired bootstrap interval. Legacy fixed is a secondary row. Numbers are in results/headlines.json.


**Did you tune on test data?** Tuning, fixed-plan search, and RL checkpoint selection use VALIDATION seeds only. TEST seeds run once after the config lock.


**What should not be claimed from this file?** Any sentence whose number is not in a results JSON or CSV loaded above. Grid, safety, and robustness verdicts are the fields in those JSON files.

