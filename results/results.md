# Simulation Results

Consolidated tables for the manuscript revision. Each section is written
by its own experiment script (Tasks 1-4); re-running a script replaces
only its own section. Numbers are produced locally by the reader -- see
the README RUN INSTRUCTIONS.


<!-- BEGIN Task 1 -->
## Task 1: E91 resource cost and SKR under the calibrated threshold S*

_Last written: 2026-07-19 01:11._

### FPR-vs-K and FNR-vs-K (calibrated S* vs old fixed S=2.0)

| Curve | Channel | K | Fixed2.0 rate | Sstar rate |
| --- | --- | --- | --- | --- |
| FNR | Ideal_0%(p=0.0) | 100 | 0.165 | 0.125 |
| FNR | Ideal_0%(p=0.0) | 200 | 0.075 | 0.020 |
| FNR | Ideal_0%(p=0.0) | 300 | 0.025 | 0.015 |
| FNR | Ideal_0%(p=0.0) | 500 | 0.010 | 0.000 |
| FNR | Ideal_0%(p=0.0) | 1000 | 0.000 | 0.000 |
| FNR | Ideal_0%(p=0.0) | 2000 | 0.000 | 0.000 |
| FNR | Ideal_0%(p=0.0) | 3000 | 0.000 | 0.000 |
| FPR | Noise_5%(p=0.1) | 100 | 0.245 | 0.125 |
| FPR | Noise_5%(p=0.1) | 200 | 0.195 | 0.075 |
| FPR | Noise_5%(p=0.1) | 300 | 0.135 | 0.030 |
| FPR | Noise_5%(p=0.1) | 500 | 0.125 | 0.000 |
| FPR | Noise_5%(p=0.1) | 1000 | 0.035 | 0.000 |
| FPR | Noise_5%(p=0.1) | 2000 | 0.000 | 0.000 |
| FPR | Noise_5%(p=0.1) | 3000 | 0.005 | 0.000 |
| FPR | Threshold_11%(p=0.22) | 100 | 0.670 | 0.210 |
| FPR | Threshold_11%(p=0.22) | 200 | 0.830 | 0.125 |
| FPR | Threshold_11%(p=0.22) | 300 | 0.810 | 0.115 |
| FPR | Threshold_11%(p=0.22) | 500 | 0.895 | 0.060 |
| FPR | Threshold_11%(p=0.22) | 1000 | 0.940 | 0.000 |
| FPR | Threshold_11%(p=0.22) | 2000 | 0.980 | 0.000 |
| FPR | Threshold_11%(p=0.22) | 3000 | 0.995 | 0.000 |

### Smallest swept K with FPR <= 5% (read S* next to fixed 2.0)

| Threshold_Mode | Channel | First K with FPR<=5% |
| --- | --- | --- |
| Fixed2.0 | Noise_5%(p=0.1) | 1000 |
| Fixed2.0 | Threshold_11%(p=0.22) | none in grid |
| Sstar | Noise_5%(p=0.1) | 300 |
| Sstar | Threshold_11%(p=0.22) | 1000 |

### E91 SKR at standard operating points (8192 pairs, threshold-independent)

| Noise_Profile | F_Eve | Mean_S | Mean_SKR | Std_SKR |
| --- | --- | --- | --- | --- |
| Ideal_0% | 0.0 | 2.8268 | 0.2213 | 0.0043 |
| Ideal_0% | 1.0 | 1.4198 | 0.0000 | 0.0000 |
| Noise_2% | 0.0 | 2.6011 | 0.1175 | 0.0091 |
| Noise_2% | 1.0 | 1.3179 | 0.0000 | 0.0000 |
| Noise_5% | 0.0 | 2.2886 | 0.0198 | 0.0092 |
| Noise_5% | 1.0 | 1.1458 | 0.0000 | 0.0000 |
| Noise_8% | 0.0 | 1.9849 | 0.0000 | 0.0000 |
| Noise_8% | 1.0 | 0.9981 | 0.0000 | 0.0000 |
| Threshold_11% | 0.0 | 1.7281 | 0.0000 | 0.0000 |
| Threshold_11% | 1.0 | 0.8591 | 0.0000 | 0.0000 |
<!-- END Task 1 -->

