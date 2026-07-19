"""
============================================================================
 SCRIPT: PRIORITY 1 - NOISE-CALIBRATED CHSH DETECTION THRESHOLD FOR E91
============================================================================
 Purpose
   Replace the fixed classical-bound threshold (S < 2.0) used to declare an
   eavesdropper in E91 with a threshold S* that is calibrated, per noise
   profile, to balance the false positive rate and false negative rate --
   the same Hoeffding-balancing principle already used for the BB84/six-
   state QBER thresholds (Lee et al., Fiorini et al.), extended to the
   four-correlator CHSH estimator.

 What this script does
   1. Calibrates S* = (S_H_hat + S_f1_hat) / 2 per noise profile, using
      calibration trials that are INDEPENDENT of (not reused for) the
      evaluation sweep below -- mirroring a real deployment's out-of-band
      channel characterization step, not live inference from the same
      data being tested for an eavesdropper.
   2. Reruns the FPR/FNR sweep over the attack fraction f using the
      calibrated S*, at the SAME scale as the existing official sweep
      for each profile, directly comparable to qkd_varying_eve.csv.
   3. Runs a mis-calibration robustness check on the synthetic noise
      ladder: calibrate S* assuming one noise profile, then evaluate
      FPR/FNR under a NEIGHBORING noise profile (simulating channel
      drift between calibration cycles). IBM_Marrakesh is excluded from
      this specific check -- it's a real device noise model, not a point
      on a clean depolarizing-strength ladder, so "neighboring profile"
      isn't a well-defined comparison for it the way it is for the
      synthetic profiles.

 This script is resumable at the (profile, f-value) row level: if
 interrupted, re-running it picks up exactly where it left off, reusing
 the threshold already calibrated for any profile that's in progress
 rather than recalibrating it.

 Output files
   qkd_e91_calibrated.csv        Per-profile S*, calibration stats, and the
                                  full FPR/FNR-vs-f sweep under S*.
   qkd_e91_miscalibration.csv    FPR/FNR when S* is calibrated at one noise
                                  profile but evaluated at a neighboring one
                                  (synthetic profiles only).
============================================================================
"""

import csv
import os
import time
import numpy as np

import detection_aware_qkd_varying_eve as base


# ===========================================================================
# IBM QUANTUM ACCESS (only needed for the IBM_Marrakesh hardware-noise profile)
# ===========================================================================
# Paste your IBM Quantum API token below to fetch the ibm_marrakesh noise
# model directly. Get a token from your account at
# https://quantum.cloud.ibm.com/ (Account settings -> API token).
#
# SECURITY: this file may be version-controlled. Do not commit it with a
# real token pasted in -- clear this line again before committing, or
# better, set it from an environment variable instead:
#   IBM_API_TOKEN = os.environ.get("IBM_QUANTUM_TOKEN", "")
#
# If left blank, the script falls back to a locally saved account
# (QiskitRuntimeService.save_account(...), as already set up per the
# project README) and otherwise skips the IBM_Marrakesh profile.
IBM_API_TOKEN = "gEI5V5g3lPGsXJrFlR8Xrxf-uBfz39Pj3g4J_JOZoBO2"   # <-- paste your token between the quotes


def get_ibm_marrakesh_noise_model():
    """
    Connects to IBM Quantum and extracts the ibm_marrakesh noise model.
    Returns None (with a warning, not a crash) if no connection can be
    made, so the rest of the script still runs on the synthetic profiles.
    """
    from qiskit_ibm_runtime import QiskitRuntimeService
    from qiskit_aer.noise import NoiseModel
    try:
        if IBM_API_TOKEN:
            service = QiskitRuntimeService(channel="ibm_quantum_platform", token=IBM_API_TOKEN)
        else:
            service = QiskitRuntimeService(channel="ibm_quantum_platform")
        backend = service.backend("ibm_marrakesh")
        model = NoiseModel.from_backend(backend)
        print("Connected to ibm_marrakesh. Noise model extracted successfully.")
        return model
    except Exception as e:
        print(f"[WARNING] Could not fetch the ibm_marrakesh noise model ({e}). "
              f"Skipping the IBM_Marrakesh profile this run -- the synthetic "
              f"profiles below are unaffected.")
        return None


