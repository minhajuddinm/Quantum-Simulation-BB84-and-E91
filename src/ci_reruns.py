"""
============================================================================
 TASK 2: HIGH-TRIAL CONFIDENCE-INTERVAL RERUNS WITH CONVERGENCE CHECKPOINTS
============================================================================
 Purpose
   Re-run the two headline sweeps at 200 Monte-Carlo trials (up from 50) for
   all three protocols, saving PER-TRIAL raw values (not just means) so the
   manuscript can put 95% confidence intervals on every figure and answer
   reviewer questions on convergence and reproducibility.

   Sweep (a) -- interception-fraction sweep, ideal channel (p_noise = 0):
       f = 0.0, 0.1, ..., 1.0 for BB84, six-state, E91.
       Per point we record the primary signal (QBER for BB84/six-state,
       CHSH S for E91), the secure key rate (SKR), and the detection
       outcome (FPR at f=0, FNR at f>0).

   Sweep (b) -- honest-channel FPR vs synthetic noise (f = 0):
       noise = 0, 2, 5, 8, 11% (p = 0.0, 0.04, 0.10, 0.16, 0.22) for all
       three protocols. Records the primary signal, SKR, and the
       false-positive indicator.

   For EVERY configuration we additionally:
     * dump one CSV row per trial (results/ci_pertrial_*.csv),
     * at trial counts 10, 25, 50, 100, 200 record the running mean and
       standard error of each headline metric (the convergence study,
       results/ci_convergence.csv),
     * compute a 95% t-distribution confidence interval for every mean
       (results/ci_summary_with_ci.csv),
   and finally run ONE Welch's t-test comparing six-state vs BB84 per-trial
   FNR (miss indicator) at f = 0.5 on the ideal channel, reporting the
   p-value (results/ci_welch_sixstate_vs_bb84_fnr_f050.csv + stdout).

 PHYSICS UNCHANGED. This script only orchestrates repeated calls to the
 existing per-trial functions in detection_aware_qkd_varying_eve.py
 (run_bb84_trial / run_six_state_trial / run_e91_trial) and the existing
 secure_key_rate. Detection thresholds:
     BB84  QBER >= 0.135
     Six-State QBER >= 0.167
     E91   S < S*_profile   (calibrated lookup, journal Table III),
           consistent with the S* migration in Task 1.

 Reproducibility: each trial is seeded independently as base_seed + trial
 index, so results are deterministic AND identical whether run serially or
 in parallel (--workers N). No global sweep-level RNG state is relied upon.

 Runtime: 200 trials x (11 f-points x 3 protocols + 5 noise-points x 3
 protocols) is dominated by the E91 8192-pair trials. Expect roughly
 2-4 hours single-core; use --workers <cpu count> to cut this to ~20-40 min.

 Run:
   python ci_reruns.py --workers 8
   python ci_reruns.py                 # serial
   python ci_reruns.py --workers 8 --sweep a    # only the f-sweep
============================================================================
"""

import argparse
import csv
import os
import time
import numpy as np

import detection_aware_qkd_varying_eve as base
import results_md

try:
    from scipy import stats as scipy_stats
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False


# ===========================================================================
# CONFIG
# ===========================================================================
TRIALS = 200
CHECKPOINTS = [10, 25, 50, 100, 200]

STD_QUBITS = 1000      # BB84 / six-state
E91_PAIRS = 8192       # E91

# Fraction of the sifted key spent on parameter estimation (its bits are
# publicly disclosed to estimate the error rate and therefore do NOT become
# key). The remaining n_key = n_sift - m bits are the raw key. This is the
# single source of truth for m; finite_key_skr.py (Task 4) reads m straight
# from the per-trial CSVs rather than re-deriving it.
PE_FRACTION = 0.5

BB84_TH = 0.135
SIX_TH = 0.167

# E91 calibrated thresholds S* per noise profile (journal Table III),
# consistent with Task 1 / the S* migration.
E91_STAR = {
    "Ideal_0%":      2.124,
    "Noise_2%":      1.945,
    "Noise_5%":      1.722,
    "Noise_8%":      1.499,
    "Threshold_11%": 1.293,
}

F_GRID = [round(0.1 * i, 1) for i in range(11)]      # 0.0 .. 1.0

# honest-channel FPR-vs-noise points: (profile, p_noise)
NOISE_POINTS = [
    ("Ideal_0%",      0.0),
    ("Noise_2%",      0.04),
    ("Noise_5%",      0.10),
    ("Noise_8%",      0.16),
    ("Threshold_11%", 0.22),
]

