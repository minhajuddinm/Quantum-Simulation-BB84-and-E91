"""
============================================================================
 TASK 1: E91 RESOURCE COST (K-SWEEP) AND SKR UNDER THE CALIBRATED THRESHOLD S*
============================================================================
 Purpose
   Re-run the E91 sample-size (K) sweep and the E91 secure-key-rate (SKR)
   operating points, replacing the OLD fixed alarm rule (S < 2.0) with a
   PER-NOISE-PROFILE calibrated threshold S* looked up from a table
   (journal manuscript Table III):

       Ideal 0%       ->  S* = 2.124
       Noise 2%       ->  S* = 1.945
       Noise 5%       ->  S* = 1.722
       Noise 8%       ->  S* = 1.499
       Threshold 11%  ->  S* = 1.293
       IBM Marrakesh  ->  S* = 2.048

   The old fixed S = 2.0 rule is kept behind the --no-fixed / --fixed-only
   flags so the two thresholds can be read off side by side. By default the
   script computes BOTH so you can compare directly.

   What it produces (all in results/):
     (a) FPR vs K and FNR vs K on the SAME K grid as the original
         resource-cost experiment (detection_aware_qkd_sample_size.py):
            - FPR on the 5% honest channel (p_noise = 0.10, f = 0)
            - FPR on the 11% honest channel (p_noise = 0.22, f = 0)
            - FNR against a full attacker (f = 1) on a clean channel
              (p_noise = 0.0)
         -> results/qkd_e91_resource_cost_sstar.csv
     (b) E91 SKR at the standard operating points (honest f=0 and full
         attack f=1 for every synthetic noise profile, at 8192 pairs).
         SKR is threshold-INDEPENDENT (it is a function of QBER + sifting
         only, see secure_key_rate), so it is computed once per point and
         is identical under S* and under the fixed rule.
         -> results/qkd_e91_skr_operating_points.csv

   At the end the script prints, for each mode and channel, the smallest
   swept K at which FPR first falls <= 5% (plus a linear-interpolated
   crossing), so you can read the new S* value next to the old fixed value
   (~700 on the 5% channel).

 PHYSICS / PROTOCOL LOGIC IS UNCHANGED. This script only chooses which
 CHSH threshold value is passed into the (already threshold-parameterized)
 detector base.monte_carlo_e91(..., chsh_threshold=...). BB84 and six-state
 are NOT touched.

 The script is row-level resumable: interrupt it and re-run, and it skips
 (mode, curve, channel, K) rows already present in the output CSV.

 Run:
   python e91_resource_cost_sstar.py                 # S* and fixed-2.0
   python e91_resource_cost_sstar.py --no-fixed      # S* only
   python e91_resource_cost_sstar.py --fixed-only    # old fixed-2.0 only
   python e91_resource_cost_sstar.py --skip-skr      # K-sweep only (skip (b))
============================================================================
"""

import argparse
import csv
import os
import time
import numpy as np

import detection_aware_qkd_varying_eve as base
import results_md


# ===========================================================================
# CONFIG
# ===========================================================================
# Per-noise-profile calibrated thresholds S* (journal Table III). This is the
# "threshold lookup" that replaces the fixed S < 2.0 alarm.
S_STAR = {
    "Ideal_0%":      2.124,
    "Noise_2%":      1.945,
    "Noise_5%":      1.722,
    "Noise_8%":      1.499,
    "Threshold_11%": 1.293,
    "IBM_Marrakesh": 2.048,
}
FIXED_THRESHOLD = 2.0   # old classical-bound rule, kept behind a flag

# Synthetic depolarizing strengths per profile (verified, do NOT re-tune):
#   p = 0.04 -> ~1.84% QBER, p = 0.10 -> ~5.29%, p = 0.22 -> ~10.92%.
P_NOISE = {
    "Ideal_0%":      0.0,
    "Noise_2%":      0.04,
    "Noise_5%":      0.10,
    "Noise_8%":      0.16,
    "Threshold_11%": 0.22,
}

