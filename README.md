# Noise-Aware Simulation and Statistical Eavesdropping Detection in BB84, Six-State, and E91 QKD Protocols

Qiskit simulation framework for a comparative study of three Quantum Key Distribution (QKD) protocols under channel noise and a **partial** intercept-and-resend eavesdropper. For each protocol it measures how reliably an eavesdropper is detected and what that detection costs in usable key.

The three protocols are:

1. **BB84** — prepare-and-measure, two bases
2. **Six-State** — prepare-and-measure, three bases
3. **E91** — entanglement-based, CHSH test

For each protocol the framework records the error indicator (QBER for the two prepare-and-measure protocols, the CHSH value `S` for E91), the secure key rate (SKR), and the two statistical detection metrics — false positive rate (FPR) and false negative rate (FNR). The eavesdropper is parameterized by an interception fraction `f ∈ [0, 1]`, so the same attack ranges from absent to full. Every protocol runs under both a synthetic depolarizing channel and a real-hardware noise model extracted from the `ibm_marrakesh` backend.

This repo tracks a **journal revision** of an accepted conference paper. The central upgrade is a **noise-calibrated CHSH detection threshold `S*`** for E91 that replaces the old fixed classical bound `S < 2.0`, plus **confidence intervals** and **convergence** evidence on every headline result.

---

## 📁 Repository Structure

All simulation and analysis code lives in **`src/`**. The scripts are flat sibling modules that `import` each other by name (e.g. `import detection_aware_qkd_varying_eve as base`), so they must stay together in one folder — they are **not** sorted into sub-packages. All input/output data lives in two folders: the published-figure CSVs in **`data/`** and the manuscript-revision outputs in **`results/`**.

> **Always run scripts from the project root**, e.g. `python src/ci_reruns.py` — never `cd src` first. Every script resolves data paths relative to the working directory (`data/` and `results/`), so the project root must be the current directory.

```
.
├── README.md                              # This guide
├── requirements.txt                       # Pinned dependency versions
├── .gitignore  /  .gitattributes
│
├── src/                                   # ── ALL SOURCE (run from root: `python src/<script>.py`) ──
│   │  · core simulation ·
│   ├── detection_aware_qkd_varying_eve.py # BASE MODULE + Experiment 1 (sweep over f)  -> data/qkd_varying_eve.csv
│   ├── ibm_noise_fetch.py                 # Utility: verify IBM connection / fetch device noise
│   │  · E91 calibrated-threshold (S*) pipeline ·
│   ├── e91_adaptive_threshold.py          # Calibrate S* per profile; FNR-vs-f  -> data/qkd_e91_calibrated.csv, data/qkd_e91_miscalibration.csv
│   ├── e91_resource_cost_calibrated.py    # E91 K-sweep under calibrated S*      -> data/qkd_e91_resource_cost_calibrated.csv
│   ├── e91_resource_cost_sstar.py         # Task 1: S* lookup + fixed-2.0 flag   -> results/qkd_e91_resource_cost_sstar.csv,
│   │                                      #          + SKR operating points         results/qkd_e91_skr_operating_points.csv
│   ├── e91_summary_table_calibrated.py    # Prints the 3 E91 summary-table numbers under S*
│   │  · manuscript-revision analysis (Tasks 1–4) ·
│   ├── ci_reruns.py                       # Task 2: 200-trial CSVs, convergence, 95% CIs, Welch  -> results/ci_*.csv
│   ├── report_config.py                   # Task 3: versions + static config facts (no simulation)
│   ├── finite_key_skr.py                  # Task 4: finite-key SKR from per-trial CSVs  -> results/finite_key_*.csv
│   ├── build_results_md.py                # Rebuild results/results.md from existing CSVs (no simulation)
│   └── results_md.py                      # Shared helper: idempotent results/results.md section writer
│
├── data/                                  # ── INPUT/OUTPUT CSVs for the figure pipeline (CWD-relative from root) ──
│   ├── qkd_varying_eve.csv                # Experiment 1 output (fixed-threshold sweep over f)
│   ├── qkd_resource_cost.csv              # sample-size (K) sweep output
│   ├── qkd_e91_calibrated.csv             # per-profile S* calibration
│   ├── qkd_e91_miscalibration.csv         # S* miscalibration FPR/FNR
│   └── two_step_miscal.csv                # two-step miscalibration data
│
├── results/                               # Output CSVs + results.md (Tasks 1-4). Committed (see note)
├── figures/                               # Figure scripts + generated PDF/SVG/PNG (run: python figures/<script>.py)
├── updates/                               # Revision planning notes, methodology write-ups, task specs
├── Docs/Paper/                            # Manuscripts (.tex), references (.bib), review comments, PDFs
├── Basic Algorithms/                      # Standalone teaching scripts (not part of the pipeline)
└── Old/                                   # Archived earlier scripts & fixed-threshold outputs
```

