"""
============================================================================
 TASK 4: FINITE-KEY SECURE KEY RATE (post-processing only -- NO simulation)
============================================================================
 Reads the per-trial CSVs produced by ci_reruns.py (Task 2) from results/ and
 computes, per trial and per configuration, a finite-key secure key rate next
 to the asymptotic value. No Qiskit / Aer is imported: this is pure arithmetic
 over the logged fields N, n_sift, m, n_key, Q, leak_EC.

 Methodology (Hoeffding-corrected parameter estimation; composable finite-key
 length a la Tomamichel et al., Nat. Commun. 3, 634 (2012), and the finite-key
 treatment of Scarani & Renner, PRL 100, 200501 (2008)):

   Inflate the estimated error rate by the statistical fluctuation
       mu   = sqrt( ln(1/eps_PE) / (2 m) )
   then the extractable secret-key length is
       ell  = n_key * (1 - 2 H2(min(Q + mu, 0.5)))
              - leak_EC
              - log2(2 / eps_sec)
              - log2(1 / eps_cor)
   with  n_key = n_sift - m,  and the finite-key rate is
       SKR_fk = max(0, ell) / N.

 leak_EC is the REAL number of parity bits disclosed by the simulated
 Cascade-style reconciliation on the n_key key bits (logged by ci_reruns.py),
 not the analytic H2 bound. The asymptotic reference rate is the same one the
 rest of the study reports,
       SKR_asy = (n_sift / N) * max(0, 1 - 2 H2(Q)).

 For E91 the treatment is identical: n_sift is the matched-axis key length and
 Q is the key-basis error rate (both logged per trial); the CHSH estimate S
 plays NO role in the key-length formula, only in detection (Task 1).

 Outputs (all in results/):
   (a) finite_key_summary.csv       per-config mean + 95% CI of finite-key SKR
                                    next to the mean asymptotic SKR.
   (b) finite_key_zero_crossing.csv per protocol, the block size N at which the
                                    finite-key SKR first exceeds zero on the
                                    honest ideal channel and at f = 0.1,
                                    obtained by scaling the formula analytically
                                    over N in [1e2, 1e6] at the observed Q
                                    (pure arithmetic, no simulation).
   (c) results/results.md           the finite-key numbers at the standard
                                    operating points (N = 1000 for BB84/six-
                                    state, N = 8192 pairs for E91; honest and
                                    f = 0.1) appended as section "## Task 4".

 Run:
   python finite_key_skr.py
============================================================================
"""

import csv
import math
import os

import numpy as np

import results_md

try:
    from scipy import stats as scipy_stats
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False


# ===========================================================================
# CONFIG  (security parameters -- edit here)
# ===========================================================================
EPS_PE = 1e-10     # parameter-estimation failure probability
EPS_SEC = 1e-10    # secrecy parameter
EPS_COR = 1e-10    # correctness parameter

RESULTS_DIR = "results"
PERTRIAL_A = os.path.join(RESULTS_DIR, "ci_pertrial_fsweep_ideal.csv")
PERTRIAL_B = os.path.join(RESULTS_DIR, "ci_pertrial_fpr_noise.csv")

SUMMARY_CSV = os.path.join(RESULTS_DIR, "finite_key_summary.csv")
CROSSING_CSV = os.path.join(RESULTS_DIR, "finite_key_zero_crossing.csv")

# Standard operating points reported in section ## Task 4.
STD_N = {"BB84": 1000, "Six-State": 1000, "E91": 8192}


# ===========================================================================
# CORE FORMULAE
# ===========================================================================
def H2(q):
    """Binary entropy in bits."""
    if q <= 0.0 or q >= 1.0:
        return 0.0
    return -q * math.log2(q) - (1 - q) * math.log2(1 - q)


