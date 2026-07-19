"""
============================================================================
 SCRIPT: RECOMPUTE THE E91 ROW OF THE SUMMARY TABLE UNDER S*
============================================================================
 Reads the calibrated-S* sweeps and prints the three threshold-dependent
 numbers that make up the E91 row of tab:summary, so the paper's E91 row
 stops mixing the old S=2.0 rule with the new S*:

   1. stealth-window edge  = largest f where FNR is still ~1 (== 1.0)
   2. detection onset      = smallest f where FNR <= 0.5
   3. K for FPR <= 5%      = smallest sample size K (5% honest channel)
                             at which FPR falls to <= 0.05, plus a linear
                             interpolation of the exact crossing for context

 Panels 1-2 use the ideal (clean) channel, S*_ideal = 2.124, from
 qkd_e91_calibrated.csv. Panel 3 uses the 5% honest channel, S*_5% = 1.722,
 from qkd_e91_resource_cost_calibrated.csv.

 Pure standard-library + numpy (no pandas), so it runs in the same
 environment as the simulation. Run AFTER e91_resource_cost_calibrated.py.
============================================================================
"""

import csv
import os
import numpy as np

CAL = "qkd_e91_calibrated.csv"
RC = "qkd_e91_resource_cost_calibrated.csv"


def _read(path):
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        return list(r)


def stealth_and_onset(profile="Ideal_0%"):
    rows = [row for row in _read(CAL)
            if row["Noise_Profile"] == profile and float(row["F_Eve"]) > 0.0]
    rows.sort(key=lambda r: float(r["F_Eve"]))
    f = np.array([float(r["F_Eve"]) for r in rows])
    fnr = np.array([float(r["FNR"]) for r in rows])

    # largest f where FNR is still essentially 1 (missed on ~every trial)
    still_one = f[np.isclose(fnr, 1.0)]
    stealth_edge = float(still_one.max()) if len(still_one) else float("nan")

    # smallest f where FNR has dropped to <= 0.5 (detector wins the coin flip)
    detected = f[fnr <= 0.5]
    onset = float(detected.min()) if len(detected) else float("nan")
    return stealth_edge, onset, list(zip(f, fnr))


def k_for_fpr(target=0.05):
    if not os.path.exists(RC):
        return None, None, None
    rows = [row for row in _read(RC) if row["Protocol"] == "E91"]
    rows.sort(key=lambda r: int(r["K"]))
    K = np.array([float(r["K"]) for r in rows])
    fpr = np.array([float(r["FPR"]) for r in rows])

    below = K[fpr <= target]
    k_step = int(below.min()) if len(below) else None

    # linear interpolation of the exact K where FPR crosses `target`
    k_interp = None
    for i in range(len(K) - 1):
        if fpr[i] > target >= fpr[i + 1]:
            frac = (fpr[i] - target) / (fpr[i] - fpr[i + 1])
            k_interp = float(K[i] + frac * (K[i + 1] - K[i]))
            break
    return k_step, k_interp, list(zip(K.astype(int), fpr))


if __name__ == "__main__":
    print("=" * 60)
    print(" E91 SUMMARY-TABLE ROW UNDER CALIBRATED S*")
    print("=" * 60)

    stealth_edge, onset, curve = stealth_and_onset()
    print("\nIdeal channel (S*_ideal = 2.124), FNR-vs-f:")
    for f, v in curve:
        print(f"    f={f:.2f} | FNR={v:.2f}")
    print(f"\n  1. stealth-window edge (largest f with FNR~1): f = {stealth_edge:.2f}")
    print(f"  2. detection onset     (smallest f, FNR<=0.5): f = {onset:.2f}")

    k_step, k_interp, fpr_curve = k_for_fpr()
    if fpr_curve is None:
        print("\n  3. K for FPR<=5%: qkd_e91_resource_cost_calibrated.csv not found --")
        print("     run e91_resource_cost_calibrated.py first.")
    else:
        print("\n5% honest channel (S*_5% = 1.722), FPR-vs-K:")
        for k, v in fpr_curve:
            print(f"    K={k:<5} | FPR={v:.3f}")
        interp_str = f"{k_interp:.0f}" if k_interp is not None else "n/a"
        print(f"\n  3. K for FPR<=5%: first swept K with FPR<=0.05 = {k_step} "
              f"(interpolated crossing ~ K={interp_str})")
    print("=" * 60)