# ===========================================================================
# SECTION 1: CALIBRATION
# ===========================================================================
def calibrate_e91_threshold(num_pairs, p_noise, model=None, calib_trials=30, seed=None):
    if seed is not None:
        np.random.seed(seed)

    S_H_list = [base.run_e91_trial(num_pairs, p_noise, 0.0, model)[0] for _ in range(calib_trials)]
    S_H_hat, S_H_std = float(np.mean(S_H_list)), float(np.std(S_H_list))

    S_f1_list = [base.run_e91_trial(num_pairs, p_noise, 1.0, model)[0] for _ in range(calib_trials)]
    S_f1_hat, S_f1_std = float(np.mean(S_f1_list)), float(np.std(S_f1_list))

    S_star = (S_H_hat + S_f1_hat) / 2.0
    return S_star, S_H_hat, S_H_std, S_f1_hat, S_f1_std


# ===========================================================================
# SECTION 2: MAIN SWEEP WITH CALIBRATED THRESHOLD (row-level resumable)
# ===========================================================================
def _read_rows(out_csv):
    if not os.path.exists(out_csv):
        return None, []
    with open(out_csv, newline='') as f:
        rows = list(csv.reader(f))
    if not rows:
        return None, []
    return rows[0], rows[1:]


def run_calibrated_sweep(noise_profiles, default_trials, default_num_pairs, default_f_fractions,
                          default_calib_trials, out_csv):
    """
    Each entry in `noise_profiles` may optionally override trials,
    num_pairs, f_fractions, and calib_trials (used by IBM_Marrakesh, which
    runs at a different scale than the synthetic profiles). Falls back to
    the default_* arguments when not overridden.
    """
    print("==========================================")
    print(" E91 ADAPTIVE (CALIBRATED) THRESHOLD SWEEP")
    print("==========================================")

    header, body = _read_rows(out_csv)
    if header is None:
        header = ["Noise_Profile", "S_star", "S_H_hat", "S_H_std", "S_f1_hat", "S_f1_std",
                   "F_Eve", "Mean_S", "Std_S", "Mean_SKR", "Std_SKR", "FPR", "FNR"]
        with open(out_csv, mode='w', newline='') as f:
            csv.writer(f).writerow(header)
        body = []

    done_f_by_profile = {}
    calib_by_profile = {}
    for row in body:
        name = row[0]
        done_f_by_profile.setdefault(name, set()).add(round(float(row[6]), 4))
        calib_by_profile[name] = (float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5]))

    calibration = {}
    for i, (noise_name, params) in enumerate(noise_profiles.items()):
        p, model = params["p_noise"], params["model"]
        trials = params.get("trials", default_trials)
        num_pairs = params.get("num_pairs", default_num_pairs)
        f_fractions = params.get("f_fractions", default_f_fractions)
        calib_trials = params.get("calib_trials", default_calib_trials)

        done_f = done_f_by_profile.get(noise_name, set())
        if len(done_f) >= len(f_fractions):
            calibration[noise_name] = calib_by_profile[noise_name]
            print(f"-> {noise_name}: already complete ({len(done_f)}/{len(f_fractions)} f-values), skipping.")
            continue

        if noise_name in calib_by_profile:
            S_star, S_H_hat, S_H_std, S_f1_hat, S_f1_std = calib_by_profile[noise_name]
            print(f"-> {noise_name}: resuming, reusing existing S* = {S_star:.4f} "
                  f"({len(done_f)}/{len(f_fractions)} f-values already done)")
        else:
            S_star, S_H_hat, S_H_std, S_f1_hat, S_f1_std = calibrate_e91_threshold(
                num_pairs, p, model, calib_trials=calib_trials, seed=1000 + i)
            print(f"\n-> {noise_name}: S_H={S_H_hat:.4f} (+/-{S_H_std:.4f})  "
                  f"S_f(f=1)={S_f1_hat:.4f} (+/-{S_f1_std:.4f})  =>  S* = {S_star:.4f}")
        calibration[noise_name] = (S_star, S_H_hat, S_H_std, S_f1_hat, S_f1_std)

        for f in f_fractions:
            if round(f, 4) in done_f:
                continue
            ms, ss, mq, sq, mskr, sskr, fpr, fnr = base.monte_carlo_e91(
                trials, num_pairs, p, f, chsh_threshold=S_star,
                seed=2000 + i * 1000 + int(round(f * 100)), device_noise_model=model)

            print(f"      f={f:.2f} | S: {ms:.4f} | SKR: {mskr:.4f} | FPR: {fpr:.2f} | FNR: {fnr:.2f}")

            with open(out_csv, mode='a', newline='') as file:
                csv.writer(file).writerow([noise_name, S_star, S_H_hat, S_H_std, S_f1_hat, S_f1_std,
                                            f, ms, ss, mskr, sskr, fpr, fnr])
            done_f.add(round(f, 4))

    print(f"\nProgress saved to: {out_csv}")
    return calibration