PROTOCOLS = ["BB84", "Six-State", "E91"]

RESULTS_DIR = "results"
PERTRIAL_A = os.path.join(RESULTS_DIR, "ci_pertrial_fsweep_ideal.csv")
PERTRIAL_B = os.path.join(RESULTS_DIR, "ci_pertrial_fpr_noise.csv")
CONVERGENCE = os.path.join(RESULTS_DIR, "ci_convergence.csv")
SUMMARY = os.path.join(RESULTS_DIR, "ci_summary_with_ci.csv")
WELCH = os.path.join(RESULTS_DIR, "ci_welch_sixstate_vs_bb84_fnr_f050.csv")


# ===========================================================================
# SINGLE-TRIAL WORKER  (top-level for multiprocessing picklability on Windows)
# ===========================================================================
def _finite_key_fields(N, sifted_alice, sifted_bob, qber):
    """Per-trial finite-key bookkeeping consumed by Task 4 (finite_key_skr.py).

    Returns (n_sift, m, n_key, Q, leak_EC):
        n_sift  = sifted key length
        m       = parameter-estimation sample size = round(PE_FRACTION * n_sift)
        n_key   = n_sift - m                (raw key bits kept)
        Q       = observed error rate (the PE sample is the same channel, so
                  the trial QBER / E91 key-basis error rate is the estimator)
        leak_EC = parity bits actually disclosed by the Cascade-style
                  error_reconciliation run on the n_key key bits (real
                  simulated leakage, NOT the analytic H2 bound). Pure classical
                  post-processing -- no Aer.
    """
    n_sift = len(sifted_alice)
    m = int(round(n_sift * PE_FRACTION))
    n_key = n_sift - m
    if n_key > 0:
        _, leak_EC = base.error_reconciliation(sifted_alice[m:], sifted_bob[m:])
    else:
        leak_EC = 0
    return n_sift, m, n_key, float(qber), int(leak_EC)


def _run_one_trial(spec):
    """
    spec = (proto, seed, num, p_noise, f_eve, e91_threshold)
    Returns a dict with:
        metric  = QBER (BB84/six-state) or CHSH S (E91)
        skr     = asymptotic secure key rate for this trial
        alarm   = 1 if the detector fired this trial, else 0
        N       = total transmitted qubits/pairs for this trial
        n_sift, m, n_key, Q, leak_EC  = finite-key fields (see _finite_key_fields)
    Detection semantics downstream: honest (f=0) alarm -> false positive;
    attack (f>0) NON-alarm -> false negative (miss).
    """
    proto, seed, num, p_noise, f_eve, e91_thr = spec
    np.random.seed(seed)

    if proto == "BB84":
        sifted_len, _errors, qber, sa, sb = base.run_bb84_trial(num, p_noise, f_eve)
        metric = qber
        alarm = 1 if qber >= BB84_TH else 0
    elif proto == "Six-State":
        sifted_len, _errors, qber, sa, sb = base.run_six_state_trial(num, p_noise, f_eve)
        metric = qber
        alarm = 1 if qber >= SIX_TH else 0
    else:  # E91
        S, sifted_len, _errors, qber, sa, sb = base.run_e91_trial(num, p_noise, f_eve)
        metric = S
        alarm = 1 if S < e91_thr else 0

    skr = base.secure_key_rate(num, sifted_len, qber)
    n_sift, m, n_key, Q, leak_EC = _finite_key_fields(num, sa, sb, qber)

    return {"metric": metric, "skr": skr, "alarm": alarm,
            "N": num, "n_sift": n_sift, "m": m, "n_key": n_key,
            "Q": Q, "leak_EC": leak_EC}


# ===========================================================================
# CONFIG RUNNER  (serial or parallel over the 200 trials)
# ===========================================================================
def run_config(proto, num, p_noise, f_eve, e91_thr, base_seed, pool):
    """Run TRIALS trials for one configuration; return a dict of per-trial arrays."""
    specs = [(proto, base_seed + t, num, p_noise, f_eve, e91_thr)
             for t in range(TRIALS)]
    if pool is None:
        results = [_run_one_trial(s) for s in specs]
    else:
        results = list(pool.map(_run_one_trial, specs))
    keys = ["metric", "skr", "alarm", "N", "n_sift", "m", "n_key", "Q", "leak_EC"]
    return {k: np.array([r[k] for r in results], dtype=float) for k in keys}