<!-- BEGIN Task 2 -->
## Task 2: High-trial CI reruns, convergence, and Welch test

_Last written: 2026-07-19 01:11._

Headline metrics with 95% t-distribution confidence intervals (200 trials/config). Full per-trial raw values, including the finite-key fields `N, n_sift, m, n_key, Q, leak_EC`, are in `ci_pertrial_fsweep_ideal.csv` and `ci_pertrial_fpr_noise.csv`; running mean/SE at 10/25/50/100/200 trials are in `ci_convergence.csv`.

### Mean and 95% CI per configuration

| Protocol | Sweep | Config | Metric | Mean | 95% CI |
| --- | --- | --- | --- | --- | --- |
| BB84 | sweep_a | f=0.0 | QBER | 0.0000 | [0.0000, 0.0000] |
| BB84 | sweep_a | f=0.0 | SKR | 0.4997 | [0.4975, 0.5020] |
| BB84 | sweep_a | f=0.0 | FPR | 0.0000 | [0.0000, 0.0000] |
| BB84 | sweep_a | f=0.1 | QBER | 0.0249 | [0.0240, 0.0258] |
| BB84 | sweep_a | f=0.1 | SKR | 0.3330 | [0.3280, 0.3381] |
| BB84 | sweep_a | f=0.1 | FNR | 1.0000 | [1.0000, 1.0000] |
| BB84 | sweep_a | f=0.2 | QBER | 0.0494 | [0.0481, 0.0507] |
| BB84 | sweep_a | f=0.2 | SKR | 0.2175 | [0.2117, 0.2233] |
| BB84 | sweep_a | f=0.2 | FNR | 1.0000 | [1.0000, 1.0000] |
| BB84 | sweep_a | f=0.3 | QBER | 0.0747 | [0.0730, 0.0764] |
| BB84 | sweep_a | f=0.3 | SKR | 0.1185 | [0.1123, 0.1246] |
| BB84 | sweep_a | f=0.3 | FNR | 1.0000 | [1.0000, 1.0000] |
| BB84 | sweep_a | f=0.4 | QBER | 0.1001 | [0.0981, 0.1020] |
| BB84 | sweep_a | f=0.4 | SKR | 0.0386 | [0.0335, 0.0436] |
| BB84 | sweep_a | f=0.4 | FNR | 0.9850 | [0.9680, 1.0020] |
| BB84 | sweep_a | f=0.5 | QBER | 0.1226 | [0.1205, 0.1246] |
| BB84 | sweep_a | f=0.5 | SKR | 0.0047 | [0.0029, 0.0066] |
| BB84 | sweep_a | f=0.5 | FNR | 0.8000 | [0.7441, 0.8559] |
| BB84 | sweep_a | f=0.6 | QBER | 0.1487 | [0.1464, 0.1510] |
| BB84 | sweep_a | f=0.6 | SKR | 0.0001 | [-0.0001, 0.0004] |
| BB84 | sweep_a | f=0.6 | FNR | 0.2100 | [0.1531, 0.2669] |
| BB84 | sweep_a | f=0.7 | QBER | 0.1735 | [0.1711, 0.1758] |
| BB84 | sweep_a | f=0.7 | SKR | 0.0000 | [0.0000, 0.0000] |
| BB84 | sweep_a | f=0.7 | FNR | 0.0100 | [-0.0039, 0.0239] |
| BB84 | sweep_a | f=0.8 | QBER | 0.1965 | [0.1940, 0.1990] |
| BB84 | sweep_a | f=0.8 | SKR | 0.0000 | [0.0000, 0.0000] |
| BB84 | sweep_a | f=0.8 | FNR | 0.0000 | [0.0000, 0.0000] |
| BB84 | sweep_a | f=0.9 | QBER | 0.2237 | [0.2209, 0.2265] |
| BB84 | sweep_a | f=0.9 | SKR | 0.0000 | [0.0000, 0.0000] |
| BB84 | sweep_a | f=0.9 | FNR | 0.0000 | [0.0000, 0.0000] |
| BB84 | sweep_a | f=1.0 | QBER | 0.2487 | [0.2458, 0.2515] |
| BB84 | sweep_a | f=1.0 | SKR | 0.0000 | [0.0000, 0.0000] |
| BB84 | sweep_a | f=1.0 | FNR | 0.0000 | [0.0000, 0.0000] |
| Six-State | sweep_a | f=0.0 | QBER | 0.0000 | [0.0000, 0.0000] |
| Six-State | sweep_a | f=0.0 | SKR | 0.3324 | [0.3304, 0.3345] |
| Six-State | sweep_a | f=0.0 | FPR | 0.0000 | [0.0000, 0.0000] |
| Six-State | sweep_a | f=0.1 | QBER | 0.0329 | [0.0315, 0.0343] |
| Six-State | sweep_a | f=0.1 | SKR | 0.1952 | [0.1905, 0.1998] |
| Six-State | sweep_a | f=0.1 | FNR | 1.0000 | [1.0000, 1.0000] |
| Six-State | sweep_a | f=0.2 | QBER | 0.0676 | [0.0659, 0.0694] |
| Six-State | sweep_a | f=0.2 | SKR | 0.0962 | [0.0918, 0.1006] |
| Six-State | sweep_a | f=0.2 | FNR | 1.0000 | [1.0000, 1.0000] |
| Six-State | sweep_a | f=0.3 | QBER | 0.1002 | [0.0979, 0.1025] |
| Six-State | sweep_a | f=0.3 | SKR | 0.0276 | [0.0239, 0.0312] |
| Six-State | sweep_a | f=0.3 | FNR | 1.0000 | [1.0000, 1.0000] |
| Six-State | sweep_a | f=0.4 | QBER | 0.1318 | [0.1291, 0.1344] |
| Six-State | sweep_a | f=0.4 | SKR | 0.0020 | [0.0010, 0.0030] |
| Six-State | sweep_a | f=0.4 | FNR | 0.9600 | [0.9326, 0.9874] |
| Six-State | sweep_a | f=0.5 | QBER | 0.1658 | [0.1629, 0.1686] |
| Six-State | sweep_a | f=0.5 | SKR | 0.0000 | [0.0000, 0.0000] |
| Six-State | sweep_a | f=0.5 | FNR | 0.5050 | [0.4351, 0.5749] |
| Six-State | sweep_a | f=0.6 | QBER | 0.1985 | [0.1957, 0.2013] |
| Six-State | sweep_a | f=0.6 | SKR | 0.0000 | [0.0000, 0.0000] |
| Six-State | sweep_a | f=0.6 | FNR | 0.0450 | [0.0160, 0.0740] |
| Six-State | sweep_a | f=0.7 | QBER | 0.2301 | [0.2269, 0.2333] |
| Six-State | sweep_a | f=0.7 | SKR | 0.0000 | [0.0000, 0.0000] |
| Six-State | sweep_a | f=0.7 | FNR | 0.0000 | [0.0000, 0.0000] |
| Six-State | sweep_a | f=0.8 | QBER | 0.2685 | [0.2651, 0.2718] |
| Six-State | sweep_a | f=0.8 | SKR | 0.0000 | [0.0000, 0.0000] |
| Six-State | sweep_a | f=0.8 | FNR | 0.0000 | [0.0000, 0.0000] |
| Six-State | sweep_a | f=0.9 | QBER | 0.3021 | [0.2986, 0.3055] |
| Six-State | sweep_a | f=0.9 | SKR | 0.0000 | [0.0000, 0.0000] |
| Six-State | sweep_a | f=0.9 | FNR | 0.0000 | [0.0000, 0.0000] |
| Six-State | sweep_a | f=1.0 | QBER | 0.3322 | [0.3286, 0.3357] |
| Six-State | sweep_a | f=1.0 | SKR | 0.0000 | [0.0000, 0.0000] |
| Six-State | sweep_a | f=1.0 | FNR | 0.0000 | [0.0000, 0.0000] |
| E91 | sweep_a | f=0.0 | CHSH_S | 2.8331 | [2.8270, 2.8392] |
| E91 | sweep_a | f=0.0 | SKR | 0.2222 | [0.2215, 0.2228] |
| E91 | sweep_a | f=0.0 | FPR | 0.0000 | [0.0000, 0.0000] |
| E91 | sweep_a | f=0.1 | CHSH_S | 2.6856 | [2.6792, 2.6921] |
| E91 | sweep_a | f=0.1 | SKR | 0.1582 | [0.1570, 0.1595] |
| E91 | sweep_a | f=0.1 | FNR | 1.0000 | [1.0000, 1.0000] |
| E91 | sweep_a | f=0.2 | CHSH_S | 2.5525 | [2.5449, 2.5601] |
| E91 | sweep_a | f=0.2 | SKR | 0.1100 | [0.1087, 0.1114] |
| E91 | sweep_a | f=0.2 | FNR | 1.0000 | [1.0000, 1.0000] |
| E91 | sweep_a | f=0.3 | CHSH_S | 2.4126 | [2.4053, 2.4200] |
| E91 | sweep_a | f=0.3 | SKR | 0.0720 | [0.0707, 0.0733] |
| E91 | sweep_a | f=0.3 | FNR | 1.0000 | [1.0000, 1.0000] |
| E91 | sweep_a | f=0.4 | CHSH_S | 2.2713 | [2.2639, 2.2788] |
| E91 | sweep_a | f=0.4 | SKR | 0.0390 | [0.0377, 0.0403] |
| E91 | sweep_a | f=0.4 | FNR | 1.0000 | [1.0000, 1.0000] |
| E91 | sweep_a | f=0.5 | CHSH_S | 2.1258 | [2.1183, 2.1333] |
| E91 | sweep_a | f=0.5 | SKR | 0.0092 | [0.0080, 0.0104] |
| E91 | sweep_a | f=0.5 | FNR | 0.5400 | [0.4703, 0.6097] |
| E91 | sweep_a | f=0.6 | CHSH_S | 1.9856 | [1.9777, 1.9934] |
| E91 | sweep_a | f=0.6 | SKR | 0.0000 | [-0.0000, 0.0001] |
| E91 | sweep_a | f=0.6 | FNR | 0.0200 | [0.0004, 0.0396] |
| E91 | sweep_a | f=0.7 | CHSH_S | 1.8446 | [1.8370, 1.8521] |
| E91 | sweep_a | f=0.7 | SKR | 0.0000 | [0.0000, 0.0000] |
| E91 | sweep_a | f=0.7 | FNR | 0.0000 | [0.0000, 0.0000] |
| E91 | sweep_a | f=0.8 | CHSH_S | 1.7034 | [1.6952, 1.7117] |
| E91 | sweep_a | f=0.8 | SKR | 0.0000 | [0.0000, 0.0000] |
| E91 | sweep_a | f=0.8 | FNR | 0.0000 | [0.0000, 0.0000] |
| E91 | sweep_a | f=0.9 | CHSH_S | 1.5573 | [1.5485, 1.5661] |
| E91 | sweep_a | f=0.9 | SKR | 0.0000 | [0.0000, 0.0000] |
| E91 | sweep_a | f=0.9 | FNR | 0.0000 | [0.0000, 0.0000] |
| E91 | sweep_a | f=1.0 | CHSH_S | 1.4174 | [1.4088, 1.4260] |
| E91 | sweep_a | f=1.0 | SKR | 0.0000 | [0.0000, 0.0000] |
| E91 | sweep_a | f=1.0 | FNR | 0.0000 | [0.0000, 0.0000] |
| BB84 | sweep_b | p=0.0 | QBER | 0.0000 | [0.0000, 0.0000] |
| BB84 | sweep_b | p=0.0 | SKR | 0.5009 | [0.4985, 0.5033] |
| BB84 | sweep_b | p=0.0 | FPR | 0.0000 | [0.0000, 0.0000] |
| BB84 | sweep_b | p=0.04 | QBER | 0.0195 | [0.0187, 0.0203] |
| BB84 | sweep_b | p=0.04 | SKR | 0.3630 | [0.3579, 0.3680] |
| BB84 | sweep_b | p=0.04 | FPR | 0.0000 | [0.0000, 0.0000] |
| BB84 | sweep_b | p=0.1 | QBER | 0.0491 | [0.0478, 0.0503] |
| BB84 | sweep_b | p=0.1 | SKR | 0.2186 | [0.2132, 0.2240] |
| BB84 | sweep_b | p=0.1 | FPR | 0.0000 | [0.0000, 0.0000] |
| BB84 | sweep_b | p=0.16 | QBER | 0.0798 | [0.0781, 0.0815] |
| BB84 | sweep_b | p=0.16 | SKR | 0.1002 | [0.0941, 0.1064] |
| BB84 | sweep_b | p=0.16 | FPR | 0.0000 | [0.0000, 0.0000] |
| BB84 | sweep_b | p=0.22 | QBER | 0.1111 | [0.1091, 0.1131] |
| BB84 | sweep_b | p=0.22 | SKR | 0.0161 | [0.0125, 0.0196] |
| BB84 | sweep_b | p=0.22 | FPR | 0.0550 | [0.0231, 0.0869] |
| Six-State | sweep_b | p=0.0 | QBER | 0.0000 | [0.0000, 0.0000] |
| Six-State | sweep_b | p=0.0 | SKR | 0.3340 | [0.3319, 0.3361] |
| Six-State | sweep_b | p=0.0 | FPR | 0.0000 | [0.0000, 0.0000] |
| Six-State | sweep_b | p=0.04 | QBER | 0.0198 | [0.0186, 0.0209] |
| Six-State | sweep_b | p=0.04 | SKR | 0.2417 | [0.2372, 0.2462] |
| Six-State | sweep_b | p=0.04 | FPR | 0.0000 | [0.0000, 0.0000] |
| Six-State | sweep_b | p=0.1 | QBER | 0.0481 | [0.0465, 0.0496] |
| Six-State | sweep_b | p=0.1 | SKR | 0.1487 | [0.1443, 0.1531] |
| Six-State | sweep_b | p=0.1 | FPR | 0.0000 | [0.0000, 0.0000] |
| Six-State | sweep_b | p=0.16 | QBER | 0.0795 | [0.0774, 0.0816] |
| Six-State | sweep_b | p=0.16 | SKR | 0.0683 | [0.0637, 0.0729] |
| Six-State | sweep_b | p=0.16 | FPR | 0.0000 | [0.0000, 0.0000] |
| Six-State | sweep_b | p=0.22 | QBER | 0.1112 | [0.1091, 0.1134] |
| Six-State | sweep_b | p=0.22 | SKR | 0.0117 | [0.0093, 0.0141] |
| Six-State | sweep_b | p=0.22 | FPR | 0.0050 | [-0.0049, 0.0149] |
| E91 | sweep_b | p=0.0 | CHSH_S | 2.8247 | [2.8180, 2.8315] |
| E91 | sweep_b | p=0.0 | SKR | 0.2222 | [0.2215, 0.2228] |
| E91 | sweep_b | p=0.0 | FPR | 0.0000 | [0.0000, 0.0000] |
| E91 | sweep_b | p=0.04 | CHSH_S | 2.6053 | [2.5977, 2.6129] |
| E91 | sweep_b | p=0.04 | SKR | 0.1168 | [0.1153, 0.1183] |
| E91 | sweep_b | p=0.04 | FPR | 0.0000 | [0.0000, 0.0000] |
| E91 | sweep_b | p=0.1 | CHSH_S | 2.2863 | [2.2786, 2.2941] |
| E91 | sweep_b | p=0.1 | SKR | 0.0213 | [0.0200, 0.0227] |
| E91 | sweep_b | p=0.1 | FPR | 0.0000 | [0.0000, 0.0000] |
| E91 | sweep_b | p=0.16 | CHSH_S | 2.0018 | [1.9940, 2.0095] |
| E91 | sweep_b | p=0.16 | SKR | 0.0000 | [0.0000, 0.0000] |
| E91 | sweep_b | p=0.16 | FPR | 0.0000 | [0.0000, 0.0000] |
| E91 | sweep_b | p=0.22 | CHSH_S | 1.7185 | [1.7092, 1.7277] |
| E91 | sweep_b | p=0.22 | SKR | 0.0000 | [0.0000, 0.0000] |
| E91 | sweep_b | p=0.22 | FPR | 0.0000 | [0.0000, 0.0000] |