def all_profiles_complete(noise_profiles, default_f_fractions, out_csv):
    header, body = _read_rows(out_csv)
    if header is None:
        return False
    counts = {}
    for row in body:
        counts[row[0]] = counts.get(row[0], 0) + 1
    for name, params in noise_profiles.items():
        expected = len(params.get("f_fractions", default_f_fractions))
        if counts.get(name, 0) < expected:
            return False
    return True


# ===========================================================================
# SECTION 3: MIS-CALIBRATION ROBUSTNESS CHECK (synthetic profiles only)
# ===========================================================================
def run_miscalibration_check(noise_profiles, calibration, trials, num_pairs, out_csv):
    print("\n==========================================")
    print(" MIS-CALIBRATION ROBUSTNESS CHECK")
    print("==========================================")

    header, body = _read_rows(out_csv)
    if header is None:
        header = ["Calibrated_At", "S_star", "Evaluated_At", "Drift", "FPR_honest", "FNR_full_attack"]
        with open(out_csv, mode='w', newline='') as f:
            csv.writer(f).writerow(header)
        body = []
    done_pairs = {(row[0], row[2]) for row in body}

    names = list(noise_profiles.keys())
    for i, calib_name in enumerate(names):
        S_star = calibration[calib_name][0]
        for j, eval_name in enumerate(names):
            drift = j - i
            if drift == 0 or abs(drift) > 1:
                continue
            if (calib_name, eval_name) in done_pairs:
                continue
            p_eval, model_eval = noise_profiles[eval_name]["p_noise"], noise_profiles[eval_name]["model"]

            _, _, _, _, _, _, fpr, _ = base.monte_carlo_e91(
                trials, num_pairs, p_eval, 0.0, chsh_threshold=S_star,
                seed=5000 + i * 100 + j, device_noise_model=model_eval)
            _, _, _, _, _, _, _, fnr = base.monte_carlo_e91(
                trials, num_pairs, p_eval, 1.0, chsh_threshold=S_star,
                seed=6000 + i * 100 + j, device_noise_model=model_eval)

            print(f"  Calibrated@{calib_name} (S*={S_star:.3f})  ->  Evaluated@{eval_name} "
                  f"(drift {drift:+d} step)  FPR={fpr:.2f}  FNR={fnr:.2f}")

            with open(out_csv, mode='a', newline='') as file:
                csv.writer(file).writerow([calib_name, S_star, eval_name, drift, fpr, fnr])
    print(f"\nSaved: {out_csv}")


# ===========================================================================
# MAIN
# ===========================================================================
if __name__ == "__main__":
    start = time.time()

    TRIALS = 50
    E91_PAIRS = 8192
    F_FRACTIONS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    CALIB_TRIALS = 30

    synthetic_profiles = {
        "Ideal_0%": {"p_noise": 0.0, "model": None},
        "Noise_2%": {"p_noise": 0.04, "model": None},
        "Noise_5%": {"p_noise": 0.10, "model": None},
        "Noise_8%": {"p_noise": 0.16, "model": None},
        "Threshold_11%": {"p_noise": 0.22, "model": None},
    }

    all_profiles = dict(synthetic_profiles)

    ibm_model = get_ibm_marrakesh_noise_model()
    if ibm_model is not None:
        all_profiles["IBM_Marrakesh"] = {
            "p_noise": 0.0,
            "model": ibm_model,
            "trials": 30,
            "num_pairs": 1024,
            "f_fractions": [0.0, 0.25, 0.5, 0.75, 1.0],
            "calib_trials": 15,
        }

    calibration = run_calibrated_sweep(
        all_profiles, TRIALS, E91_PAIRS, F_FRACTIONS, CALIB_TRIALS,
        out_csv="data/qkd_e91_calibrated.csv")

    if all_profiles_complete(all_profiles, F_FRACTIONS, "data/qkd_e91_calibrated.csv"):
        # Mis-calibration drift check only makes sense across the synthetic
        # noise ladder -- see module docstring for why IBM_Marrakesh is excluded.
        synthetic_calibration = {k: v for k, v in calibration.items() if k in synthetic_profiles}
        run_miscalibration_check(
            synthetic_profiles, synthetic_calibration, trials=TRIALS, num_pairs=E91_PAIRS,
            out_csv="data/qkd_e91_miscalibration.csv")
    else:
        print(f"\nMain sweep not yet complete -- skipping mis-calibration check this run. "
              f"Re-run the script to continue.")

    print(f"\nTotal elapsed: {(time.time()-start)/60:.2f} min")
