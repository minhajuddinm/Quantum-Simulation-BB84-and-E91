# Priority 1: Noise-Calibrated CHSH Detection Threshold for E91 — What We Did and How

This document explains, in detail, what Priority 1 of the journal extension involved, why it was necessary, exactly how the new threshold was derived and validated, and what changed in the paper. It consolidates the working derivation (`Priority1_CHSH_Threshold_Derivation.md`), the full verification report (`Priority1_Verification_Report.md`), and the actual Overleaf insertions into one narrative.

---

## 1. The problem we found

The paper compares eavesdropping detection across three QKD protocols: BB84, six-state, and E91.

BB84 and six-state detect eavesdropping through the Quantum Bit Error Rate (QBER), tested against fixed thresholds from prior published work: 0.135 (Lee et al.) and 0.167 (Fiorini et al.). Those thresholds were derived using Hoeffding's inequality to balance false-positive rate (FPR — a false alarm on an honest channel) against false-negative rate (FNR — a missed attacker), and they hold up because the honest-channel QBER barely moves across the noise range tested in this study.

E91 is entanglement-based and uses the CHSH Bell statistic `S` instead of QBER. Before this work, E91's alarm rule was simply `S < 2.0` — the classical Bell bound. That number is a **security bound** (the point below which quantum correlations can no longer be explained without eavesdropping), not a **statistically calibrated detection threshold**. Nobody had derived an actual detection threshold for it, and unlike QBER, the honest-channel `⟨S⟩` is *not* noise-invariant — it slides steadily downward as depolarizing noise increases.

Checking the existing simulation data (`qkd_varying_eve.csv`) against the fixed `S=2.0` rule exposed how bad this was in practice:

| Noise profile | Honest `S̄` | FPR at fixed `S=2.0` |
|---|---|---|
| Ideal (0% noise) | 2.823 | 0.00 |
| 2% noise | 2.611 | 0.00 |
| 5% noise | 2.291 | 0.00 |
| 8% noise | 1.989 | **0.60** |
| 11% noise (paper's stress-test level) | 1.726 | **1.00** |

At 8% noise, the honest channel's own CHSH value has already dropped below 2.0, so the fixed rule false-alarms on 60% of honest sessions. At 11% noise — the exact operating point the rest of the paper uses to stress-test BB84 and six-state's robustness — **the fixed threshold false-alarms on every single honest session**. E91's detector was, in effect, non-functional at the noise level the paper treats as the robustness boundary. This was the real gap: `S=2.0` had never been calibrated against anything, it was just borrowed from Bell's theorem.

## 2. What we set out to do

Derive a proper detection threshold for the CHSH statistic using the same Hoeffding-balancing method Lee et al. and Fiorini et al. used for QBER, adapted to the four-correlator structure of CHSH, then validate it empirically against the existing simulation framework (`detection_aware_qkd_varying_eve.py`) and — separately — against real IBM hardware noise.

## 3. The system as actually implemented

This derivation is grounded directly in the existing code (`run_e91_trial` / `monte_carlo_e91` in `detection_aware_qkd_varying_eve.py`), not a generic textbook description of E91.

Alice measures at 3 angles `{0, π/4, π/2}` (indices 0, 1, 2). Bob measures at 3 angles `{π/4, π/2, 3π/4}` (indices 0, 1, 2), chosen uniformly at random and independently per entangled pair. Key bits come from the two matched-basis combinations (Alice=1, Bob=0) and (Alice=2, Bob=1). The CHSH statistic is built from the other four basis combinations:

```
E(a,b) = (matches − mismatches) / (matches + mismatches)     [over pairs landing in basis combo (a,b)]
S = E(0,0) − E(0,2) + E(2,0) + E(2,2)
```

The code returns `abs(S)`, not signed `S`.

Two structural facts make this tractable for a Hoeffding-style bound:

- Each pair's contribution to `E(a,b)` is exactly `+1` (match) or `−1` (mismatch) — bounded, just like the QBER estimator, but sign-valued instead of 0/1-valued.
- Alice and Bob each pick uniformly among 3 bases independently, so each of the 9 `(a,b)` combinations gets on average `N/9` of the `N` total transmitted pairs. Only 4 of those 9 combinations feed into `S`. With `N=8192` (the paper's standard sweep size), that's a mean of about 910 pairs per relevant combination — the *effective sample size* for CHSH detection, not `N` and not the sifted-key length. That's roughly 9× fewer effective samples than pairs transmitted, versus BB84's sifted key getting roughly `N/2`.

## 4. Derivation of the threshold

**Step 1 — the estimator.** `Ŝ` is built from four sample means, each itself an average of ±1-valued terms over its basis combination's `n` pairs.

**Step 2 — effective sample size.** As above, `n ≈ N/9` per relevant combination, and the four counts are multinomial (not fixed), which is handled rigorously in Step 3.

**Step 3 — Hoeffding concentration bound.** Write `Ŝ − S` as a normalized sum of `4n` independent, ±1-bounded terms (the four correlators, `c = (+1, −1, +1, +1)`; only `|c_j|=1` matters for the bound width, so the specific sign pattern doesn't affect the result). Hoeffding's inequality for independent bounded variables gives:

```
P(T − E[T] ≥ t) ≤ exp(−2t² / Σ(b_j − a_j)²) = exp(−2t² / (4n·4)) = exp(−t² / 8n)
```

Substituting `t = nδ` and taking the two-sided version:

```
P(|Ŝ − S| ≥ δ) ≤ 2 exp(−n δ² / 8)
```

This is the exact CHSH analogue of the bound Lee et al. use for QBER — same tool, applied to a statistic that pools four correlators instead of a single error rate, with `n = N/9` in place of the sifted-key length.

**Step 4 — the balanced threshold.** Let `S_H` be the true honest-channel CHSH value and `S_f` the true value under an attacker intercepting a fraction `f` of the channel. For a threshold `S*` sitting between them:

```
FPR bound:  P(Ŝ < S* | S_H) ≤ exp(−n(S_H − S*)² / 8)
FNR bound:  P(Ŝ ≥ S* | S_f) ≤ exp(−n(S* − S_f)² / 8)
```

Equalizing the two exponents — the same move used to derive the QBER midpoint rule — gives:

```
S* = (S_H + S_f) / 2
```

Structurally identical to the QBER threshold rule. The four-correlator structure changes the achievable statistical confidence (through `n = N/9` instead of the sifted-key length) but not the form of the rule itself.

### 4.1 Handling the multinomial sample sizes rigorously

The four basis-combination counts aren't fixed at exactly `N/9` — they're multinomially distributed. Conditioning on the realized counts `n_1, n_2, n_3, n_4`, each one-sided Hoeffding bound holds *exactly* for its own realized `n_i` (Hoeffding doesn't require `n_i` to be non-random once you condition on it). The worst case across the four is governed by `n_min = min(n_1, ..., n_4)`.

For `N=8192`, each `n_i` is approximately Normal with mean 910.2 and standard deviation 28.4 (from the multinomial variance `N·p·(1−p)`, `p=1/9`). This gives `P(n_i < 800) ≈ 5.3×10⁻⁵` per combination, and a union bound over the four relevant combinations gives `P(n_min < 800) ≲ 2.1×10⁻⁴`. So: conditional on the high-probability event `n_min ≥ 800` (probability ≥ ~0.9998 for `N=8192`), the analytic bound can be safely evaluated using `n=800` as a floor — a precise conditional statement, not an approximation based on the mean.

## 5. Calibration methodology

Calibration is treated as an **out-of-band process**, run separately from the live detection test being evaluated — mirroring how real QKD systems characterize channel noise ahead of time rather than adaptively, session by session. This is a deliberate design choice, and it directly parallels how Lee et al. and Fiorini et al.'s own QBER thresholds were characterized once and then held fixed, not recomputed live.

For each noise profile:

1. Estimate `Ŝ_H` (honest-channel CHSH) from 30 independent calibration trials.
2. Estimate `Ŝ_{f=1}` (CHSH under a full, 100%-interception attacker) from 30 independent calibration trials, disjoint from the trials used in step 1 and from the evaluation trials.
3. Fix `S* = (Ŝ_H + Ŝ_{f=1}) / 2`.
4. Evaluate FPR/FNR on a fresh sweep of attack fractions `f = 0.0, 0.1, ..., 1.0`, 50 trials per point (30 for IBM_Marrakesh, matching its existing smaller-scale methodology), at the paper's standard 8192-pair scale (1024 pairs for IBM_Marrakesh).

Calibration targets the **full-attack case (`f=1`)**, matching the BB84/six-state convention — this is deliberately *not* optimized for weak, stealthy attackers (`f = 0.1–0.3`). Catching stealthy attackers is what the separate, planned Priority 2 sequential/multi-session detector is for; Priority 1 only fixes the correctness of the per-session rule.

A single universal `S*` (calibrated once at the worst-case 11%-noise profile) was checked analytically and found to leave a 100%-interception attacker undetected on average at the 0%/2%-noise profiles — because honest `⟨S⟩` moves so much across the noise range (2.835 at 0% noise down to 1.721 at 11% noise, already below the classical bound on a fully honest channel). This is why calibration is done **per noise profile** rather than as one fixed number.

## 6. Results

### 6.1 Honest-channel FPR: fixed `S=2.0` vs. calibrated `S*`

30 calibration trials + 50 evaluation trials per synthetic profile (15 + 30 for IBM_Marrakesh), 8192 pairs (1024 for IBM_Marrakesh):

| Noise profile | `Ŝ_H` (std) | `Ŝ_{f=1}` (std) | `S*` | FPR, fixed `S=2.0` | FPR, calibrated `S*` |
|---|---|---|---|---|---|
| Ideal (0%) | 2.835 (0.037) | 1.414 (0.062) | 2.124 | 0.00 | 0.00 |
| 2% noise | 2.609 (0.049) | 1.280 (0.072) | 1.945 | 0.00 | 0.00 |
| 5% noise | 2.284 (0.054) | 1.160 (0.064) | 1.722 | 0.00 | 0.00 |
| 8% noise | 1.993 (0.053) | 1.006 (0.048) | 1.499 | **0.60** | **0.00** |
| 11% noise | 1.721 (0.063) | 0.866 (0.063) | 1.293 | **1.00** | **0.00** |
| IBM Marrakesh (real device) | 2.742 (0.112) | 1.354 (0.169) | 2.048 | 0.00 | 0.00 |

The fix works exactly as derived: both noise levels where the fixed threshold was broken (8% and 11%) return to FPR = 0.00 under calibration, with no cost at the noise levels that were already fine.

The analytic FPR bound (evaluated at `n_min=800`, §4.1) ranges from `1.2×10⁻²²` (Ideal) to `1.1×10⁻⁸` (11% noise) across the synthetic profiles — many orders of magnitude below what 50 trials could statistically distinguish from zero. With 50 trials, an empirical FPR of 0 is *consistent with* zero, not proof of it; by the rule of three, 0/50 bounds the true FPR at roughly ≤6% (95% confidence), and 0/30 at ≤10%. The "0.00" entries above should be read that way.

IBM_Marrakesh has a much weaker analytic guarantee than the synthetic profiles — only `N=1024` pairs (vs. 8192), giving `n ≈ 113.8` and a bound of `≈1.1×10⁻³`, five to nineteen orders of magnitude looser than the synthetic profiles. The empirical FPR of 0/30 is still consistent with that bound, but the confidence level is genuinely much lower, not just nominally so.

### 6.2 Full attack-fraction sweep (FNR), fixed vs. calibrated

Calibration corrects the honest-channel false-alarm problem, but it does not — and isn't meant to — make weak/stealthy attackers detectable in a single session. At 8% noise (`S*=1.499`), for example:

| `f` | 0.0 | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.6–1.0 |
|---|---|---|---|---|---|---|---|
| FNR, fixed | (FPR 0.60) | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FNR, calibrated | (FPR 0.00) | 1.00 | 1.00 | 1.00 | 0.92 | 0.40 | 0.00 |

This looks worse for FNR at low `f`, but that's the honest trade-off being paid to eliminate the false alarms — the old rule's apparent "good" FNR at low `f` was an artifact of a threshold sitting so low that it was already unreliable on honest traffic. Quantifying the hardest point (8% noise, `f=0.1`): honest `S̄=2.005` vs. attacked `S̄=1.905`, a separation of `Δ=0.100`, giving a detectability index `d′≈1.69` — a real but moderate separation, meaning any single fixed threshold along this axis necessarily trades FPR against FNR at that operating point. That's the direct motivation for Priority 2 (accumulating evidence across multiple sessions) rather than chasing a better single-session threshold.

### 6.3 IBM Marrakesh (real hardware noise)

Run separately by the user against real IBM Quantum backend noise data, using the same script: `Ŝ_H=2.742`, `Ŝ_{f=1}=1.354` → `S*=2.048`.

| `f` | 0.00 | 0.25 | 0.50 | 0.75 | 1.00 |
|---|---|---|---|---|---|
| Fixed `S=2.0` | FPR 0.000 | FNR 1.000 | FNR 0.533 | FNR 0.067 | FNR 0.000 |
| Calibrated `S*` | FPR 0.000 | FNR 1.000 | FNR 0.567 | FNR 0.000 | FNR 0.000 |

Unlike the synthetic 8%/11% profiles, IBM Marrakesh's honest channel was never broken under the old fixed threshold (honest `S̄≈2.7`, comfortably above 2.0) — so this isn't a fix, it's a consistency check, and it holds: FPR stays at 0.000, with a small improvement at `f=0.75` and no meaningful change elsewhere (the `f=0.5` difference is within trial-to-trial noise at only 30 trials).

A notable side finding: the real device's CHSH estimator is noticeably noisier than the synthetic depolarizing model at a comparable operating point — `Std_S ≈ 0.158` on IBM Marrakesh vs. `≈0.063` on the synthetic 8%-noise profile, roughly 2.5×. The synthetic model likely understates real-world estimator variance, which strengthens the case for Priority 4 (hardware validation) beyond just "running on real hardware is good practice."

### 6.4 Mis-calibration robustness (does a stale calibration still work?)

Since calibration is out-of-band, a natural question is how much the channel can drift before a stale `S*` starts failing. Two tests were run.

**One-step drift** (`S*` calibrated at profile X, evaluated at the immediately adjacent noise profile), 50 trials each: all 8 combinations tested — FPR = 0.00 and FNR = 0.00 in every case. A calibration one noise-step out of date shows no measurable degradation.

**Two-step drift** (a tougher test, since the one-step result was uniformly clean enough to risk looking like the test wasn't stressed enough): this surfaced a real robustness boundary.

| Calibrated at | `S*` | Evaluated at | Drift | FPR | FNR |
|---|---|---|---|---|---|
| Ideal (0%) | 2.124 | 5% noise | +2 | 0.000 | 0.000 |
| 5% noise | 1.722 | Ideal (0%) | −2 | 0.000 | 0.000 |
| 2% noise | 1.945 | 8% noise | +2 | **0.240** | 0.000 |
| 8% noise | 1.499 | 2% noise | −2 | 0.000 | 0.000 |
| 5% noise | 1.722 | 11% noise | +2 | **0.580** | 0.000 |
| 11% noise | 1.293 | 5% noise | −2 | 0.000 | 0.000 |

**Mechanism:** failure occurs when `S*` ends up close to or above the drifted-to profile's actual honest `Ŝ_H`. For 2%→8% noise: `S*=1.945` sits just below `Ŝ_H(8%)=1.993`, a gap of only 0.048 — under one honest-channel standard deviation — so a large fraction of honest sessions land below `S*` purely by chance (FPR=0.240). It's worse for 5%→11% noise: `S*=1.722` calibrated at 5% noise is essentially equal to `Ŝ_H(11%)=1.721` — the gap has collapsed to ~0, so roughly half of honest sessions fall below `S*` (FPR=0.580, consistent with a threshold sitting right at the honest mean).

The safe direction — calibrating at *higher* noise and evaluating at *lower* noise (the channel getting cleaner than assumed) — stays safe, because `S*` ends up conservatively far below the drifted-to profile's `Ŝ_H`: e.g. 8%→2% noise, `S*=1.499` vs. `Ŝ_H(2%)=2.609`, a gap of 1.11. This asymmetry — tolerant of the channel improving, intolerant of it getting noisier by more than about one calibration step — sets a practical bound on how infrequently the channel needs to be recharacterized.

IBM Marrakesh was excluded from both drift tests by design: its real gate/readout error composition isn't a point on the same synthetic depolarizing-strength ladder, so "N steps away" isn't a meaningful concept for it.

## 7. What changed in the paper (Overleaf)

Three edits were made to `main.tex`, all in the "Results and Discussion" section:

1. **New methods paragraph** ("Novel Metrics: Statistical Detection" subsection, right after the existing "Decision thresholds" paragraph): introduces the noise-calibrated CHSH threshold, frames it explicitly as the same Hoeffding-balancing method used for the QBER thresholds above (not a new, ad-hoc technique), and explains *why* per-noise-profile calibration is necessary — honest `⟨S⟩` is not noise-invariant the way QBER is, sliding from 2.835 (noiseless) to 1.721 (11% noise). It also clarifies that this is a precomputed, held-fixed characterization (like Lee/Fiorini's own thresholds), not the live/adaptive scheme the paper elsewhere explains was considered and set aside.

2. **New results content** ("Robustness to Channel Noise" subsection, placed right after the existing paragraph describing the fixed-threshold failure at 8%/11% noise — a natural problem→solution flow): a new table (`Table III` in the compiled PDF) reporting `S*`, fixed-threshold FPR, and calibrated-threshold FPR for all six noise profiles; prose explaining the fix and pointing to a new figure (the full attack-fraction sweep, fixed vs. calibrated, across all six profiles); and a paragraph covering the mis-calibration robustness results (one-step: uniformly safe; two-step: two failure cases identified and explained, with the safe-direction asymmetry noted).

3. **Updated "Summary of Findings" table**: E91's row now shows the calibrated threshold `S*` (rather than the old fixed `S=2.0`) and FPR at 11% noise of `0.00` (rather than the old `1.00`), with an added caveat sentence clarifying that E91's compared-signal count `K` and secure-key-rate entries in that same table are unchanged from the original fixed-threshold analysis and have not been rederived under calibration — so the table doesn't imply more was recomputed than actually was.

One item is still pending on the paper side: the new figure file (`fig_e91_calibrated_threshold.pdf`) needs to be manually uploaded into Overleaf's Figures folder before it will render (automated upload wasn't safely achievable through the browser-automation tooling used for these edits); the document currently compiles cleanly with a draft placeholder in its place.

## 8. Known assumptions and limitations (for the record)

1. The derivation is over signed `S`, but the code takes `abs(S)`. This wasn't observed to matter anywhere in the tested range (`S` was never within ~0.86 of zero), but the derivation doesn't formally cover the region near zero.
2. Calibration targets the full-attack case, not any specific stealthy fraction — deliberate, for consistency with the BB84/six-state convention. Priority 2's planned sequential detector is meant to cover weak-attacker detection instead of re-targeting this threshold.
3. Sample sizes: 30 calibration / 50 evaluation trials for the synthetic profiles; 15 calibration / 30 evaluation for IBM Marrakesh (kept smaller because of the real noise model's higher per-trial runtime cost) — this directly weakens IBM Marrakesh's analytic FPR guarantee relative to the synthetic profiles (see §6.1/§6.3).
4. `Ŝ_H` / `Ŝ_{f=1}` vary by about ±0.02 across reruns with nominally identical seeds, because Qiskit Aer's internal shot-sampling RNG isn't tied to numpy's seed. This propagates to about ±0.01–0.02 variability in `S*` — negligible next to the honest–attacked gap (0.86 to 1.42 across profiles), and consistent with ordinary Monte Carlo standard error for a 30-trial mean. Only exact bit-for-bit reproduction of one specific run is affected, not the conclusions.

## 9. Source files

- `updates/Priority1_CHSH_Threshold_Derivation.md` — first-pass working derivation.
- `updates/Priority1_Verification_Report.md` — full verification report (two independent review passes, all numbers re-derived and cross-checked; this is the authoritative source for the exact figures used above).
- `updates/priority1_verification_changes.md` — changelog of what was corrected between verification passes.
- `e91_adaptive_threshold.py` — script implementing per-profile calibration and the FPR/FNR sweep.
- `qkd_e91_calibrated.csv` — full sweep output (all six noise profiles × all attack fractions).
- `qkd_e91_miscalibration.csv`, `two_step_miscal.csv` — mis-calibration robustness check outputs (one-step and two-step drift).
- `figures/fig_e91_calibrated_threshold.py` (+ `.pdf`/`.svg`/`.png`) — the new comparison figure (fixed vs. calibrated FPR/FNR across all six profiles).
