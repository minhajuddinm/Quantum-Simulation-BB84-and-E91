# Priority 1 — Optimized CHSH Detection Threshold for E91 (first-pass derivation)

Grounded directly in `run_e91_trial` / `monte_carlo_e91` in `detection_aware_qkd_varying_eve.py`, and in the existing `qkd_varying_eve.csv` data — not a generic textbook E91 description.

## 1. The estimator, as actually implemented

Alice uses 3 angles `{0, π/4, π/2}` (indices 0,1,2), Bob uses 3 angles `{π/4, π/2, 3π/4}` (indices 0,1,2). Key bits come from the matched pairs (Alice=1,Bob=0) and (Alice=2,Bob=1). The CHSH statistic uses the other four basis combinations:

`S = E(0,0) − E(0,2) + E(2,0) + E(2,2)`, where each `E(a,b) = (matches − mismatches)/(matches + mismatches)` over the pairs that landed in that basis combination.

Two facts make this tractable for a Hoeffding-style bound:
- Each pair's contribution to `E(a,b)` is exactly `+1` or `−1` (match/mismatch), not just bounded — same structure as the QBER estimator, just sign-valued instead of 0/1-valued.
- Alice and Bob each pick uniformly among 3 bases, so each of the 4 relevant `(a,b)` combinations gets on average `n ≈ N/9` of the `N` total pairs (here `N=8192` in the synthetic sweep ⇒ `n≈910`). This is the effective sample size for detection — not `N`, and not the sifted-key length. That's roughly **9x fewer effective samples than total pairs transmitted**, vs. BB84's sifted key getting roughly `N/2`.

## 2. Concentration bound

Writing `Ŝ − S` as a normalized sum of `4n` independent ±1-bounded terms (the four correlators pooled, accounting for sign), Hoeffding's inequality gives:

`P(|Ŝ − S| ≥ δ) ≤ 2 exp(−n δ² / 8)`

This is the CHSH analogue of the bound Lee et al. use for QBER — same tool, applied to a statistic that pools 4 correlators instead of 1 error rate, with `n = N/9` in place of the sifted length.

## 3. Balanced threshold

Let `S_H` = true CHSH under the honest channel, `S_f` = true CHSH under the channel attacked at interception fraction `f`. For a threshold `S*` between them:

- FPR bound: `P(Ŝ < S* | S_H) ≤ exp(−n(S_H−S*)²/8)`
- FNR bound: `P(Ŝ ≥ S* | S_f) ≤ exp(−n(S*−S_f)²/8)`

Equalizing the two exponents (same move as the QBER midpoint rule) gives:

**`S* = (S_H + S_f) / 2`**

Structurally identical to the QBER case — the four-correlator structure changes the achievable confidence (via `n=N/9`), not the form of the rule.

## 4. Why this matters — it's not just "more optimal," the current threshold is measurably broken

Using the honest-channel (`F_Eve=0`) rows already in `qkd_varying_eve.csv`:

| Noise profile | Honest S̄ | Full-attack S̄ (f=1) | Derived S* | **Current FPR at fixed S=2.0** | FPR bound at S* |
|---|---|---|---|---|---|
| Ideal_0% | 2.823 | 1.415 | 2.119 | 0.00 | ~3e-25 |
| Noise_2% | 2.611 | 1.316 | 1.964 | 0.00 | ~2e-21 |
| Noise_5% | 2.291 | 1.162 | 1.726 | 0.00 | ~2e-16 |
| Noise_8% | 1.989 | 0.994 | 1.491 | **0.60** | ~6e-13 |
| Threshold_11% | 1.726 | 0.858 | 1.292 | **1.00** | ~5e-10 |

At 8% honest noise, the fixed `S=2.0` rule false-alarms 60% of honest sessions, because the honest channel's own CHSH value has dropped to 1.989 — below the "threshold." At 11% noise (the exact operating point the paper already uses to stress-test BB84 and six-state's robustness), the fixed threshold false-alarms on **every single honest session**. This isn't a marginal improvement opportunity — the current E91 detector is non-functional at the noise level the rest of the paper treats as the robustness boundary.

**Why BB84/six-state's fixed thresholds don't have this problem:** their thresholds (0.135, 0.167) were calibrated against the honest QBER at that same 11% regime with margin built in. `S=2` was never calibrated against anything — it's the classical/security bound from Bell's theorem, not a statistically derived detection threshold. That mismatch in role (security bound vs. detection threshold) is the real gap, and it's a stronger, more concrete framing for the paper than "nobody has derived this yet."

## 5. Recommended approach (needs your confirmation)

- Calibrate `S*` **per noise profile** using a known honest-channel baseline (consistent with how the existing framework already characterizes noise profiles), rather than searching for one universal number — a single fixed `S*` would just relocate the same failure mode to a different noise level.
- Calibrate against the full-attack case (`f=1`) as the worst-case `S_f`, matching the Lee/Fiorini convention used for BB84/six-state. This keeps cross-protocol comparison apples-to-apples.
- This deliberately leaves low-`f` stealthy attacks (0.1–0.3) hard to catch per-session even with the optimized threshold — that's expected and fine, because that's exactly what Priority 2's sequential detector is for. Priority 1 fixes the per-session rule's correctness; Priority 2 handles the stealth window. They're not redundant.