# Same K grid as the original resource-cost experiment.
K_VALUES = [100, 200, 300, 500, 1000, 2000, 3000]
TRIALS = 200

# SKR operating points: standard scale used everywhere else for E91.
SKR_PAIRS = 8192
SKR_TRIALS = 50            # matches the published synthetic-sweep trial count
SKR_PROFILES = ["Ideal_0%", "Noise_2%", "Noise_5%", "Noise_8%", "Threshold_11%"]
SKR_FRACTIONS = [0.0, 1.0]  # honest operating point and full-attack operating point

RESULTS_DIR = "results"
RC_CSV = os.path.join(RESULTS_DIR, "qkd_e91_resource_cost_sstar.csv")
SKR_CSV = os.path.join(RESULTS_DIR, "qkd_e91_skr_operating_points.csv")


# ===========================================================================
# THRESHOLD LOOKUP
# ===========================================================================
def e91_threshold(profile, use_fixed):
    """Per-noise-profile S* lookup, or the fixed classical bound behind the flag."""
    return FIXED_THRESHOLD if use_fixed else S_STAR[profile]


# The three K-sweep curves, as (curve, profile-used-for-threshold, p_noise, f_eve).
# 'profile' names which S* row the threshold comes from for that channel.
CURVES = [
    ("FPR", "Noise_5%",      P_NOISE["Noise_5%"],      0.0),   # 5% honest channel
    ("FPR", "Threshold_11%", P_NOISE["Threshold_11%"], 0.0),   # 11% honest channel
    ("FNR", "Ideal_0%",      P_NOISE["Ideal_0%"],      1.0),   # clean channel, full attack
]


