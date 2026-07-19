# Task Spec: Re-run E91 detection under the noise-calibrated threshold S*

## PROJECT OVERVIEW
This repo is the Qiskit simulation behind the paper "Noise-Aware Simulation and Statistical Eavesdropping Detection in BB84, Six-State, and E91 QKD Protocols" (journal upgrade of an accepted conference paper). It simulates BB84, six-state, and E91 under a partial intercept-and-resend attacker and reports QBER/CHSH, secure key rate, and FPR/FNR detection statistics across ideal, synthetic-depolarizing, and ibm_marrakesh device-noise regimes.

## CURRENT STATE
- E91 eavesdropper detection currently fires an alarm when the measured CHSH value `S < 2.0` (the fixed classical Bell bound).
- The journal upgrade (Priority 1) added a noise-calibrated threshold `S* = (S_H + S_f)/2`, where `S_H` is the honest-channel mean CHSH and `S_f` is the full-attack (f=1) mean CHSH at a given noise profile.
- Problem: `S*` was only applied to the honest-channel FPR result (Table III / `fig_e91_calibrated_threshold.pdf`). The threshold-dependent E91 outputs used elsewhere (FNR sweeps, resource-cost K, and the summary-table rows derived from them) are still computed under the old `S = 2.0` rule. The summary table therefore mixes two thresholds in one E91 row.

## GOAL OF THIS TASK
Rerun ONLY the E91, threshold-dependent outputs using a per-noise-profile `S*` instead of the fixed `S = 2.0`, then report the new numbers. Specifically:

1. Change the E91 alarm rule from `S < 2.0` to `S < S*_profile`, where `S*_profile` is computed per noise profile from held-out calibration trials (separate from evaluation trials to avoid circularity): run honest trials to get `S_H`, run full-attack `f=1` trials to get `S_f`, set `S* = (S_H + S_f)/2`, hold it fixed for evaluation.
2. Sanity-check the computed `S*` against these already-reported values (should match within Monte Carlo error): Ideal 0% = 2.124, Noise 2% = 1.945, Noise 5% = 1.722, Noise 8% = 1.499, Threshold 11% = 1.293, IBM Marrakesh = 2.048.
3. Regenerate ONLY these figures/curves for E91 (leave BB84 and six-state curves in them untouched):
   - `Figures/fig_tradeoff.pdf` — E91 FNR-vs-f, ideal channel, threshold `S*_ideal = 2.124`.
   - `Figures/fig_device.pdf` — E91 FNR-vs-f, ibm_marrakesh, threshold `S*_marrakesh = 2.048`.
   - `Figures/fig_resource_cost.pdf` panel (a) — E91 FPR-vs-K on the 5% honest channel, threshold `S*_5% = 1.722`.
   - `Figures/fig_resource_cost.pdf` panel (b) — E91 FNR-vs-K on the clean channel under full attack, threshold `S*_ideal = 2.124`.
4. Recompute the E91 row of the summary table (`tab:summary`): stealth-window edge (largest f where FNR is still ~1), detection onset (smallest f where FNR <= 0.5), and K for FPR <= 5%. Report the three new numbers.

## EXPECTED DIRECTION (use as a bug check)
- On the ideal channel `S*_ideal = 2.124 > 2.0`, so the detector is more aggressive than before. E91 detection onset should move EARLIER (down from f = 0.7, expected near f ~ 0.5), and stealth-window edge should shrink (down from 0.5). If the onset does not move earlier, something is wrong, stop and report.
- On the 5% honest channel the margin from honest baseline (`S_H ~ 2.291`) to `S*_5% = 1.722` is much wider than to 2.0, so E91 FPR should fall below 5% at a SMALLER K than the current ~700. Report the new K.

## CONSTRAINTS
- Do NOT touch BB84 or six-state code, thresholds, curves, or numbers. This is E91-only.
- Do NOT change secure key rate (SKR) values, raw QBER/CHSH signal curves (`fig_metric_vs_f.pdf`), the honest-noise FPR figure (`fig_fpr_vs_noise.pdf`), or the already-calibrated `fig_e91_calibrated_threshold.pdf`. SKR and the raw signal are threshold-independent, so they stay as published.
- Keep the existing simulation methodology unchanged: same trial counts (50 trials with 8192 pairs per trial for ideal E91; 30 trials with 1024 pairs for device), same interception-fraction sweep steps, same RNG seeding convention.
- Compute `S*` from calibration trials in code; do not hardcode the six values above except as an assertion/sanity check.
- Keep changes minimal and localized to the E91 detection-threshold logic and the four listed regenerations.

## REPORT BACK
- The computed `S*` per profile vs the expected values above.
- New E91 numbers: stealth-window edge (f), detection onset (f, FNR <= 0.5), and K for FPR <= 5%.
- Confirmation that BB84/six-state outputs and all SKR values are unchanged.
- The four regenerated figure files, and a one-line note flagging anything that moved in an unexpected direction.

## ATTACHMENTS AND REFERENCES
1. This repo (you already have access) — the Qiskit QKD simulation code and the `Figures/` output directory.
2. `Journal_Quantum.pdf` — current journal draft, for context on which figure/table each output maps to.
3. `Conf_Quantum.pdf` — accepted conference version, for the original fixed `S = 2.0` behavior.
4. S* derivation: FPR <= exp(-n(S_H - S*)^2 / 8), FNR <= exp(-n(S* - S_f)^2 / 8), balanced at S* = (S_H + S_f)/2, computed per noise profile.

## STATUS (implemented — awaiting simulation run)
See `updates/Priority1_E91_Sstar_Rerun.md` for the full write-up. Summary:
- The FNR-vs-f data under S* for `fig_tradeoff` (ideal) and `fig_device` (marrakesh)
  already exists in `qkd_e91_calibrated.csv`; all six S* match expected within MC error.
- New `e91_resource_cost_calibrated.py` re-runs ONLY the E91 K-sweep under S*_5% (FPR) and
  S*_ideal (FNR) -> `qkd_e91_resource_cost_calibrated.csv`. This is the one sim to run.
- `figures/results_fig.py` edited so E91 detection curves read the calibrated CSVs; BB84,
  six-state, and all SKR untouched.
- `e91_summary_table_calibrated.py` prints the 3 summary numbers.
- New numbers so far: stealth edge f=0.5 -> 0.4; onset f=0.7 -> 0.5 (both as predicted);
  K for FPR<=5% pending the K-sweep run.