### Data-file locations (important)

| Location | Files | Read by |
| --- | --- | --- |
| **`data/`** | `qkd_varying_eve.csv`, `qkd_resource_cost.csv`, `qkd_e91_calibrated.csv`, `qkd_e91_miscalibration.csv`, `qkd_e91_resource_cost_calibrated.csv` | the figure scripts in `figures/` and `src/e91_summary_table_calibrated.py` |
| **`results/`** | `qkd_e91_resource_cost_sstar.csv`, `qkd_e91_skr_operating_points.csv`, `ci_*.csv`, `finite_key_*.csv` | collected for the manuscript revision (not consumed by the figure scripts) |

> Source code is under `src/`; the `data/` CSVs feed the published figure pipeline (read/written by working-directory-relative `data/...` paths, so scripts must be run from the project root). New manuscript-revision scripts write fresh outputs to `results/`.

### Basic Algorithms

`Basic Algorithms/` holds five standalone scripts that each demonstrate one concept in isolation (learning aids, not used by the experiments): `bb84_simulation.py`, `bb84_eve_simulation.py`, `bb84_noise_simulation.py`, `e91_simulation.py`, `e91_chsh_simulation.py`.

---

## ⚙️ Installation

Developed and verified on **Python 3.14.0**. A virtual environment is recommended:

```bash
pip install -r requirements.txt
```

`requirements.txt` pins the exact versions used (`qiskit==2.4.1`, `qiskit-aer==0.17.2`, `qiskit-ibm-runtime==0.47.0`, `numpy==2.4.6`, `scipy==1.17.1`, `matplotlib==3.10.9`, `pandas>=2.2`).

- Simulation core needs: `qiskit`, `qiskit-aer`, `qiskit-ibm-runtime`, `numpy`.
- `scipy` is needed by `ci_reruns.py` and `finite_key_skr.py` for exact t-distribution CIs and the Welch test (a fallback t-table is used if absent).
- `matplotlib` + `pandas` are needed **only** by the figure scripts.

### IBM Quantum setup (only for `IBM_Marrakesh` device-noise runs)

The synthetic-noise results run entirely on the local Aer simulator and need **no** IBM account. Only the `ibm_marrakesh` device profile requires one.

```python
from qiskit_ibm_runtime import QiskitRuntimeService
# Run ONCE locally, then delete the file. Never commit your token.
QiskitRuntimeService.save_account(
    channel="ibm_quantum_platform",
    token="PASTE_YOUR_API_KEY_HERE",
    overwrite=True,
)
```

Verify the connection:

```bash
python src/ibm_noise_fetch.py
```

---

## 🚀 Running the code

Run every command **from the project root** (scripts assume the root is the working directory).

### 0. Configuration / reproducibility report (seconds, no simulation)

```bash
python src/report_config.py
```

Prints library versions and all static configuration facts (shots, transpiler settings, seed policy, reconciliation block size, how leakage enters the SKR). Start here for a reproducibility snapshot.

### 1. Core experiments