### Welch's t-test: six-state vs BB84 FNR at f = 0.5 (ideal channel)

- mean FNR six-state = 0.5050, mean FNR BB84 = 0.8000
- Welch t = -6.4993, dof = 379.71, p-value = 2.539e-10
<!-- END Task 2 -->

<!-- BEGIN Task 3 -->
## Task 3: Configuration and reproducibility report

_Last written: 2026-07-19 01:11._

### Software versions (runtime)

| Component | Version |
| --- | --- |
| Python | 3.14.0 (Windows 11) |
| numpy | 2.4.6 |
| qiskit | 2.4.1 |
| qiskit-aer | 0.17.2 |
| qiskit-ibm-runtime | 0.47.0 |
| scipy | 1.17.1 |

### Reproducibility facts (static code facts)

| Item | Value |
| --- | --- |
| Shots per circuit | BB84/six-state: `shots=1` per batched circuit (one run per qubit batch); E91: `shots=count`, one shot per entangled pair |
| Transpiler optimization_level | not applied (no explicit `transpile` step; circuits handed to `AerSimulator.run()` with Aer defaults) |
| Random seed policy | NumPy global RNG seeded per configuration (`np.random.seed(seed)`); ci_reruns.py seeds per trial (`base_seed + trial`); Aer given no `seed_simulator` |
| Error-reconciliation block size | 8 (`error_reconciliation(..., block_size=8)`), Cascade-style: 1 parity bit/block + binary-search bits on a mismatch |
| Parity bits disclosed | data-dependent runtime count (`disclosed_bits`); logged per trial as `leak_EC` by ci_reruns.py |
| Reconciliation simulated vs approximated | PROCEDURE is simulated (block parity + binary search + bit flips + SHA-256 privacy amplification); the asymptotic SKR leakage is the analytic `2*H2(QBER)` approximation |
| Leakage into SKR | asymptotic SKR uses `1 - 2*H2(QBER)` (Shor-Preskill); the finite-key SKR (Task 4) uses the real simulated `leak_EC` term instead |
<!-- END Task 3 -->