## 6. Confirmed by simulation — full sweep complete

Ran `e91_adaptive_threshold.py` (new script, reuses `run_e91_trial`/`monte_carlo_e91` from the existing codebase): per-profile calibration (30 independent calibration trials for `S_H` and `S_f1` each, not reused for evaluation) followed by the full official-scale FPR/FNR sweep (50 trials, 8192 pairs, `f`=0.0–1.0 step 0.1) — same scale as `qkd_varying_eve.csv`, so directly comparable.

**Honest-channel FPR, fixed `S=2.0` vs. calibrated `S*`:**

| Noise profile | Calibrated S* | FPR with fixed S=2.0 (existing data) | FPR with calibrated S* (new) |
|---|---|---|---|
| Ideal_0% | 2.124 | 0.00 | 0.00 |
| Noise_2% | 1.945 | 0.00 | 0.00 |
| Noise_5% | 1.722 | 0.00 | 0.00 |
| Noise_8% | 1.499 | **0.60** | **0.00** |
| Threshold_11% | 1.293 | **1.00** | **0.00** |

The fix works exactly as derived — both noise levels where the fixed threshold was broken (8% and 11%) are back to FPR=0.00 under the calibrated threshold, with no cost at the low-noise profiles (already fine, stay fine).

**Mis-calibration robustness check** (S* calibrated at profile X, evaluated live at the neighboring noise profile — channel drifted one step since the last calibration cycle): FPR and FNR are both 0.00 across all 8 one-step-drift combinations tested. The calibrated threshold tolerates at least one synthetic noise step of staleness with no measurable detection degradation. This directly answers the "we wouldn't know the noise in advance" objection from the design discussion — a calibration that's one maintenance cycle out of date still works fine.

Output files: `qkd_e91_calibrated.csv` (full sweep), `qkd_e91_miscalibration.csv` (robustness check). Script: `e91_adaptive_threshold.py`, resumable at the (profile, f-value) row level.

## 7. IBM_Marrakesh (real device noise model)

Run by the user locally (where the IBM Quantum credentials are saved), same script, extended to fetch and calibrate on the real `ibm_marrakesh` noise model — 30 trials, 1024 pairs, calibrated on 15 independent honest/full-attack trials each: `S_H_hat = 2.742`, `S_f1_hat = 1.354` → `S* = 2.048`.

| f | Old fixed S=2.0 FPR/FNR | New calibrated S* FPR/FNR |
|---|---|---|
| 0.00 (honest) | FPR 0.000 | FPR 0.000 |
| 0.25 | FNR 1.000 | FNR 1.000 |
| 0.50 | FNR 0.533 | FNR 0.567 |
| 0.75 | FNR 0.067 | FNR 0.000 |
| 1.00 | FNR 0.000 | FNR 0.000 |

Unlike the 8%/11% synthetic profiles, IBM_Marrakesh's honest channel was never broken under the old fixed threshold (honest S̄≈2.7, comfortably clear of 2.0) — so this isn't a "fix," it's a consistency check, and it holds up: FPR stays at 0.000 under the new threshold too, with a small, likely-within-noise improvement at f=0.75 (0.067→0.000) and no meaningful change elsewhere (the f=0.5 FNR difference, 0.533 vs 0.567, is within the trial-to-trial noise at only 30 trials).

One extra, unplanned finding worth keeping for the paper: the real device's CHSH estimator is noticeably noisier than the synthetic model at a comparable honest-channel operating point — `Std_S ≈ 0.158` on IBM_Marrakesh vs. `Std_S ≈ 0.063` on the synthetic Noise_8% profile (roughly 2.5x). The synthetic depolarizing model likely *understates* real-world estimator variance, which is itself a reason Priority 4's hardware validation matters beyond "running it on a real device is good practice."

## 8. Figure regenerated

`figures/fig_e91_calibrated_threshold.py` — new script (matches the existing `results_fig.py` style/conventions), produces `fig_e91_calibrated_threshold.{pdf,svg,png}`: fixed-S=2.0 vs calibrated-S* FPR side by side across all 6 profiles (5 synthetic + IBM_Marrakesh), with each profile's calibrated `S*` value annotated on the bar.

## 9. What's still needed before this goes into the paper draft

- Write this up formally as a methods subsection (the derivation in §1–3) and a results subsection (the tables in §6–7 plus the mis-calibration result), in the actual LaTeX manuscript. Not done yet — this file is the working derivation only. User is doing this via a live Overleaf session (Claude in Chrome) rather than having it drafted standalone first.
- The mis-calibration check currently only tests drift to the adjacent profile on the 5-point synthetic noise grid, not a continuous drift amount, and doesn't cover IBM_Marrakesh at all (excluded by design, see §3 docstring) — worth a finer-grained follow-up if reviewers want the tolerance quantified more precisely.