# ===========================================================================
# STATISTICS HELPERS
# ===========================================================================
def _t_crit(df, conf=0.95):
    """Two-sided t critical value; scipy if present, else a small fallback table."""
    if HAVE_SCIPY:
        return float(scipy_stats.t.ppf(0.5 + conf / 2.0, df))
    # fallback 97.5% t table (rarely hit; scipy is expected per task spec)
    table = {1: 12.706, 2: 4.303, 5: 2.571, 9: 2.262, 24: 2.064,
             49: 2.010, 99: 1.984, 199: 1.972}
    keys = sorted(table)
    for k in keys:
        if df <= k:
            return table[k]
    return 1.96


def mean_se_ci(values):
    """Return (mean, se, ci_low, ci_high) with a 95% t-distribution CI."""
    n = len(values)
    m = float(np.mean(values))
    if n < 2:
        return m, 0.0, m, m
    sd = float(np.std(values, ddof=1))
    se = sd / np.sqrt(n)
    tc = _t_crit(n - 1)
    return m, se, m - tc * se, m + tc * se


def running_checkpoints(values, metric_name, checkpoints):
    """running mean + SE at each checkpoint <= len(values)."""
    out = []
    for n in checkpoints:
        if n > len(values):
            continue
        m, se, _, _ = mean_se_ci(values[:n])
        out.append((metric_name, n, m, se))
    return out


# ===========================================================================
# CSV WRITERS
# ===========================================================================
def _init_csv(path, header):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(path, "w", newline="") as f:
        csv.writer(f).writerow(header)


def _append(path, row):
    with open(path, "a", newline="") as f:
        csv.writer(f).writerow(row)


# ===========================================================================
# SWEEP (a): f-sweep on the ideal channel
# ===========================================================================
def sweep_a(pool):
    print("\n" + "=" * 64)
    print(" SWEEP (a): interception-fraction sweep, ideal channel (200 trials)")
    print("=" * 64)
    _init_csv(PERTRIAL_A,
              ["Protocol", "Channel", "P_Noise", "F_Eve", "Trial",
               "Metric_Name", "Metric", "SKR", "Alarm", "Detection_Outcome",
               "N", "n_sift", "m", "n_key", "Q", "leak_EC"])

    # cache the f=0.5 miss-indicator arrays for the Welch test
    miss_f050 = {}

    for proto in PROTOCOLS:
        num = E91_PAIRS if proto == "E91" else STD_QUBITS
        e91_thr = E91_STAR["Ideal_0%"]      # ideal channel
        metric_name = "CHSH_S" if proto == "E91" else "QBER"
        print(f"\n-- {proto} (metric = {metric_name}, E91 threshold S*={e91_thr}) --")

        for f in F_GRID:
            base_seed = 20000 + PROTOCOLS.index(proto) * 5000 + int(round(f * 100))
            res = run_config(proto, num, 0.0, f, e91_thr, base_seed, pool)
            metric, skr, alarm = res["metric"], res["skr"], res["alarm"]

            # detection outcome per trial: honest -> FP indicator; attack -> miss indicator
            if f == 0.0:
                outcome = alarm                      # 1 = false positive
                outcome_name = "FP"
                det_rate = float(np.mean(alarm))     # FPR
                rate_name = "FPR"
            else:
                outcome = 1.0 - alarm                # 1 = missed attacker
                outcome_name = "FN"
                det_rate = float(np.mean(1.0 - alarm))  # FNR
                rate_name = "FNR"

            # per-trial rows (incl. finite-key fields consumed by Task 4)
            for t in range(TRIALS):
                _append(PERTRIAL_A,
                        [proto, "Ideal_0%", 0.0, f, t, metric_name,
                         metric[t], skr[t], int(alarm[t]), int(outcome[t]),
                         int(res["N"][t]), int(res["n_sift"][t]), int(res["m"][t]),
                         int(res["n_key"][t]), res["Q"][t], int(res["leak_EC"][t])])

            # convergence checkpoints (metric, SKR, detection rate)
            for mname, vals in [(metric_name, metric), ("SKR", skr), (rate_name, outcome)]:
                for cn, n, m, se in running_checkpoints(vals, mname, CHECKPOINTS):
                    _append(CONVERGENCE,
                            [proto, "sweep_a", "Ideal_0%", f"f={f}", cn, n, m, se])

            # CI summary
            for mname, vals in [(metric_name, metric), ("SKR", skr), (rate_name, outcome)]:
                m, se, lo, hi = mean_se_ci(vals)
                _append(SUMMARY,
                        [proto, "sweep_a", "Ideal_0%", f"f={f}", mname,
                         TRIALS, m, se, lo, hi])

            if abs(f - 0.5) < 1e-9:
                miss_f050[proto] = (1.0 - alarm)  # per-trial miss indicator at f=0.5

            print(f"    f={f:.1f} | {metric_name}={np.mean(metric):.4f} | "
                  f"SKR={np.mean(skr):.4f} | {rate_name}={det_rate:.3f}")

    return miss_f050


