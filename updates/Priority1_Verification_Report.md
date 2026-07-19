# Verification Report: Noise-Calibrated CHSH Detection Threshold for E91 (v2)

**Purpose of this document:** a self-contained technical report on a new eavesdropper-detection threshold derived for the E91 QKD protocol. v1 of this report was reviewed by another model; that review confirmed the derivation and headline result but flagged eight presentation/rigor items, all addressed below (each independently re-verified here, not just copied from the review — two of the review's own numbers required a follow-up simulation to confirm, which is now included). A second pass caught a small numeric inconsistency and two other fixes, also applied below. Section 7 lists open questions for further checking.

---

## 1. Background

This is part of a QKD research paper comparing eavesdropping detection across three protocols: BB84, six-state, and E91. BB84 and six-state detect eavesdropping via the Quantum Bit Error Rate (QBER) against fixed thresholds (0.135, 0.167) derived in prior published work (Lee et al. for BB84, Fiorini et al. for six-state) using Hoeffding's inequality to balance false positive rate (FPR: false alarm on an honest channel) against false negative rate (FNR: missed detection under attack).

E91 is entanglement-based and detects eavesdropping via the CHSH Bell statistic `S` instead of QBER. Until this work, E91 used the fixed classical bound `S < 2.0` as the alarm threshold — a **security bound**, not a **statistically calibrated detection threshold**. This report derives and validates a calibrated alternative.

## 2. The system under study, as actually implemented

Alice uses 3 angles `{0, π/4, π/2}` (indices 0,1,2), Bob uses `{π/4, π/2, 3π/4}` (indices 0,1,2), chosen uniformly at random and independently per entangled pair. Key bits come from matched-basis pairs (Alice=1,Bob=0) and (Alice=2,Bob=1). CHSH uses the other four combinations:

```python
def expect(a_i, b_i):
    mask = (alice_bases == a_i) & (bob_bases == b_i)
    if not np.any(mask): return 0
    matches = np.sum(alice_results[mask] == bob_results[mask])
    mismatches = np.sum(alice_results[mask] != bob_results[mask])
    return (matches - mismatches) / (matches + mismatches)

S = expect(0, 0) - expect(0, 2) + expect(2, 0) + expect(2, 2)
return abs(S), ...   # the function returns abs(S), not S
```
(`run_e91_trial`, `detection_aware_qkd_varying_eve.py`.)

Existing rule: `alarm_triggered = S < chsh_threshold`, fixed at `2.0` for every noise condition and attack strength. Attacker model: partial intercept-resend at fraction `f ∈[0,1]`; `f=0` measures FPR, `f>0` measures FNR, both as empirical frequencies over independent Monte Carlo trials (`monte_carlo_e91`, same file).

Six noise conditions: five synthetic depolarizing profiles (`Ideal_0%` … `Threshold_11%`, named for the honest QBER they'd produce in BB84/six-state) plus one real-hardware noise model extracted from IBM's `ibm_marrakesh` backend.

## 3. Derivation

**Step 1.** Each pair's contribution to `expect(a,b)` is exactly `+1` (match) or `−1` (mismatch); `Ê(a,b)` is the sample mean over the `n_{a,b}` pairs landing in that basis combination.

**Step 2 — effective sample size.** Alice and Bob each pick uniformly among 3 bases independently, so each of 9 `(a,b)` combinations gets `N/9` pairs on average (`N=8192` ⇒ mean ≈910); 4 of the 9 feed into `S`. The four counts are multinomial, not fixed — see §3.1 for how this is handled rigorously.

**Step 3 — Hoeffding bound.** Conditional on the realized sample sizes, write `Ŝ − S = (T−E[T])/n` with `T = Σ c(j)ξ_j` over `4n` independent ±1-bounded terms (`c=(+1,−1,+1,+1)`; the derivation is insensitive to which sign pattern is used, since only `|c_j|=1` matters for the bound width). By Hoeffding's inequality for independent bounded variables:

`P(T−E[T] ≥ t) ≤ exp(−2t²/Σ(b_j−a_j)²) = exp(−2t²/(4n·4)) = exp(−t²/8n)`

Substituting `t=nδ`: `P(Ŝ−S ≥ δ) ≤ exp(−nδ²/8)`, two-sided: `P(|Ŝ−S|≥δ) ≤ 2exp(−nδ²/8)`.

**Step 4 — balanced threshold.** For `S_f < S* < S_H`: FPR bound `≤ exp(−n(S_H−S*)²/8)`, FNR bound `≤ exp(−n(S*−S_f)²/8)`. Equalizing exponents: `S* = (S_H+S_f)/2`.

*(Confirmed correct on review: the algebra in Steps 3–4 and the sign-vector argument both check out.)*

### 3.1 Handling the multinomial sample sizes rigorously

Condition on the realized per-combination sample sizes `n_1,n_2,n_3,n_4`. Each one-sided sub-bound then holds *exactly* for its own realized `n_i` (Hoeffding doesn't require `n_i` to be non-random once conditioned on). The worst case across the four is governed by `n_min = min(n_1,...,n_4)`.

For `N=8192`, each `n_i` is (marginally) approximately Normal with mean 910.2 and std 28.4 (from the multinomial variance `N·p·(1−p)`, `p=1/9`). `P(n_i < 800) ≈ 5.3×10⁻⁵` per combination; union bound over the 4 relevant combinations gives `P(n_min < 800) ≲ 2.1×10⁻⁴`. So: **conditional on the high-probability event `n_min ≥ 800` (probability ≥ ~0.9998 for N=8192), the bound holds using `n=800` as a floor, without needing the equal-group-size approximation.** This is a high-probability conditional statement, not a claim that holds with certainty.

## 4. Empirical validation methodology

Calibration is treated as an out-of-band process, independent of the live detection test (mirrors how real QKD systems characterize channel noise separately from the session being tested — a deliberate design choice, not a data-driven one). For each noise profile: `S_H` and `S_f=1` are each estimated from 30 independent trials (disjoint from the evaluation trials), `S* = (Ŝ_H+Ŝ_f=1)/2` is fixed, then evaluation sweeps `f=0.0,...,1.0` at 50 trials each (30 for IBM_Marrakesh, matching its existing smaller-scale methodology). Calibration targets the **full-attack case (`f=1`)**, matching the BB84/six-state convention — deliberately not optimized for weak/stealthy attackers (`f=0.1–0.3`), which a separate planned sequential/multi-session detector is meant to handle.

## 5. Results

### 5.1 Honest-channel FPR: fixed threshold vs. calibrated threshold, with full auditability

| Noise profile | Ŝ_H (std) | Ŝ_f=1 (std) | S* | FPR, fixed S=2.0 | FPR, calibrated S* | Analytic FPR bound (n_min=800) |
|---|---|---|---|---|---|---|
| Ideal_0% | 2.835 (0.037) | 1.414 (0.062) | 2.124 | 0.00 | 0.00 | 1.2×10⁻²² |
| Noise_2% | 2.609 (0.049) | 1.280 (0.072) | 1.945 | 0.00 | 0.00 | 6.6×10⁻²⁰ |
| Noise_5% | 2.284 (0.054) | 1.160 (0.064) | 1.722 | 0.00 | 0.00 | 2.0×10⁻¹⁴ |
| Noise_8% | 1.993 (0.053) | 1.006 (0.048) | 1.499 | **0.60** | **0.00** | 2.6×10⁻¹¹ |
| Threshold_11% | 1.721 (0.063) | 0.866 (0.063) | 1.293 | **1.00** | **0.00** | 1.1×10⁻⁸ |
| IBM_Marrakesh | 2.742 (0.112) | 1.354 (0.169) | 2.048 | 0.00 | 0.00 | 1.1×10⁻³ (see §5.2 note) |

(All bounds computed from `n_min=800` per §3.1, not the `n≈910` mean used in v1 — this widens the synthetic-profile range from v1's stated "1e-10 to 1e-25" to the correct **1.1×10⁻⁸ to 1.2×10⁻²²**. The v1 range understated how weak the bound gets at Threshold_11% specifically.)

**Statistical caveat:** with 50 trials (30 for IBM_Marrakesh), an empirical FPR of 0 is a *consistent-with-zero* observation, not a *proof* of zero. By the rule of three, 0/50 bounds the true FPR at ≲6% (95% CI), and 0/30 at ≲10%. All the "0.00" FPR entries above should be read this way — as not contradicting the analytic bound (which predicts FPR many orders of magnitude below what 50 trials could even detect), not as independent confirmation of a bound that small.

### 5.2 Full attack-fraction sweep (FNR), fixed vs. calibrated

**Noise_8% (S*=1.499 vs. fixed 2.0):**

| f | 0.0 | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.6-1.0 |
|---|---|---|---|---|---|---|---|
| FNR, fixed | (FPR 0.60) | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| FNR, calibrated | (FPR 0.00) | 1.00 | 1.00 | 1.00 | 0.92 | 0.40 | 0.00 |

**Threshold_11% (S*=1.293 vs. fixed 2.0):**

| f | 0.0 | 0.1 | 0.2 | 0.3 | 0.4 | 0.5 | 0.6 | 0.7-1.0 |
|---|---|---|---|---|---|---|---|---|
| FNR, fixed | (FPR 1.00) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.06 | 0.00 |
| FNR, calibrated | (FPR 0.00) | 1.00 | 1.00 | 1.00 | 0.96 | 0.56 | 0.06 | 0.00 |

**Quantified separation at the hardest point (Noise_8% at f=0.1):** evaluation-sweep statistics give honest `S̄=2.005` (std 0.063) vs. attacked-at-f=0.1 `S̄=1.905` (std 0.055). **Δ = 2.005 − 1.905 = 0.100.** Using a pooled-standard-deviation detectability index (`d' = Δ/√((σ₁²+σ₂²)/2)`), `d' ≈ 1.69`. This is a moderate, not negligible, separation — it does **not** support a strict "any ratio below 1 makes separation impossible" claim (that specific framing, offered in the prior review, isn't independently confirmed here: depending on which denominator convention is used, the ratio ranges from 0.85 [sum of stds] to 1.59 [honest std alone] to 1.69 [pooled/d'], so no clean unit threshold holds up across conventions). What the number does support: the honest and weakly-attacked distributions overlap enough that **any single fixed threshold along this axis trades FPR against FNR** — pushing the threshold to catch more of the `f=0.1` cases necessarily catches more honest sessions too. That is a real constraint on single-session detection at this noise level, not an artifact of this particular calibration choice — but it's a continuous tradeoff (an ROC-curve reality), not a hard binary cutoff. This is the motivation for accumulating evidence across sessions (a separate, planned sequential detector) rather than seeking a better single-session threshold.

**IBM_Marrakesh (S*=2.048 vs. fixed 2.0), 30 trials, 1024 pairs:**

| f | 0.00 | 0.25 | 0.50 | 0.75 | 1.00 |
|---|---|---|---|---|---|
| FNR/FPR, fixed | FPR 0.000 | FNR 1.000 | FNR 0.533 | FNR 0.067 | FNR 0.000 |
| FNR/FPR, calibrated | FPR 0.000 | FNR 1.000 | FNR 0.567 | FNR 0.000 | FNR 0.000 |

Calibration: `Ŝ_H=2.742` (std 0.112), `Ŝ_f=1=1.354` (std 0.169), 15 calibration trials each.

**Weaker analytic guarantee on this profile:** `N=1024` here (vs. 8192 for the synthetic ladder) ⇒ `n=N/9≈113.8`. With `δ=Ŝ_H−S*=0.694`: bound `= exp(−113.8×0.694²/8) ≈ 1.1×10⁻³` — **five to nineteen orders of magnitude weaker** than the synthetic profiles' bounds in §5.1. The empirical FPR (0.000 over 30 trials) remains consistent with this bound (rule of three: ≲10%), but the analytic guarantee here is genuinely much looser, not just nominally so — worth stating explicitly in the paper rather than implying IBM_Marrakesh has the same confidence level as the synthetic profiles.

Additional observation: `Std_S` on IBM_Marrakesh honest channel (≈0.158, evaluation sweep) is roughly 2.5x the synthetic Noise_8% profile's (≈0.063) at a broadly comparable nominal noise level — the real device's CHSH estimator is noticeably noisier than the synthetic depolarizing model predicts.

### 5.3 Mis-calibration robustness check — one-step and two-step drift

**One-step drift** (S* calibrated at profile X, evaluated at the immediately adjacent profile), 50 trials each:

| Calibrated at | S* | Evaluated at | Drift | FPR | FNR |
|---|---|---|---|---|---|
| Ideal_0% | 2.124 | Noise_2% | +1 | 0.00 | 0.00 |
| Noise_2% | 1.945 | Ideal_0% | −1 | 0.00 | 0.00 |
| Noise_2% | 1.945 | Noise_5% | +1 | 0.00 | 0.00 |
| Noise_5% | 1.722 | Noise_2% | −1 | 0.00 | 0.00 |
| Noise_5% | 1.722 | Noise_8% | +1 | 0.00 | 0.00 |
| Noise_8% | 1.499 | Noise_5% | −1 | 0.00 | 0.00 |
| Noise_8% | 1.499 | Threshold_11% | +1 | 0.00 | 0.00 |
| Threshold_11% | 1.293 | Noise_8% | −1 | 0.00 | 0.00 |

**Two-step drift** (newly run, since uniformly clean 1-step results risked reading as "not stressed enough" rather than "genuinely robust"). This test found a real robustness boundary the 1-step test did not surface:

| Calibrated at | S* | Evaluated at | Drift | FPR | FNR |
|---|---|---|---|---|---|
| Ideal_0% | 2.124 | Noise_5% | +2 | 0.000 | 0.000 |
| Noise_5% | 1.722 | Ideal_0% | −2 | 0.000 | 0.000 |
| Noise_2% | 1.945 | Noise_8% | +2 | **0.240** | 0.000 |
| Noise_8% | 1.499 | Noise_2% | −2 | 0.000 | 0.000 |
| Noise_5% | 1.722 | Threshold_11% | +2 | **0.580** | 0.000 |
| Threshold_11% | 1.293 | Noise_5% | −2 | 0.000 | 0.000 |

**Mechanism:** the failure occurs when `S*` ends up close to or above the drifted-to profile's actual honest `Ŝ_H`. For Noise_2%→Noise_8%: `S*=1.945` is just below `Ŝ_H(Noise_8%)=1.993` — a gap of only 0.048, under one honest-channel standard deviation (≈0.05), so a substantial fraction of honest sessions fall below `S*` by chance (FPR=0.240). It gets worse for Noise_5%→Threshold_11%: `S*=1.722` calibrated at Noise_5% is essentially equal to `Ŝ_H(Threshold_11%)=1.721` — the gap has collapsed to ~0, so roughly half of honest sessions fall below `S*` (FPR=0.580, consistent with a threshold sitting at the honest mean). The safe direction (calibrating at higher noise, evaluating at lower) instead has `S*` ending up *far below* the drifted-to profile's `Ŝ_H` — e.g. Noise_8%→Noise_2%: `S*=1.499` vs. `Ŝ_H(Noise_2%)=2.609`, a gap of 1.11 — making the threshold conservative rather than dangerous, hence FPR=0.000 in both safe-direction rows.

**Practical implication for the paper:** recalibration should happen at least every ~1 noise-step of expected drift, and the direction of expected drift matters — the safe margin is asymmetric, more tolerant of the channel getting cleaner than assumed than of it getting noisier.

IBM_Marrakesh is excluded from both drift checks by design — its noise composition (real gate/readout error channels) isn't a point on the same depolarizing-strength ladder, so "N steps away" isn't defined for it.

## 6. Remaining assumptions and limitations

1. **`abs(S)` vs. signed `S`:** the derivation is over signed `S`; the code takes `abs(S)`. Not observed to matter in the tested range (`S` never within ~0.86 of zero), but the derivation doesn't formally cover the region near zero.
2. **Calibration target = full attack, not a specific stealthy fraction** — deliberate, for consistency with the BB84/six-state convention; a separate sequential detector is intended to cover weak-attacker detection instead of re-targeting this threshold.
3. **Per-noise-profile calibration, not a single universal threshold** — a single fixed `S*` (calibrated at the worst-case 11% profile) was checked analytically and found to leave a 100%-interception attacker undetected on average at `Ideal_0%`/`Noise_2%`; this is why per-profile calibration was adopted.
4. **Sample sizes:** 30 calibration / 50 evaluation trials for synthetic profiles; 15 calibration / 30 evaluation for IBM_Marrakesh (smaller, to keep runtime reasonable given the real noise model's higher per-trial cost) — see §5.2 for how this affects IBM_Marrakesh's analytic guarantee specifically.
5. **RNG reproducibility:** `Ŝ_H`/`Ŝ_f=1` vary by ≈0.02 across reruns with nominally identical seeds, because Qiskit Aer's internal shot-sampling RNG is not tied to `numpy`'s seed. This propagates to ≈0.01–0.02 variability in `S*` — negligible relative to the honest–attacked gap, which ranges from 0.86 (Threshold_11%) to 1.42 (Ideal_0%) across profiles. The observed variation is also consistent with ordinary Monte Carlo standard error for a 30-trial mean (≈ std/√30 ≈ 0.01). Conclusions are robust to this; only bit-for-bit reproduction of one specific run is affected.

## 7. Open questions for further review

1. Is the `n_min`-conditional argument in §3.1 the right way to handle the multinomial sample sizes, or is there a cleaner formulation?
2. Is the `d'≈1.69` framing in §5.2 (continuous tradeoff, not a hard binary threshold) the right level of claim, or should this be tightened further / left out until it can be derived more rigorously?
3. Does the two-step mis-calibration mechanism (§5.3 — failure when `S*` closes in on the drifted-to profile's `Ŝ_H`) suggest a specific, derivable recalibration-interval rule (e.g. in terms of `(Ŝ_H − S*)/σ`), rather than the qualitative statement given here?
4. Are the empirical zero-FPR results now adequately caveated (rule of three, §5.1) given the 30–50-trial sample sizes, or is more needed?
5. Anything else that looks wrong, unjustified, or overclaimed.

## Changelog

**v1 → v2**, addressing an external model review (8 items): recomputed the analytic FPR bound range using `n_min` instead of mean `n` (item 1 — this required redoing every bound in §5.1; the v1 range was optimistic, especially at Threshold_11%), added the rule-of-three caveat (item 2), replaced the unresolved multinomial-sample-size approximation with a precise conditional argument using `n_min` (item 3), flagged IBM_Marrakesh's much weaker analytic guarantee with the actual computed number, ≈1.1×10⁻³ vs. 1.2×10⁻²² for the best synthetic profile (item 4), added raw `Ŝ_H`/`Ŝ_f=1` values (with std) for every profile so the arithmetic is independently auditable (item 5), added a quantified separation measure (`d'`) for the FNR tradeoff claim, while noting the reviewer's proposed strict "ratio < 1" threshold doesn't hold up cleanly across different denominator conventions (item 6), softened and quantified the RNG-reproducibility caveat with actual numbers instead of "not guaranteed" (item 7), and ran a new two-step drift simulation instead of just adding a caveat sentence (item 8) — which surfaced a real, previously invisible robustness boundary (safe toward lower noise, degrading toward higher noise by two steps).

**v2 → v2.1**, addressing a second-pass check: fixed a 0.099-vs-0.100 rounding inconsistency in §5.2 by stating the separation explicitly as `Δ = 2.005 − 1.905 = 0.100`; added the causal mechanism sentence to §5.3 explaining *why* the two-step drift fails in one direction and not the other (`S*` closing in on or exceeding the drifted-to profile's `Ŝ_H`) rather than just reporting that it does; and completed the changelog itself, which had been truncated mid-sentence in the previous file. (This pass updated `Δ` but missed propagating it through all three ratio conventions — see v2.2.)

**v2.1 → v2.2** (this revision): the Δ=0.100 fix in v2.1 wasn't fully propagated — the three separation ratios (sum-of-stds, honest-std-alone, pooled/`d'`) were a stale mix computed against different Δ values. All three recomputed fresh against Δ=0.100: sum-of-stds 0.85 (was stated 0.84), honest-std-alone 1.59 (unchanged), pooled `d'` 1.69 (was stated 1.68). Updated in §5.2 and in the corresponding §7 open question. No conclusions change — this is a third-decimal-place correction, not a substantive one.