```bash
python src/detection_aware_qkd_varying_eve.py  # Experiment 1: sweep f  -> data/qkd_varying_eve.csv
python Old/detection_aware_qkd_sample_size.py  # Experiment 2: sweep K  -> data/qkd_resource_cost.csv  (archived script)
```

Experiment 1 requires an IBM account (it includes the `IBM_Marrakesh` profile). Both stream progress to the console and write their CSV to `data/`.

### 2. E91 calibrated-threshold (S*) pipeline

```bash
# a) Calibrate S* per noise profile and rerun FNR-vs-f under S*
python src/e91_adaptive_threshold.py           # -> data/qkd_e91_calibrated.csv, data/qkd_e91_miscalibration.csv

# b) E91 resource cost (FPR/FNR vs K) and SKR under S*   [Task 1]
python src/e91_resource_cost_sstar.py          # -> results/qkd_e91_resource_cost_sstar.csv,
                                               #    results/qkd_e91_skr_operating_points.csv
#    Flags:  --no-fixed (S* only)  |  --fixed-only (old 2.0 only)  |  --skip-skr

# c) Print the 3 E91 summary-table numbers under S*
python src/e91_summary_table_calibrated.py
```

`e91_resource_cost_sstar.py` runs **both** the calibrated `S*` and the old fixed `S = 2.0` rule by default and prints, for each channel, the smallest `K` at which FPR first drops ≤ 5% — so you can read the new value next to the old (~700).

### 3. Confidence-interval reruns (manuscript revision) — Task 2

```bash
python src/ci_reruns.py --workers 6            # see the memory note below before raising this
```

200-trial reruns of the f-sweep (ideal channel) and the honest-channel FPR-vs-noise sweep for all three protocols. Writes per-trial raw values, convergence checkpoints (at 10/25/50/100/200 trials), 95% CIs, and one Welch's t-test (six-state vs BB84 FNR at `f = 0.5`) to `results/ci_*.csv`, plus the `## Task 2` section of `results/results.md`. Serial fallback: drop `--workers`. Single-sweep: `--sweep a` or `--sweep b`.

> **⚠️ Choosing `--workers` (memory, not cores, is the limit).** Each worker runs a full E91 8192-pair Aer trial and holds its own simulator, so RAM — not CPU — caps the useful worker count. On a 16 GB machine, **6 workers** is a safe choice with headroom; pushing to the full logical-core count can exhaust memory and hang the whole OS. Results are **identical regardless of worker count** — each trial is seeded independently (`base_seed + trial_index`), so fewer workers costs only wall-clock time, never accuracy.
>
> **⚠️ `ci_reruns.py` is not resumable.** It truncates its output CSVs at the start of every run, so an interrupted run loses all progress — re-run the whole command from scratch (a completed run is the only usable one).

Each per-trial row also logs the finite-key fields `N, n_sift, m, n_key, Q, leak_EC` (transmitted qubits, sifted length, parameter-estimation sample, raw-key length, observed error rate, and the **actual** disclosed parity bits from the simulated reconciliation). **These columns feed Task 4**, so `ci_reruns.py` must be run before `finite_key_skr.py`. `m = round(0.5 · n_sift)` by default (the `PE_FRACTION` constant at the top of `ci_reruns.py`).

### 4. Finite-key secure key rate — Task 4 (seconds, no simulation)

```bash
python src/finite_key_skr.py                   # -> results/finite_key_summary.csv,
                                               #    results/finite_key_zero_crossing.csv
```

Reads the per-trial CSVs from `results/` and computes, per trial and per configuration, the Hoeffding-corrected finite-key SKR next to the asymptotic value. Also finds, per protocol, the block size `N` at which the finite-key SKR first becomes positive (analytic scaling over `N ∈ [10², 10⁶]`), and writes the `## Task 4` section of `results/results.md`. Security parameters `eps_PE = eps_sec = eps_cor = 1e-10` are configurable at the top of the script. No Qiskit/Aer import — pure post-processing.

