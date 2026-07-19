"""
============================================================================
 SCRIPT: E91 RESOURCE-COST (K-SWEEP) UNDER THE NOISE-CALIBRATED THRESHOLD S*
============================================================================
 Purpose
   Re-run ONLY the E91 sample-size (K) sweep that feeds
   `figures/fig_resource_cost.pdf`, replacing the old fixed alarm rule
   (S < 2.0) with the noise-calibrated threshold S* = (S_H + S_f)/2 used
   everywhere else in the journal upgrade.

   Two panels, two operating points -- matching the original K-sweep in
   detection_aware_qkd_sample_size.py, only the E91 threshold changes:

     panel (a)  FPR vs K   honest 5% channel (p_noise = 0.10, f = 0),
                           threshold S*_5%   (~1.722)
     panel (b)  FNR vs K   clean channel under full attack (p_noise = 0,
                           f = 1),  threshold S*_ideal (~2.124)

   BB84 and six-state are NOT touched here -- their K-sweep rows stay
   exactly as published in qkd_resource_cost.csv. The figure script reads
   BB84/six-state from that file and E91 from the file this script writes.

 S* is CALIBRATED in code from held-out trials (independent of the K-sweep
 evaluation trials), then asserted against the already-reported per-profile
 values as a sanity check -- it is never hardcoded into the alarm rule.

 S* is a property of the noise profile (a function of the honest and
 full-attack MEAN CHSH), not of the sample size K: only the variance of the
 measured S shrinks with K. So S* is calibrated once per profile at a fixed
 reference scale and then held constant across every K -- which is exactly
 the question this figure answers ("with the alarm threshold fixed, how many
 compared signals K are needed to drive FPR/FNR below 5%?").

 Output file
   qkd_e91_resource_cost_calibrated.csv   Protocol,K,Trials,FPR,FNR
                                          (Protocol is always E91)
============================================================================
"""

import csv
import os
import time
import numpy as np

import detection_aware_qkd_varying_eve as base
from e91_adaptive_threshold import calibrate_e91_threshold


# ===========================================================================
# CONFIG (mirrors detection_aware_qkd_sample_size.py for E91)
# ===========================================================================
K_VALUES = [100, 200, 300, 500, 1000, 2000, 3000]
TRIALS = 200

# Operating points, unchanged from the original E91 K-sweep:
P_NOISE_FPR = 0.10   # honest 5% channel (Noise_5% profile) -> false alarms
P_NOISE_FNR = 0.0    # clean channel, full attack           -> missed attacker

# Calibration reference scale. S* depends only on the honest/full-attack MEAN
# CHSH, which is K-independent, so we estimate it once at a large, stable scale
# on trials that are HELD OUT from the K-sweep evaluation below (distinct seeds).
CALIB_PAIRS = 8192
CALIB_TRIALS = 30

# Already-reported per-profile S* values (updates/Priority1_*.md, qkd_e91_calibrated.csv).
# Used ONLY as a Monte-Carlo sanity assertion, never fed into the alarm rule.
EXPECTED_S_STAR_IDEAL = 2.124
EXPECTED_S_STAR_5PCT = 1.722
SANITY_TOL = 0.05

OUT_CSV = "data/qkd_e91_resource_cost_calibrated.csv"