def finite_key_length(n_sift, m, n_key, Q, leak_EC,
                      eps_pe=EPS_PE, eps_sec=EPS_SEC, eps_cor=EPS_COR):
    """Extractable secret-key length ell (bits); may be negative."""
    if m <= 0 or n_key <= 0:
        return 0.0
    mu = math.sqrt(math.log(1.0 / eps_pe) / (2.0 * m))
    Q_hat = min(Q + mu, 0.5)
    ell = (n_key * (1.0 - 2.0 * H2(Q_hat))
           - leak_EC
           - math.log2(2.0 / eps_sec)
           - math.log2(1.0 / eps_cor))
    return ell


def finite_key_skr(N, n_sift, m, n_key, Q, leak_EC):
    ell = finite_key_length(n_sift, m, n_key, Q, leak_EC)
    return max(0.0, ell) / N if N > 0 else 0.0


def asymptotic_skr(N, n_sift, Q):
    if N <= 0:
        return 0.0
    return (n_sift / N) * max(0.0, 1.0 - 2.0 * H2(Q))


# ===========================================================================
# STATISTICS
# ===========================================================================
def _t_crit(df, conf=0.95):
    if HAVE_SCIPY and df >= 1:
        return float(scipy_stats.t.ppf(0.5 + conf / 2.0, df))
    table = {1: 12.706, 2: 4.303, 5: 2.571, 9: 2.262, 24: 2.064,
             49: 2.010, 99: 1.984, 199: 1.972}
    for k in sorted(table):
        if df <= k:
            return table[k]
    return 1.96


def mean_ci(values):
    v = np.asarray(values, dtype=float)
    n = len(v)
    m = float(np.mean(v)) if n else 0.0
    if n < 2:
        return m, m, m
    se = float(np.std(v, ddof=1)) / math.sqrt(n)
    tc = _t_crit(n - 1)
    return m, m - tc * se, m + tc * se


# ===========================================================================
# INPUT
# ===========================================================================
def _load(path, channel_col):
    """Load a per-trial CSV; normalise the channel column name to 'Config'."""
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        try:
            rec = {
                "Protocol": r["Protocol"],
                "Config": r[channel_col],
                "P_Noise": float(r["P_Noise"]),
                "F_Eve": float(r["F_Eve"]),
                "N": float(r["N"]),
                "n_sift": float(r["n_sift"]),
                "m": float(r["m"]),
                "n_key": float(r["n_key"]),
                "Q": float(r["Q"]),
                "leak_EC": float(r["leak_EC"]),
                "source": os.path.basename(path),
            }
        except KeyError as e:
            raise SystemExit(
                f"\n[ERROR] {path} is missing column {e}. This file predates the "
                "Task 2 update. Re-run ci_reruns.py so the per-trial CSVs include "
                "N, n_sift, m, n_key, Q, leak_EC, then re-run finite_key_skr.py.\n")
        out.append(rec)
    return out


def load_all():
    rows = _load(PERTRIAL_A, "Channel") + _load(PERTRIAL_B, "Noise_Profile")
    if not rows:
        raise SystemExit(
            f"\n[ERROR] No per-trial CSVs found in {RESULTS_DIR}/. Run "
            "ci_reruns.py (Task 2) first.\n")
    return rows


def group_by_config(rows):
    """Return {(Protocol, Config, P_Noise, F_Eve, source): [rows]}."""
    groups = {}
    for r in rows:
        key = (r["Protocol"], r["Config"], r["P_Noise"], r["F_Eve"], r["source"])
        groups.setdefault(key, []).append(r)
    return groups


