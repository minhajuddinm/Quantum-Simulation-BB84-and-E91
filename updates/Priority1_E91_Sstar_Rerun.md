# Priority 1 — E91 threshold-dependent outputs re-run under S* (what I changed, and what you need to run)

This closes the gap flagged in `e91_sstar_rerun_spec.md`: the calibrated threshold
`S* = (S_H + S_f)/2` was only ever applied to the honest-channel FPR result
(Table III / `fig_e91_calibrated_threshold.pdf`). Every *other* threshold-dependent
E91 output — the FNR-vs-f curves, the resource-cost K-sweep, and the summary-table
row derived from them — was still computed under the old `S < 2.0` rule, so the E91
summary row mixed two thresholds. This change moves all of those onto per-noise-profile
`S*`. BB84, six-state, all SKR values, and the raw QBER/CHSH signal are untouched.

---

## What was already in place (no re-run needed)

`qkd_e91_calibrated.csv` (produced earlier by `e91_adaptive_threshold.py`) already
contains the full FNR-vs-f sweep under `S*` for **every** profile, including the two
the figures need. Its calibrated `S*` values match the reported targets within Monte
Carlo error:

| Profile | S* in CSV | Expected | ok |
|---|---|---|---|
| Ideal 0% | 2.1245 | 2.124 | ✓ |
| Noise 2% | 1.9447 | 1.945 | ✓ |
| Noise 5% | 1.7218 | 1.722 | ✓ |
| Noise 8% | 1.4993 | 1.499 | ✓ |
| Threshold 11% | 1.2934 | 1.293 | ✓ |
| IBM Marrakesh | 2.0479 | 2.048 | ✓ |

So `fig_tradeoff` (E91 FNR, ideal) and `fig_device` (E91 FNR, marrakesh) can be
regenerated from data that already exists — **the only new simulation you need to run
is the E91 resource-cost K-sweep**, which never existed under `S*`.

---

## Files I added / changed

### 1. `e91_resource_cost_calibrated.py` (new) — the one simulation to run
E91-only re-run of the sample-size (K) sweep that feeds `fig_resource_cost.pdf`,
with the E91 alarm rule changed from `S < 2.0` to `S < S*`:

- **panel (a)** FPR vs K on the honest 5% channel (`p_noise = 0.10`, `f = 0`) →
  threshold `S*_5% ≈ 1.722`
- **panel (b)** FNR vs K on the clean channel under full attack (`p_noise = 0`, `f = 1`) →
  threshold `S*_ideal ≈ 2.124`

`S*` is **calibrated in code** from 30 held-out trials at 8192 pairs (separate seeds from
the K-sweep evaluation, so no circularity), then **asserted** against 2.124 / 1.722 as a
sanity check — never hardcoded into the alarm rule. `S*` is calibrated once per profile
and held fixed across all K (it depends on the *mean* CHSH, which is K-independent; only
the variance shrinks with K — which is exactly what this figure measures). Same K grid
`[100,200,300,500,1000,2000,3000]`, same 200 trials, same operating points as the original
`detection_aware_qkd_sample_size.py`. Row-level resumable. Writes
`qkd_e91_resource_cost_calibrated.csv`. Pure synthetic noise — **no IBM access needed.**

### 2. `figures/results_fig.py` (edited, E91-only branches)
- `tradeoff()` — E91 FNR curve now read from `qkd_e91_calibrated.csv` (Ideal_0%). E91 SKR
  and both BB84/six-state curves unchanged.
- `device_noise()` — E91 FNR curve now read from `qkd_e91_calibrated.csv` (IBM_Marrakesh).
  SKR bars and BB84/six-state unchanged.
- `resource_cost()` — E91 FPR/FNR now read from `qkd_e91_resource_cost_calibrated.csv`.
  BB84/six-state still read from the published `qkd_resource_cost.csv`.

  BB84 and six-state are pulled from the original, untouched CSVs in every case, so their
  numbers are byte-for-byte identical. `fig_metric_vs_f` and `fig_fpr_vs_noise` read only
  unchanged data/code, so they re-render identically (no numeric change).

### 3. `e91_summary_table_calibrated.py` (new) — recomputes the E91 summary row
Reads the two calibrated CSVs and prints the three `tab:summary` numbers (stealth-window
edge, detection onset, K for FPR ≤ 5%). Pure stdlib + numpy (no pandas), runs in the same
env as the simulation.

---

## New E91 numbers (2 of 3 already computable, 3rd pending your run)

From `qkd_e91_calibrated.csv`, ideal channel, `S*_ideal = 2.124`:

| Quantity | Old (S = 2.0) | New (S*) | Direction |
|---|---|---|---|
| stealth-window edge (largest f with FNR ≈ 1) | f = 0.5 | **f = 0.4** | shrinks ✓ |
| detection onset (smallest f, FNR ≤ 0.5) | f = 0.7 | **f = 0.5** (FNR 0.42) | earlier ✓ |
| K for FPR ≤ 5% (5% honest, S*_5%) | ~700 | **pending K-sweep run** | expected smaller |

Both computable numbers moved in the direction the spec predicted (onset earlier, stealth
window narrower), which is the built-in bug check — the more-aggressive `S*_ideal > 2.0`
detector catches the attacker at a lower interception fraction. The old vs new FNR-vs-f are
directly comparable: old `qkd_varying_eve.csv` E91/Ideal had FNR=1.0 up to f=0.5 then 0.54
at f=0.6, 0.0 at f=0.7; new has FNR=1.0 up to f=0.4 then 0.42 at f=0.5, 0.0 at f=0.6.

The K-for-FPR≤5% value comes out of the K-sweep you're about to run; `e91_summary_table_calibrated.py`
will print it (with a linear-interpolated crossing) once the CSV exists.

---

## What you need to run (in `D:\MITACS\Scotland\Quantum Simulation BB84 and E91`)

```powershell
# 1. the only new simulation — E91 resource-cost K-sweep under S* (synthetic, no IBM)
D:\Pycharm\python.exe e91_resource_cost_calibrated.py
#    -> writes qkd_e91_resource_cost_calibrated.csv
#    -> prints the calibrated S* and confirms the sanity assertions pass

# 2. print the recomputed E91 summary-table row (incl. the new K for FPR<=5%)
D:\Pycharm\python.exe e91_summary_table_calibrated.py

# 3. regenerate the figures (needs pandas + matplotlib)
cd figures
python results_fig.py          # or your figure env; D:\Pycharm\python.exe lacks pandas
```

Then confirm back to me: the K value printed in step 2, and whether the step-1 sanity
assertions passed. I'll fold the K number into the summary-table row.

**Heads-up on the figure env:** `D:\Pycharm\python.exe` has qiskit/numpy/matplotlib but
**not** pandas, and `results_fig.py` uses pandas. Run the figure step from whatever env you
used to generate the figures originally, or `pip install pandas` into the PyCharm interpreter.
Steps 1 and 2 run fine on `D:\Pycharm\python.exe` as-is.

---

## Sanity boundaries (what did NOT change)
- No BB84 or six-state code, thresholds, curves, or numbers touched.
- No SKR values changed (E91 SKR is threshold-independent, still read from `qkd_varying_eve.csv`).
- `fig_metric_vs_f.pdf`, `fig_fpr_vs_noise.pdf`, and `fig_e91_calibrated_threshold.pdf` unchanged.
- Trial counts, pair counts, f-sweep steps, and seeding convention preserved.