### 5. Figures

```bash
python figures/results_fig.py                  # 5 result figures from the data/ CSVs
python figures/fig_e91_calibrated_threshold.py # E91 fixed-vs-calibrated threshold comparison
python figures/fig.py                          # 7 conceptual / circuit figures
python figures/fig_pipe.py                     # methodology pipeline figure
```

`figures/results_fig.py` reads `qkd_varying_eve.csv`, `qkd_resource_cost.csv`, `qkd_e91_calibrated.csv`, and `qkd_e91_resource_cost_calibrated.csv` from `data/` and writes `fig_metric_vs_f`, `fig_tradeoff`, `fig_fpr_vs_noise`, `fig_device`, and `fig_resource_cost` (each as PDF, SVG, PNG) into `figures/`. BB84/six-state curves come from the fixed-threshold CSVs; only the E91 **detection** curves are re-read from the calibrated-`S*` CSVs.

### 6. Rebuild `results/results.md` (seconds, no simulation)

```bash
python src/build_results_md.py                 # reassemble all four Task sections from the CSVs
```

Regenerates the whole of `results/results.md` in one pass by re-reading the CSVs already written by Tasks 1–4 — no simulation is run. Use it after the task scripts finish (or after re-running any single task) to get a clean, complete `results.md`. It prints `sections written : [1, 2, 3, 4]` when every input CSV is present; any task whose CSVs are missing is listed as skipped. Pass `--keep` to preserve existing sections instead of a fresh rebuild.

---

## 🔧 Experiment configuration

**Detection thresholds**

| Protocol | Indicator | Alarm condition |
| --- | --- | --- |
| BB84 | QBER | `QBER ≥ 0.135` |
| Six-State | QBER | `QBER ≥ 0.167` |
| E91 (old) | CHSH `S` | `S < 2.0` (fixed classical bound; kept behind a flag) |
| E91 (new) | CHSH `S` | `S < S*` (per-profile calibrated, below) |

**E91 calibrated threshold `S*`** — `S* = (S_H + S_f)/2`, the midpoint of the honest and full-attack mean CHSH per noise profile (journal Table III):

| Profile | `S*` |
| --- | --- |
| Ideal 0% | 2.124 |
| Noise 2% | 1.945 |
| Noise 5% | 1.722 |
| Noise 8% | 1.499 |
| Threshold 11% | 1.293 |
| IBM Marrakesh | 2.048 |

**Synthetic noise profiles** (depolarizing strength `p`; honest QBER ≈ `p/2`)

| Profile | `p` | Approx. honest QBER |
| --- | --- | --- |
| `Ideal_0%` | 0.00 | 0% |
| `Noise_2%` | 0.04 | ~1.84% |
| `Noise_5%` | 0.10 | ~5.29% |
| `Noise_8%` | 0.16 | ~8% |
| `Threshold_11%` | 0.22 | ~10.92% |
| `IBM_Marrakesh` | device model | hardware-defined |

**Trial counts / scale**

- `detection_aware_qkd_varying_eve.py`: 200 trials per synthetic point, 30 per device point; 1000 qubits/trial (BB84, six-state), 8192 pairs/trial (E91); `f = 0.0…1.0` step 0.1 (synthetic), `{0, .25, .5, .75, 1}` (device).
- `detection_aware_qkd_sample_size.py` and the E91 K-sweeps: 200 trials per point; `K ∈ {100, 200, 300, 500, 1000, 2000, 3000}`.
- `ci_reruns.py`: 200 trials per configuration, convergence checkpoints at `{10, 25, 50, 100, 200}`.

Prepare-and-measure runners batch independent qubits in groups of 10 to bound memory. A full sweep across all three protocols can take several hours single-core — use `ci_reruns.py --workers N` to parallelize.

---

## 🗃️ Output data schema