# ===========================================================================
# SWEEP (b): honest-channel FPR vs noise
# ===========================================================================
def sweep_b(pool):
    print("\n" + "=" * 64)
    print(" SWEEP (b): honest-channel FPR vs synthetic noise (200 trials)")
    print("=" * 64)
    _init_csv(PERTRIAL_B,
              ["Protocol", "Noise_Profile", "P_Noise", "F_Eve", "Trial",
               "Metric_Name", "Metric", "SKR", "Alarm_FP",
               "N", "n_sift", "m", "n_key", "Q", "leak_EC"])

    for proto in PROTOCOLS:
        num = E91_PAIRS if proto == "E91" else STD_QUBITS
        metric_name = "CHSH_S" if proto == "E91" else "QBER"
        print(f"\n-- {proto} (metric = {metric_name}) --")

        for profile, p_noise in NOISE_POINTS:
            e91_thr = E91_STAR[profile]     # per-profile S* for E91
            base_seed = 40000 + PROTOCOLS.index(proto) * 5000 + int(round(p_noise * 1000))
            res = run_config(proto, num, p_noise, 0.0, e91_thr, base_seed, pool)
            metric, skr, alarm = res["metric"], res["skr"], res["alarm"]

            fpr = float(np.mean(alarm))

            for t in range(TRIALS):
                _append(PERTRIAL_B,
                        [proto, profile, p_noise, 0.0, t, metric_name,
                         metric[t], skr[t], int(alarm[t]),
                         int(res["N"][t]), int(res["n_sift"][t]), int(res["m"][t]),
                         int(res["n_key"][t]), res["Q"][t], int(res["leak_EC"][t])])

            for mname, vals in [(metric_name, metric), ("SKR", skr), ("FPR", alarm)]:
                for cn, n, m, se in running_checkpoints(vals, mname, CHECKPOINTS):
                    _append(CONVERGENCE,
                            [proto, "sweep_b", profile, f"p={p_noise}", cn, n, m, se])

            for mname, vals in [(metric_name, metric), ("SKR", skr), ("FPR", alarm)]:
                m, se, lo, hi = mean_se_ci(vals)
                _append(SUMMARY,
                        [proto, "sweep_b", profile, f"p={p_noise}", mname,
                         TRIALS, m, se, lo, hi])

            print(f"    {profile:<14} (p={p_noise}) | {metric_name}={np.mean(metric):.4f} "
                  f"| SKR={np.mean(skr):.4f} | FPR={fpr:.3f}")


# ===========================================================================
# WELCH'S T-TEST: six-state vs BB84 FNR (miss indicator) at f = 0.5, ideal
# ===========================================================================
def welch_test(miss_f050):
    _init_csv(WELCH,
              ["Comparison", "F_Eve", "Channel", "N_per_group",
               "Mean_FNR_SixState", "Mean_FNR_BB84",
               "Welch_t", "dof", "p_value"])
    if "Six-State" not in miss_f050 or "BB84" not in miss_f050:
        print("\n[Welch] f=0.5 arrays unavailable (run sweep a); skipping.")
        return

    six = miss_f050["Six-State"]
    bb = miss_f050["BB84"]
    mean_six, mean_bb = float(np.mean(six)), float(np.mean(bb))

    if HAVE_SCIPY:
        res = scipy_stats.ttest_ind(six, bb, equal_var=False)
        t_stat, p_val = float(res.statistic), float(res.pvalue)
        # Welch-Satterthwaite dof
        v1, v2 = np.var(six, ddof=1), np.var(bb, ddof=1)
        n1, n2 = len(six), len(bb)
        num = (v1 / n1 + v2 / n2) ** 2
        den = (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)
        dof = float(num / den) if den > 0 else float("nan")
    else:
        v1, v2 = np.var(six, ddof=1), np.var(bb, ddof=1)
        n1, n2 = len(six), len(bb)
        se = np.sqrt(v1 / n1 + v2 / n2)
        t_stat = (mean_six - mean_bb) / se if se > 0 else float("nan")
        dof = float("nan")
        p_val = float("nan")
        print("[Welch] scipy not installed -- p-value unavailable; install scipy.")

    _append(WELCH,
            ["SixState_vs_BB84_FNR", 0.5, "Ideal_0%", TRIALS,
             mean_six, mean_bb, t_stat, dof, p_val])

    print("\n" + "=" * 64)
    print(" WELCH'S T-TEST: six-state vs BB84 per-trial FNR at f=0.5 (ideal)")
    print("=" * 64)
    print(f"  mean FNR six-state = {mean_six:.4f}")
    print(f"  mean FNR BB84      = {mean_bb:.4f}")
    print(f"  Welch t = {t_stat:.4f}   dof = {dof:.2f}   p-value = {p_val:.3e}")
    print("=" * 64)