# ===========================================================================
# (a) PER-CONFIG SUMMARY
# ===========================================================================
def write_summary(groups):
    header = ["Protocol", "Config", "P_Noise", "F_Eve", "Source", "N_trials",
              "Mean_N", "Mean_n_sift", "Mean_m", "Mean_Q", "Mean_leak_EC",
              "Mean_SKR_finite", "CI95_Low_finite", "CI95_High_finite",
              "Mean_SKR_asymptotic"]
    out_rows = []
    for key in sorted(groups):
        proto, config, p_noise, f_eve, source = key
        trials = groups[key]
        fk = [finite_key_skr(r["N"], r["n_sift"], r["m"], r["n_key"],
                             r["Q"], r["leak_EC"]) for r in trials]
        asy = [asymptotic_skr(r["N"], r["n_sift"], r["Q"]) for r in trials]
        m_fk, lo, hi = mean_ci(fk)
        out_rows.append([
            proto, config, p_noise, f_eve, source, len(trials),
            f'{np.mean([r["N"] for r in trials]):.1f}',
            f'{np.mean([r["n_sift"] for r in trials]):.1f}',
            f'{np.mean([r["m"] for r in trials]):.1f}',
            f'{np.mean([r["Q"] for r in trials]):.6f}',
            f'{np.mean([r["leak_EC"] for r in trials]):.1f}',
            f'{m_fk:.8f}', f'{lo:.8f}', f'{hi:.8f}',
            f'{np.mean(asy):.8f}',
        ])
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(SUMMARY_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(out_rows)
    print(f"Wrote {SUMMARY_CSV}  ({len(out_rows)} configurations)")
    return out_rows


# ===========================================================================
# (b) ANALYTIC ZERO-CROSSING OF FINITE-KEY SKR OVER BLOCK SIZE N
# ===========================================================================
def _config_shape(groups, proto, f_eve):
    """Observed (sifting ratio r, PE fraction pe, Q, leak-per-key-bit) for the
    ideal-channel config of `proto` at interception fraction `f_eve`, taken
    from the sweep-a (ci_pertrial_fsweep_ideal.csv) rows."""
    key = (proto, "Ideal_0%", 0.0, f_eve, "ci_pertrial_fsweep_ideal.csv")
    if key not in groups:
        return None
    trials = groups[key]
    mean_N = np.mean([r["N"] for r in trials])
    mean_nsift = np.mean([r["n_sift"] for r in trials])
    mean_m = np.mean([r["m"] for r in trials])
    mean_nkey = np.mean([r["n_key"] for r in trials])
    mean_Q = np.mean([r["Q"] for r in trials])
    mean_leak = np.mean([r["leak_EC"] for r in trials])
    r = mean_nsift / mean_N if mean_N else 0.0
    pe = mean_m / mean_nsift if mean_nsift else 0.0
    leak_rate = mean_leak / mean_nkey if mean_nkey else 0.0
    return {"r": r, "pe": pe, "Q": float(mean_Q), "leak_rate": leak_rate}


def _crossing_N(shape, n_min=100, n_max=1_000_000, points=4000):
    """Smallest N in [n_min, n_max] where the scaled finite-key SKR > 0, using
    the observed shape (sifting ratio, PE fraction, Q, per-bit leakage). Pure
    arithmetic -- nothing simulated."""
    if shape is None or shape["r"] <= 0:
        return None
    grid = np.unique(np.round(
        np.logspace(math.log10(n_min), math.log10(n_max), points)).astype(int))
    for N in grid:
        n_sift = shape["r"] * N
        m = shape["pe"] * n_sift
        n_key = n_sift - m
        leak_EC = shape["leak_rate"] * n_key
        ell = finite_key_length(n_sift, m, n_key, shape["Q"], leak_EC)
        if ell > 0:
            return int(N)
    return None


def write_crossing(groups):
    header = ["Protocol", "Channel", "F_Eve", "Observed_Q", "Sifting_ratio",
              "PE_fraction", "Leak_per_keybit", "N_finite_key_SKR_first_positive"]
    out_rows = []
    for proto in ["BB84", "Six-State", "E91"]:
        for f_eve in (0.0, 0.1):
            shape = _config_shape(groups, proto, f_eve)
            Ncross = _crossing_N(shape)
            if shape is None:
                out_rows.append([proto, "Ideal_0%", f_eve, "n/a", "n/a",
                                 "n/a", "n/a", "config not found"])
            else:
                out_rows.append([
                    proto, "Ideal_0%", f_eve,
                    f'{shape["Q"]:.6f}', f'{shape["r"]:.4f}', f'{shape["pe"]:.4f}',
                    f'{shape["leak_rate"]:.4f}',
                    Ncross if Ncross is not None else ">1e6"])
    with open(CROSSING_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(out_rows)
    print(f"Wrote {CROSSING_CSV}  ({len(out_rows)} rows)")
    return out_rows


# ===========================================================================
# (c) results/results.md  -- Task 4 section (standard operating points)
# ===========================================================================
def write_results_md(groups, crossing_rows):
    body = []
    body.append(
        "Finite-key secure key rate (Hoeffding-corrected parameter estimation, "
        f"eps_PE = eps_sec = eps_cor = {EPS_PE:g}) next to the asymptotic value, "
        "at the standard operating points. Per-configuration means and 95% CIs "
        "are in `finite_key_summary.csv`; the block-size zero crossings are in "
        "`finite_key_zero_crossing.csv`.\n")

    # --- standard operating points table ---
    header = ["Protocol", "N", "F_Eve", "Mean_Q", "Mean_SKR_finite",
              "95% CI (finite)", "Mean_SKR_asymptotic"]
    trows = []
    for proto in ["BB84", "Six-State", "E91"]:
        for f_eve in (0.0, 0.1):
            key = (proto, "Ideal_0%", 0.0, f_eve, "ci_pertrial_fsweep_ideal.csv")
            if key not in groups:
                trows.append([proto, STD_N[proto], f_eve, "n/a", "n/a", "n/a", "n/a"])
                continue
            trials = groups[key]
            fk = [finite_key_skr(r["N"], r["n_sift"], r["m"], r["n_key"],
                                 r["Q"], r["leak_EC"]) for r in trials]
            asy = [asymptotic_skr(r["N"], r["n_sift"], r["Q"]) for r in trials]
            m_fk, lo, hi = mean_ci(fk)
            trows.append([
                proto, STD_N[proto], f_eve,
                f'{np.mean([r["Q"] for r in trials]):.5f}',
                f'{m_fk:.8f}', f'[{lo:.8f}, {hi:.8f}]',
                f'{np.mean(asy):.6f}'])
    body.append("### Finite-key vs asymptotic SKR at standard operating points\n")
    body.append(results_md.md_table(header, trows))

    # --- zero-crossing table ---
    body.append("\n### Block size N at which finite-key SKR first exceeds zero "
                "(analytic scaling at observed Q)\n")
    ch_header = ["Protocol", "Channel", "F_Eve", "Observed_Q",
                 "N (finite-key SKR > 0)"]
    ch_rows = [[r[0], r[1], r[2], r[3], r[7]] for r in crossing_rows]
    body.append(results_md.md_table(ch_header, ch_rows))
    body.append("\n_Note: at N = 1000 (BB84/six-state) and N = 8192 pairs (E91) "
                "the statistical fluctuation term mu dominates, so the finite-key "
                "SKR is 0 at the standard operating points; it turns positive only "
                "at the larger block sizes in the crossing table._")

    results_md.update_section(
        4, "Finite-key secure key rate", "\n".join(body))
    print(f"Wrote Task 4 section -> {results_md.RESULTS_MD}")


# ===========================================================================
# MAIN
# ===========================================================================
def main():
    if not HAVE_SCIPY:
        print("[WARNING] scipy not found; 95% CIs use a fallback t-table.\n")
    rows = load_all()
    groups = group_by_config(rows)
    print(f"Loaded {len(rows)} per-trial rows across {len(groups)} configurations.\n")

    write_summary(groups)
    crossing_rows = write_crossing(groups)
    write_results_md(groups, crossing_rows)
    print("\nTask 4 complete.")


if __name__ == "__main__":
    main()