| CSV | Columns |
| --- | --- |
| `data/qkd_varying_eve.csv` | `Protocol, Noise_Profile, F_Eve, QBER_Threshold, CHSH_Threshold, Mean_Metric, Std_Metric, Mean_SKR, Std_SKR, FPR, FNR` |
| `data/qkd_resource_cost.csv` | `Protocol, K, Trials, FPR, FNR` |
| `data/qkd_e91_calibrated.csv` | `Noise_Profile, S_star, S_H_hat, S_H_std, S_f1_hat, S_f1_std, F_Eve, Mean_S, Std_S, Mean_SKR, Std_SKR, FPR, FNR` |
| `data/qkd_e91_resource_cost_calibrated.csv` | `Protocol, K, Trials, FPR, FNR` |
| `results/qkd_e91_resource_cost_sstar.csv` | `Threshold_Mode, Curve, Channel, P_Noise, F_Eve, Threshold_Value, K, Trials, Rate` |
| `results/qkd_e91_skr_operating_points.csv` | `Noise_Profile, P_Noise, F_Eve, Pairs, Trials, Mean_SKR, Std_SKR, Mean_S, Std_S` |
| `results/ci_pertrial_fsweep_ideal.csv` | `Protocol, Channel, P_Noise, F_Eve, Trial, Metric_Name, Metric, SKR, Alarm, Detection_Outcome, N, n_sift, m, n_key, Q, leak_EC` |
| `results/ci_pertrial_fpr_noise.csv` | `Protocol, Noise_Profile, P_Noise, F_Eve, Trial, Metric_Name, Metric, SKR, Alarm_FP, N, n_sift, m, n_key, Q, leak_EC` |
| `results/ci_convergence.csv` | `Protocol, Sweep, Config_Profile, Config_Point, Metric_Name, N_Trials, Running_Mean, Running_SE` |
| `results/ci_summary_with_ci.csv` | `Protocol, Sweep, Config_Profile, Config_Point, Metric_Name, N, Mean, SE, CI95_Low, CI95_High` |
| `results/ci_welch_sixstate_vs_bb84_fnr_f050.csv` | `Comparison, F_Eve, Channel, N_per_group, Mean_FNR_SixState, Mean_FNR_BB84, Welch_t, dof, p_value` |
| `results/finite_key_summary.csv` | `Protocol, Config, P_Noise, F_Eve, Source, N_trials, Mean_N, Mean_n_sift, Mean_m, Mean_Q, Mean_leak_EC, Mean_SKR_finite, CI95_Low_finite, CI95_High_finite, Mean_SKR_asymptotic` |
| `results/finite_key_zero_crossing.csv` | `Protocol, Channel, F_Eve, Observed_Q, Sifting_ratio, PE_fraction, Leak_per_keybit, N_finite_key_SKR_first_positive` |
| `results/results.md` | Consolidated markdown tables, sections `## Task 1` … `## Task 4` (written by the four experiment scripts) |

The finite-key fields in the per-trial CSVs (`N, n_sift, m, n_key, Q, leak_EC`) are logged so `finite_key_skr.py` can compute the finite-key length `ℓ = n_key·(1 − 2 H₂(min(Q+μ, ½))) − leak_EC − log₂(2/ε_sec) − log₂(1/ε_cor)`, with `μ = √(ln(1/ε_PE)/2m)` and `n_key = n_sift − m`.

In `data/qkd_varying_eve.csv`, `Mean_Metric` is the mean QBER for BB84/six-state and the mean CHSH `S` for E91; `FPR` is populated only on honest rows (`F_Eve = 0`) and `FNR` only on attacked rows (`F_Eve > 0`).

> **Why `results/` is committed (not gitignored).** The CSVs are small (kilobytes), the paper links this repo and cites exact numbers, and `results.md` is meant to be readable on GitHub without cloning and running. So `results/` and its outputs are tracked. Only `__pycache__/` and editor cruft are gitignored.

---

## ▶️ RUN INSTRUCTIONS (Tasks 1–4, in order)