# ===========================================================================
# results/results.md  -- Task 2 section
# ===========================================================================
def write_results_md():
    """Assemble the ## Task 2 section of results/results.md from the summary
    and Welch CSVs just written. Pure file I/O; safe to call after any run."""
    body = []
    body.append("Headline metrics with 95% t-distribution confidence intervals "
                "(200 trials/config). Full per-trial raw values, including the "
                "finite-key fields `N, n_sift, m, n_key, Q, leak_EC`, are in "
                "`ci_pertrial_fsweep_ideal.csv` and `ci_pertrial_fpr_noise.csv`; "
                "running mean/SE at 10/25/50/100/200 trials are in "
                "`ci_convergence.csv`.\n")

    # --- CI summary table (compact) ---
    if os.path.exists(SUMMARY):
        with open(SUMMARY, newline="") as f:
            rows = list(csv.DictReader(f))
        header = ["Protocol", "Sweep", "Config", "Metric", "Mean", "95% CI"]
        trows = []
        for r in rows:
            trows.append([
                r["Protocol"], r["Sweep"], r["Config_Point"], r["Metric_Name"],
                f'{float(r["Mean"]):.4f}',
                f'[{float(r["CI95_Low"]):.4f}, {float(r["CI95_High"]):.4f}]',
            ])
        body.append("### Mean and 95% CI per configuration\n")
        body.append(results_md.md_table(header, trows))

    # --- Welch test ---
    if os.path.exists(WELCH):
        with open(WELCH, newline="") as f:
            wrows = list(csv.DictReader(f))
        if wrows:
            w = wrows[-1]
            body.append("\n### Welch's t-test: six-state vs BB84 FNR at f = 0.5 (ideal channel)\n")
            body.append(
                f"- mean FNR six-state = {float(w['Mean_FNR_SixState']):.4f}, "
                f"mean FNR BB84 = {float(w['Mean_FNR_BB84']):.4f}\n"
                f"- Welch t = {float(w['Welch_t']):.4f}, dof = {float(w['dof']):.2f}, "
                f"p-value = {float(w['p_value']):.3e}"
            )

    results_md.update_section(
        2, "High-trial CI reruns, convergence, and Welch test", "\n".join(body))
    print(f"Wrote Task 2 section -> {results_md.RESULTS_MD}")


# ===========================================================================
# MAIN
# ===========================================================================
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workers", type=int, default=1,
                    help="Parallel worker processes over trials (default 1 = serial).")
    ap.add_argument("--sweep", choices=["a", "b", "both"], default="both",
                    help="Which sweep(s) to run (default both).")
    args = ap.parse_args()

    if not HAVE_SCIPY:
        print("[WARNING] scipy not found. CIs use a fallback t-table and the "
              "Welch p-value will be NaN. Install scipy for exact values:\n"
              "          pip install scipy\n")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    # (re)initialise the append-mode summary/convergence files once up front
    _init_csv(CONVERGENCE,
              ["Protocol", "Sweep", "Config_Profile", "Config_Point",
               "Metric_Name", "N_Trials", "Running_Mean", "Running_SE"])
    _init_csv(SUMMARY,
              ["Protocol", "Sweep", "Config_Profile", "Config_Point",
               "Metric_Name", "N", "Mean", "SE", "CI95_Low", "CI95_High"])

    start = time.time()
    pool = None
    if args.workers and args.workers > 1:
        from multiprocessing import Pool
        pool = Pool(processes=args.workers)
        print(f"Running with {args.workers} worker processes.")

    try:
        miss_f050 = {}
        if args.sweep in ("a", "both"):
            miss_f050 = sweep_a(pool)
        if args.sweep in ("b", "both"):
            sweep_b(pool)
        if args.sweep in ("a", "both"):
            welch_test(miss_f050)
    finally:
        if pool is not None:
            pool.close()
            pool.join()

    write_results_md()
    print(f"\nAll CSVs written to {RESULTS_DIR}/. Elapsed {(time.time()-start)/60:.2f} min.")


if __name__ == "__main__":
    main()