<!-- BEGIN Task 4 -->
## Task 4: Finite-key secure key rate

_Last written: 2026-07-19 01:11._

Finite-key secure key rate (Hoeffding-corrected parameter estimation, eps_PE = eps_sec = eps_cor = 1e-10) next to the asymptotic value, at the standard operating points. Per-configuration means and 95% CIs are in `finite_key_summary.csv`; the block-size zero crossings are in `finite_key_zero_crossing.csv`.

### Finite-key vs asymptotic SKR at standard operating points

| Protocol | N | F_Eve | Mean_Q | Mean_SKR_finite | 95% CI (finite) | Mean_SKR_asymptotic |
| --- | --- | --- | --- | --- | --- | --- |
| BB84 | 1000 | 0 | 0.00000 | 0.00000000 | [0.00000000, 0.00000000] | 0.499740 |
| BB84 | 1000 | 0.1 | 0.02488 | 0.00000000 | [0.00000000, 0.00000000] | 0.333038 |
| Six-State | 1000 | 0 | 0.00000 | 0.00000000 | [0.00000000, 0.00000000] | 0.332425 |
| Six-State | 1000 | 0.1 | 0.03291 | 0.00000000 | [0.00000000, 0.00000000] | 0.195152 |
| E91 | 8192 | 0 | 0.00000 | 0.00000000 | [0.00000000, 0.00000000] | 0.222151 |
| E91 | 8192 | 0.1 | 0.02054 | 0.00000000 | [0.00000000, 0.00000000] | 0.158223 |

### Block size N at which finite-key SKR first exceeds zero (analytic scaling at observed Q)

| Protocol | Channel | F_Eve | Observed_Q | N (finite-key SKR > 0) |
| --- | --- | --- | --- | --- |
| BB84 | Ideal_0% | 0 | 0.000000 | 6553 |
| BB84 | Ideal_0% | 0.1 | 0.024876 | 16201 |
| Six-State | Ideal_0% | 0 | 0.000000 | 9874 |
| Six-State | Ideal_0% | 0.1 | 0.032911 | 35945 |
| E91 | Ideal_0% | 0 | 0.000000 | 14674 |
| E91 | Ideal_0% | 0.1 | 0.020544 | 29759 |

_Note: at N = 1000 (BB84/six-state) and N = 8192 pairs (E91) the statistical fluctuation term mu dominates, so the finite-key SKR is 0 at the standard operating points; it turns positive only at the larger block sizes in the crossing table._
<!-- END Task 4 -->