# ===========================================================================
# RESUMABLE CSV HELPERS
# ===========================================================================
def _existing_rc_keys():
    """Set of (Threshold_Mode, Curve, Channel, K) already written."""
    if not os.path.exists(RC_CSV):
        return None, set()
    with open(RC_CSV, newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return None, set()
    header = rows[0]
    done = {(r[0], r[1], r[2], int(r[6])) for r in rows[1:] if len(r) >= 7}
    return header, done


def _existing_skr_keys():
    if not os.path.exists(SKR_CSV):
        return None, set()
    with open(SKR_CSV, newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return None, set()
    header = rows[0]
    done = {(r[0], float(r[2])) for r in rows[1:] if len(r) >= 3}  # (profile, f_eve)
    return header, done


# ===========================================================================
# (a) K-SWEEP: FPR vs K (5% and 11%) and FNR vs K (clean, full attack)
# ===========================================================================
def run_k_sweep(modes):
    header, done = _existing_rc_keys()
    if header is None:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        with open(RC_CSV, "w", newline="") as f:
            csv.writer(f).writerow(
                ["Threshold_Mode", "Curve", "Channel", "P_Noise", "F_Eve",
                 "Threshold_Value", "K", "Trials", "Rate"])
        done = set()

    for mode in modes:                      # "Sstar" or "Fixed2.0"
        use_fixed = (mode == "Fixed2.0")
        print(f"\n========== K-SWEEP | threshold mode: {mode} ==========")
        for curve, profile, p_noise, f_eve in CURVES:
            thr = e91_threshold(profile, use_fixed)
            channel = f"{profile}(p={p_noise})"
            print(f"  {curve} on {channel}  ->  threshold = {thr:.4f}")
            for K in K_VALUES:
                if (mode, curve, channel, K) in done:
                    print(f"    K={K:<5} already done, skipping.")
                    continue

                # distinct, reproducible seeds per (mode, curve, K)
                mode_off = 0 if not use_fixed else 100000
                curve_off = {"FPR": 8000, "FNR": 9000}[curve]
                prof_off = {"Noise_5%": 0, "Threshold_11%": 10000, "Ideal_0%": 0}[profile]
                seed = mode_off + curve_off + prof_off + K

                (_, _, _, _, _, _, fpr_val, fnr_val) = base.monte_carlo_e91(
                    TRIALS, K, p_noise=p_noise, f_eve=f_eve,
                    chsh_threshold=thr, seed=seed)
                rate = fpr_val if curve == "FPR" else fnr_val

                print(f"    K={K:<5} | {curve}: {rate:.3f}")
                with open(RC_CSV, "a", newline="") as f:
                    csv.writer(f).writerow(
                        [mode, curve, channel, p_noise, f_eve, thr, K, TRIALS, rate])
    print(f"\nWrote K-sweep -> {RC_CSV}")


# ===========================================================================
# (b) E91 SKR AT THE STANDARD OPERATING POINTS (threshold-independent)
# ===========================================================================
def run_skr_points():
    header, done = _existing_skr_keys()
    if header is None:
        os.makedirs(RESULTS_DIR, exist_ok=True)
        with open(SKR_CSV, "w", newline="") as f:
            csv.writer(f).writerow(
                ["Noise_Profile", "P_Noise", "F_Eve", "Pairs", "Trials",
                 "Mean_SKR", "Std_SKR", "Mean_S", "Std_S"])
        done = set()

    print("\n========== E91 SKR OPERATING POINTS (8192 pairs) ==========")
    print("  (SKR is threshold-independent: identical under S* and fixed 2.0)")
    for pi, profile in enumerate(SKR_PROFILES):
        p_noise = P_NOISE[profile]
        for f_eve in SKR_FRACTIONS:
            if (profile, f_eve) in done:
                print(f"  {profile:<14} f={f_eve} already done, skipping.")
                continue
            # deterministic seed (no Python hash randomization)
            seed = 3000 + pi * 10 + int(round(f_eve))
            (ms, ss, _, _, mskr, sskr, _, _) = base.monte_carlo_e91(
                SKR_TRIALS, SKR_PAIRS, p_noise=p_noise, f_eve=f_eve,
                chsh_threshold=S_STAR[profile], seed=seed)
            print(f"  {profile:<14} f={f_eve} | S={ms:.4f} | SKR={mskr:.4f} (+/-{sskr:.4f})")
            with open(SKR_CSV, "a", newline="") as f:
                csv.writer(f).writerow(
                    [profile, p_noise, f_eve, SKR_PAIRS, SKR_TRIALS, mskr, sskr, ms, ss])
    print(f"\nWrote SKR operating points -> {SKR_CSV}")


# ===========================================================================
# REPORTING: K at which FPR first falls <= 5%, S* vs fixed side by side
# ===========================================================================
def report_fpr_crossings():
    if not os.path.exists(RC_CSV):
        return
    with open(RC_CSV, newline="") as f:
        rows = list(csv.DictReader(f))

    print("\n" + "=" * 64)
    print(" K AT WHICH E91 FPR FIRST FALLS <= 5%  (read S* next to fixed 2.0)")
    print("=" * 64)
    # group FPR rows by (mode, channel)
    groups = {}
    for r in rows:
        if r["Curve"] != "FPR":
            continue
        key = (r["Threshold_Mode"], r["Channel"], r["Threshold_Value"])
        groups.setdefault(key, []).append((int(r["K"]), float(r["Rate"])))

    for (mode, channel, thr), pts in sorted(groups.items()):
        pts.sort()
        K = np.array([k for k, _ in pts])
        fpr = np.array([v for _, v in pts])
        below = K[fpr <= 0.05]
        k_step = int(below.min()) if len(below) else None
        k_interp = None
        for i in range(len(K) - 1):
            if fpr[i] > 0.05 >= fpr[i + 1]:
                frac = (fpr[i] - 0.05) / (fpr[i] - fpr[i + 1])
                k_interp = float(K[i] + frac * (K[i + 1] - K[i]))
                break
        interp_str = f"{k_interp:.0f}" if k_interp is not None else "n/a"
        curve_str = "  ".join(f"K={k}:{v:.3f}" for k, v in pts)
        print(f"\n  mode={mode}  channel={channel}  threshold={thr}")
        print(f"    {curve_str}")
        print(f"    -> first swept K with FPR<=5% = {k_step}  (interp ~ K={interp_str})")
    print("=" * 64)


# ===========================================================================
# results/results.md  -- Task 1 section
# ===========================================================================
def write_results_md():
    """Assemble the ## Task 1 section from the K-sweep and SKR CSVs."""
    body = []

    # --- FPR/FNR vs K, S* next to fixed 2.0 ---
    if os.path.exists(RC_CSV):
        with open(RC_CSV, newline="") as f:
            rows = list(csv.DictReader(f))
        # pivot: one row per (Curve, Channel, K) with a column per mode
        modes = sorted({r["Threshold_Mode"] for r in rows})
        keys = sorted({(r["Curve"], r["Channel"], int(r["K"])) for r in rows},
                      key=lambda t: (t[0], t[1], t[2]))
        lut = {(r["Threshold_Mode"], r["Curve"], r["Channel"], int(r["K"])):
               float(r["Rate"]) for r in rows}
        header = ["Curve", "Channel", "K"] + [f"{m} rate" for m in modes]
        trows = []
        for curve, channel, K in keys:
            trows.append([curve, channel, K] +
                         [f'{lut.get((m, curve, channel, K), float("nan")):.3f}'
                          for m in modes])
        body.append("### FPR-vs-K and FNR-vs-K (calibrated S* vs old fixed S=2.0)\n")
        body.append(results_md.md_table(header, trows))

        # crossings: smallest K with FPR <= 5%
        body.append("\n### Smallest swept K with FPR <= 5% (read S* next to fixed 2.0)\n")
        cross_rows = []
        groups = {}
        for r in rows:
            if r["Curve"] != "FPR":
                continue
            groups.setdefault((r["Threshold_Mode"], r["Channel"]), []).append(
                (int(r["K"]), float(r["Rate"])))
        for (mode, channel), pts in sorted(groups.items()):
            pts.sort()
            below = [k for k, v in pts if v <= 0.05]
            cross_rows.append([mode, channel,
                               below[0] if below else "none in grid"])
        body.append(results_md.md_table(["Threshold_Mode", "Channel",
                                         "First K with FPR<=5%"], cross_rows))

    # --- SKR operating points ---
    if os.path.exists(SKR_CSV):
        with open(SKR_CSV, newline="") as f:
            srows = list(csv.DictReader(f))
        header = ["Noise_Profile", "F_Eve", "Mean_S", "Mean_SKR", "Std_SKR"]
        trows = [[r["Noise_Profile"], r["F_Eve"],
                  f'{float(r["Mean_S"]):.4f}', f'{float(r["Mean_SKR"]):.4f}',
                  f'{float(r["Std_SKR"]):.4f}'] for r in srows]
        body.append("\n### E91 SKR at standard operating points (8192 pairs, threshold-independent)\n")
        body.append(results_md.md_table(header, trows))

    results_md.update_section(
        1, "E91 resource cost and SKR under the calibrated threshold S*",
        "\n".join(body))
    print(f"Wrote Task 1 section -> {results_md.RESULTS_MD}")


# ===========================================================================
# MAIN
# ===========================================================================
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-fixed", action="store_true",
                    help="Run only the calibrated S* threshold (skip fixed 2.0 baseline).")
    ap.add_argument("--fixed-only", action="store_true",
                    help="Run only the old fixed S=2.0 baseline (skip S*).")
    ap.add_argument("--skip-skr", action="store_true",
                    help="Skip the SKR operating-point computation (part b).")
    args = ap.parse_args()

    if args.fixed_only:
        modes = ["Fixed2.0"]
    elif args.no_fixed:
        modes = ["Sstar"]
    else:
        modes = ["Sstar", "Fixed2.0"]

    start = time.time()
    os.makedirs(RESULTS_DIR, exist_ok=True)

    run_k_sweep(modes)
    if not args.skip_skr:
        run_skr_points()

    report_fpr_crossings()
    write_results_md()
    print(f"\nDone. Elapsed {(time.time()-start)/60:.2f} min.")


if __name__ == "__main__":
    main()
