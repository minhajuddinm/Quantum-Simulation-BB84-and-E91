# Priority 1 Verification — Recommended Changes

Verification pass on the E91 CHSH detection threshold derivation. Math and headline results check out; the items below are presentation/rigor tightening.

---

## What's correct (no change needed)

- Hoeffding derivation in §3, Steps 3 and 4 — algebra is right end-to-end.
- Balanced threshold formula `S* = (S_H + S_f)/2` — correctly derived.
- Sign vector `c = (+1, −1, +1, +1)` does not affect the bound (|c_j|=1).
- IBM_Marrakesh S* = (2.742 + 1.354)/2 = 2.048 — matches table.

---

## Changes required

### 1. Widen or split the analytic FPR range (§5.1)

**Current claim:** "on the order of 1e-10 to 1e-25"

**Problem:** Threshold_11% profile has the smallest honest-attacked gap; back-of-envelope with δ ≈ 0.35–0.40 gives exp(−17) ≈ 4e−8, which is **outside** the stated lower bound.

**Fix:** Either
- Widen to "on the order of 1e−7 to 1e−25", OR
- Split per-profile with the actual δ for each row.

---

### 2. Add rule-of-3 caveat to empirical zero-FPR claims (§5.1, §5.3)

**Problem:** Empirical "FPR 0.00" over 50 trials only bounds true FPR at ~6% (95% CI); over 30 trials at ~10%. Currently reads as demonstration rather than "not contradicting" the analytic bound.

**Fix — add one sentence to §5.1:**
> Given 50 trials (30 for IBM_Marrakesh), an empirical FPR of 0 is consistent with true FPR up to ~6% (~10%) by the rule of three, and with the analytic Hoeffding bound throughout that interval.

---

### 3. Rewrite §6 item 1 (multinomial group sizes)

**Problem:** Currently framed as an unresolved approximation. It's actually removable.

**Fix — replace with:**
> Condition on the realized per-combination sample sizes (n_1, n_2, n_3, n_4). The four one-sided sub-bounds each hold with their own n_i; the worst case is bounded by exp(−n_min · δ² / 8). For N=8192, n_min > 800 with overwhelming probability, so the reported bounds hold at n = n_min without approximation.

This eliminates the caveat rather than defending it.

---

### 4. Flag IBM_Marrakesh's weaker analytic guarantee (§5.2, IBM_Marrakesh subsection)

**Problem:** N=1024 → n ≈ 113 → analytic FPR bound ≈ 1e−3, not 1e−13. Currently unstated.

**Fix — add to the IBM_Marrakesh paragraph:**
> Because N=1024 for this profile (vs. 8192 for the synthetic ladder), the analytic Hoeffding bound is exp(−113 · 0.482 / 8) ≈ 1e−3 — orders of magnitude weaker than the synthetic profiles, though the empirical FPR (0.000) remains consistent with the bound.

---

### 5. Surface raw calibration values for all profiles (§5.1)

**Problem:** Only IBM_Marrakesh's Ŝ_H and Ŝ_f=1 are reported (2.742, 1.354). For the other five profiles the S* value is stated but the inputs are not, so the arithmetic can't be independently verified.

**Fix:** Add two columns to the §5.1 table: `Ŝ_H (std)` and `Ŝ_f=1 (std)`. Makes the calculation auditable end-to-end.

---

### 6. Strengthen §5.2 tradeoff interpretation

**Current:** Explains the FNR-increase-at-weak-attack as an expected artifact of the fixed threshold's inflated FPR.

**Fix — add supporting number:**
> For Noise_8%, |Ŝ_H − Ŝ_f=0.1| relative to Std_Ŝ is [X]. When this ratio is < 1, no single-session threshold can reliably separate the honest and weakly-attacked distributions — the FNR at f=0.1 under any FPR-calibrated threshold is then a hard information-theoretic bound, not a design choice.

Turns the "expected tradeoff" claim into a hard bound.

---

### 7. Soften §6 item 6 (Aer RNG reproducibility)

**Current:** Reads as "reproducibility not guaranteed" — worse than reality.

**Fix — replace with:**
> Ŝ_H and Ŝ_f=1 vary by ~0.02 across reruns due to Aer's independent RNG state. This propagates to ~0.01 variability in S*, which is negligible relative to the honest–attacked gap (0.5–1.4). Conclusions are robust; only bit-for-bit reproduction of a specific run is affected.

---

### 8. Stress-test the mis-calibration robustness (§5.3)

**Problem:** All 8 combinations = 0.00/0.00 is uniformly clean. A reviewer may read this as "not stressed enough" rather than "genuinely robust."

**Fix — add either:**
- A two-step drift row (calibrate at Noise_2%, evaluate at Noise_8%), OR
- A one-line note: "One-step drift on this grid keeps S* well within [Ŝ_f=1, Ŝ_H] for the adjacent profile; the FPR/FNR margin only degrades under drift ≥ [X] steps."

---

## Suggested addition to §7 (reviewer questions)

Add:
> 8. Are the empirical zero-FPR results reported with adequate statistical caveating (rule of three) given the 30–50-trial sample size, or should they be explicitly stated as consistent-with-zero rather than proven-zero?

---

## Bottom line

Nothing above overturns the derivation or the headline result. The E91 threshold is sound and the empirical evidence supports it. The changes above make the report harder to attack on the empirical claims (items 1, 2, 4), remove one unnecessary caveat (item 3), and add auditability (item 5).