Run everything **from the project root** (`python src/<script>.py`). The commands below produce every number for the manuscript revision. Runtimes are for a modern multi-core laptop; the two simulation-heavy steps dominate. Steps 1, 4 and 5 do **no** simulation and finish in seconds.

| # | Command | ~Runtime | Produces |
| --- | --- | --- | --- |
| 1 | `python src/report_config.py` | seconds (no sim) | stdout version/config report; `results/results.md` → `## Task 3` |
| 2 | `python src/e91_resource_cost_sstar.py` | ~1–2 h | `results/qkd_e91_resource_cost_sstar.csv`, `results/qkd_e91_skr_operating_points.csv`; `results/results.md` → `## Task 1` |
| 3 | `python src/ci_reruns.py --workers 6` | ~30–60 min (6 workers); ~2–4 h serial | `results/ci_pertrial_fsweep_ideal.csv`, `results/ci_pertrial_fpr_noise.csv`, `results/ci_convergence.csv`, `results/ci_summary_with_ci.csv`, `results/ci_welch_sixstate_vs_bb84_fnr_f050.csv`; `results/results.md` → `## Task 2` |
| 4 | `python src/finite_key_skr.py` | seconds (no sim) | `results/finite_key_summary.csv`, `results/finite_key_zero_crossing.csv`; `results/results.md` → `## Task 4` |
| 5 | `python src/build_results_md.py` | seconds (no sim) | reassembles the complete `results/results.md` from all Task CSVs |

**Ordering constraint:** step 4 reads the per-trial CSVs from step 3, so **run step 3 before step 4**; run step 5 last. Steps 1–3 are otherwise independent. For `--workers`, **memory is the limit, not cores** — 6 is safe on 16 GB; see the memory note under section 3. `ci_reruns.py` is **not** resumable (it truncates its CSVs on each run), so if it is interrupted, re-run the whole command from scratch.

> **If you previously ran an older `ci_reruns.py`:** the per-trial CSVs must be regenerated, because the finite-key columns (`N, n_sift, m, n_key, Q, leak_EC`) were added for Task 4. Delete `results/ci_pertrial_*.csv` and re-run step 3 before step 4. `finite_key_skr.py` aborts with a clear message if it sees the old schema.

Optional (not needed for Tasks 1–4): the published core sweep `python src/detection_aware_qkd_varying_eve.py` (needs an IBM account) and the S* calibration `python src/e91_adaptive_threshold.py`; figures are section 5 above.

---

## 📤 WHAT TO RETURN (collect after running)

Paste these back so the numbers can go into the manuscript:

**1. The consolidated results file (most important):**
- `results/results.md` — the whole file (sections `## Task 1` – `## Task 4`).

**2. All CSVs in `results/`:**
- `qkd_e91_resource_cost_sstar.csv`, `qkd_e91_skr_operating_points.csv` (Task 1)
- `ci_pertrial_fsweep_ideal.csv`, `ci_pertrial_fpr_noise.csv`, `ci_convergence.csv`, `ci_summary_with_ci.csv`, `ci_welch_sixstate_vs_bb84_fnr_f050.csv` (Task 2)
- `finite_key_summary.csv`, `finite_key_zero_crossing.csv` (Task 4)

**3. These printed values from the console:**
- **Task 3** (`report_config.py`): the entire `SOFTWARE VERSIONS` block and the disclosed-parity-bits example.
- **Task 1** (`e91_resource_cost_sstar.py`): the `K AT WHICH E91 FPR FIRST FALLS ≤ 5%` block — the S* value next to the old fixed-2.0 value (~700) for both the 5% and 11% channels.
- **Task 2** (`ci_reruns.py`): the `WELCH'S T-TEST` block — the p-value for six-state vs BB84 FNR at `f = 0.5`.
- **Task 4** (`finite_key_skr.py`): the per-protocol block size `N` at which the finite-key SKR first becomes positive (also in `finite_key_zero_crossing.csv`).