# ===========================================================================
# CALIBRATION (held out from evaluation)
# ===========================================================================
def calibrate():
    print("==========================================")
    print(" CALIBRATING S* (held-out trials)")
    print("==========================================")

    # panel (b) FNR is evaluated on the clean channel -> use the ideal S*.
    S_star_ideal, S_H_i, S_H_i_std, S_f_i, S_f_i_std = calibrate_e91_threshold(
        CALIB_PAIRS, p_noise=0.0, model=None, calib_trials=CALIB_TRIALS, seed=7001)
    print(f"  ideal (clean):  S_H={S_H_i:.4f} (+/-{S_H_i_std:.4f})  "
          f"S_f={S_f_i:.4f} (+/-{S_f_i_std:.4f})  =>  S*_ideal = {S_star_ideal:.4f} "
          f"(expected ~{EXPECTED_S_STAR_IDEAL})")

    # panel (a) FPR is evaluated on the 5% honest channel -> use the 5% S*.
    S_star_5, S_H_5, S_H_5_std, S_f_5, S_f_5_std = calibrate_e91_threshold(
        CALIB_PAIRS, p_noise=P_NOISE_FPR, model=None, calib_trials=CALIB_TRIALS, seed=7002)
    print(f"  5% honest:      S_H={S_H_5:.4f} (+/-{S_H_5_std:.4f})  "
          f"S_f={S_f_5:.4f} (+/-{S_f_5_std:.4f})  =>  S*_5% = {S_star_5:.4f} "
          f"(expected ~{EXPECTED_S_STAR_5PCT})")

    assert abs(S_star_ideal - EXPECTED_S_STAR_IDEAL) < SANITY_TOL, (
        f"S*_ideal={S_star_ideal:.4f} deviates from expected "
        f"{EXPECTED_S_STAR_IDEAL} by more than {SANITY_TOL} -- investigate before trusting the sweep.")
    assert abs(S_star_5 - EXPECTED_S_STAR_5PCT) < SANITY_TOL, (
        f"S*_5%={S_star_5:.4f} deviates from expected "
        f"{EXPECTED_S_STAR_5PCT} by more than {SANITY_TOL} -- investigate before trusting the sweep.")
    print("  [sanity check passed: both S* within tolerance of the reported values]\n")
    return S_star_ideal, S_star_5


# ===========================================================================
# ROW-LEVEL RESUMABLE K-SWEEP (E91 only)
# ===========================================================================
def done_k_values(out_csv):
    if not os.path.exists(out_csv):
        return None, set()
    with open(out_csv, newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return None, set()
    return rows[0], {int(r[1]) for r in rows[1:] if r and r[0] == "E91"}


def main():
    start = time.time()
    S_star_ideal, S_star_5 = calibrate()

    header, done = done_k_values(OUT_CSV)
    if header is None:
        with open(OUT_CSV, mode="w", newline="") as f:
            csv.writer(f).writerow(["Protocol", "K", "Trials", "FPR", "FNR"])

    print("==========================================")
    print(" E91 K-SWEEP UNDER CALIBRATED S*")
    print(f"  FPR: p_noise={P_NOISE_FPR} f=0  threshold S*_5%={S_star_5:.4f}")
    print(f"  FNR: p_noise={P_NOISE_FNR} f=1  threshold S*_ideal={S_star_ideal:.4f}")
    print("==========================================")

    for K in K_VALUES:
        if K in done:
            print(f"  K={K:<5} already done, skipping.")
            continue

        # FPR: 5% honest channel, f=0, evaluated against S*_5%.
        _, _, _, _, _, _, fpr_val, _ = base.monte_carlo_e91(
            TRIALS, K, p_noise=P_NOISE_FPR, f_eve=0.0, chsh_threshold=S_star_5,
            seed=8000 + K)
        # FNR: clean channel, full attack, evaluated against S*_ideal.
        _, _, _, _, _, _, _, fnr_val = base.monte_carlo_e91(
            TRIALS, K, p_noise=P_NOISE_FNR, f_eve=1.0, chsh_threshold=S_star_ideal,
            seed=9000 + K)

        print(f"  K={K:<5} | FPR: {fpr_val:.3f} | FNR: {fnr_val:.3f}")
        with open(OUT_CSV, mode="a", newline="") as f:
            csv.writer(f).writerow(["E91", K, TRIALS, fpr_val, fnr_val])

    print(f"\nDone. Wrote {OUT_CSV}. Elapsed {(time.time()-start)/60:.2f} min.")


if __name__ == "__main__":
    main()
