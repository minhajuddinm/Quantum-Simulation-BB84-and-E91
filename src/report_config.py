"""
============================================================================
 TASK 3: CONFIGURATION / REPRODUCIBILITY REPORT
============================================================================
 Prints the software versions and the simulation configuration facts a
 reviewer needs to reproduce the study. Runtime values (library versions,
 a representative disclosed-parity-bit count from the pure-classical
 reconciliation routine) are computed live. Everything else is a STATIC
 code fact, quoted here with its source location so nothing has to be run.

 NOTE: this script does NOT run any Qiskit/Aer simulation. The only thing
 it executes is the classical error-reconciliation routine on mock keys
 (plain Python/NumPy arithmetic, no quantum circuits), to report a concrete
 example of how many parity bits get disclosed.

 Run:
   python report_config.py
============================================================================
"""

import platform
import sys

import results_md


def _version(modname, attr="__version__"):
    try:
        mod = __import__(modname)
        return getattr(mod, attr, "(installed, version attr missing)")
    except Exception as e:
        return f"(not importable: {e})"


def _dist_version(dist):
    try:
        from importlib.metadata import version
        return version(dist)
    except Exception as e:
        return f"(not found: {e})"


def print_versions():
    print("=" * 70)
    print(" SOFTWARE VERSIONS (runtime)")
    print("=" * 70)
    print(f"  Python            : {platform.python_version()} "
          f"({platform.system()} {platform.release()})")
    print(f"  Python executable : {sys.executable}")
    print(f"  numpy             : {_version('numpy')}")
    print(f"  qiskit            : {_dist_version('qiskit')}")
    print(f"  qiskit-aer        : {_dist_version('qiskit-aer')}")
    print(f"  qiskit-ibm-runtime: {_dist_version('qiskit-ibm-runtime')}")
    print(f"  scipy             : {_dist_version('scipy')}")


def print_static_facts():
    print("\n" + "=" * 70)
    print(" SIMULATION CONFIGURATION (static code facts, with source lines)")
    print("=" * 70)

    print("""
 SHOTS PER CIRCUIT EXECUTION
   BB84 / six-state: 1 shot per batched circuit (one physical run per qubit
   batch), quoted from detection_aware_qkd_varying_eve.py:
       counts = simulator.run(qc, shots=1).result().get_counts()   # line 147 (BB84)
       counts = simulator.run(qc, shots=1).result().get_counts()   # line 218 (six-state)
   E91: shots = number of entangled pairs sharing that (basis, Eve) setting,
   so each pair is one shot:
       counts_dict = simulator.run(qc, shots=count).result().get_counts()  # line 281

 TRANSPILER optimization_level
   NONE IS SET. The code never calls qiskit.transpile(...) and never passes
   optimization_level anywhere (a repo-wide search for 'transpile' and
   'optimization_level' returns no hits in the simulation scripts). Circuits
   are handed directly to AerSimulator.run(), i.e. Aer's default internal
   handling is used with no explicit transpilation pass. Report this as
   "optimization_level: not applied (no explicit transpile step; Aer default)."

 RANDOM SEED POLICY
   Each Monte-Carlo runner seeds NumPy's global RNG once at entry via
       if seed is not None: np.random.seed(seed)     # monte_carlo_* , line 314 / 335 / 356
   The per-trial physics functions (run_bb84_trial / run_six_state_trial /
   run_e91_trial) then draw from that seeded stream (np.random.randint /
   np.random.rand / np.random.shuffle). Seeds are assigned per configuration
   by the driver scripts:
     - e91_adaptive_threshold.py: calibration seed = 1000 + profile_index;
       sweep seed = 2000 + profile_index*1000 + round(f*100).
     - e91_resource_cost_*.py: FPR seed = 8000 + K; FNR seed = 9000 + K
       (offset for 11% channel / fixed mode in e91_resource_cost_sstar.py).
     - ci_reruns.py (Task 2): PER-TRIAL seeding, base_seed + trial_index, so
       runs are reproducible AND identical serial vs. parallel.
   Aer itself is NOT given a separate seed_simulator; measurement sampling
   uses Aer's default RNG. Report: "randomness is controlled at the NumPy
   layer via np.random.seed(seed) per configuration; Aer sampling uses its
   default RNG (no seed_simulator set)."

 ERROR-RECONCILIATION BLOCK SIZE
   block_size = 8 (default arg), quoted from
       def error_reconciliation(alice_key, bob_key, block_size=8):   # line 39
   Reconciliation is a Cascade-style single pass: one parity bit disclosed
   per 8-bit block, and on a parity mismatch a binary search
   (binary_search_parity) discloses ~log2(block) additional parity bits to
   locate and flip one error.

 NUMBER OF PARITY BITS DISCLOSED
   DATA-DEPENDENT (not a fixed constant): tracked at runtime in
   error_reconciliation as `disclosed_bits`:
       disclosed_bits += 1                       # one parity per block, line 52
       disclosed_bits += bits_used               # binary-search bits per mismatched block, line 56
   i.e. disclosed = (#blocks) + sum over mismatched blocks of the binary-search
   parity bits. A concrete example is computed live below.

 RECONCILIATION: SIMULATED vs LEAKAGE-APPROXIMATED
   BOTH aspects are present, and it matters which output you look at:
     * The reconciliation PROCEDURE is actually SIMULATED: error_reconciliation
       really runs the block-parity + binary-search correction and flips Bob's
       mismatched bits (reconciled_bob_key[i+error_idx] ^= 1, line 58), and
       privacy_amplification really hashes the keys (SHA-256) to a shortened
       output (lines 92-96).
     * But the REPORTED secure key rate does NOT use the simulated disclosed-bit
       count. It uses the asymptotic Shor-Preskill leakage APPROXIMATION
       (analytic binary-entropy term); see next block. So: reconciliation is
       simulated for key-agreement validation, while its leakage cost enters
       the headline SKR only through the analytic 2*H(QBER) approximation.

 HOW LEAKAGE ENTERS THE SKR FORMULA
   The reported secure key rate is
       def secure_key_rate(num_sent, sifted_len, qber):
           sifting_ratio  = sifted_len / num_sent
           secret_fraction = max(0.0, 1 - 2 * binary_entropy(qber))   # line 33
           return sifting_ratio * secret_fraction
   Leakage enters ONLY through the analytic  1 - 2*H(QBER)  secret fraction
   (one H(QBER) for error-correction leakage, one for privacy amplification,
   i.e. the Shor-Preskill / Devetak-Winter asymptotic bound). The empirically
   simulated `disclosed_bits` does NOT feed this reported SKR; it only affects
   the finite output length inside privacy_amplification:
       secure_len = int(n * max(0.0, 1 - 2*h_qber)) - disclosed_bits   # line 84
   which is a separate quantity from the SKR reported in the sweeps/CSVs.
   Report: "SKR leakage = analytic 2*H(QBER) (Shor-Preskill asymptotic);
   the simulated disclosed-bit count is tracked but does not enter the
   reported SKR."
""")


def demo_disclosed_bits():
    """Run the pure-classical reconciliation on mock keys (NO quantum sim)
    to report a concrete disclosed-parity-bit example."""
    print("=" * 70)
    print(" DISCLOSED-PARITY-BITS EXAMPLE (live, classical only -- no Aer)")
    print("=" * 70)
    try:
        import numpy as np
        from detection_aware_qkd_varying_eve import error_reconciliation
    except Exception as e:
        print(f"  [skipped: could not import error_reconciliation ({e})]")
        print(f"  The static code facts above still fully specify the behaviour.")
        return

    L = 500  # representative sifted-key length
    for qber in (0.02, 0.05, 0.11):
        np.random.seed(12345)
        alice = list(np.random.randint(2, size=L))
        bob = alice.copy()
        n_flip = int(round(qber * L))
        flip_idx = np.random.choice(L, size=n_flip, replace=False)
        for i in flip_idx:
            bob[i] ^= 1
        _, disclosed = error_reconciliation(alice, bob, block_size=8)
        print(f"  QBER~{qber*100:4.1f}% | key len={L} | block_size=8 "
              f"| disclosed parity bits = {disclosed} "
              f"({disclosed/L*100:.1f}% of key)")
    print("  (illustrative; the exact count is data-dependent per the code above)")
    print("=" * 70)


def write_results_md():
    """Write the ## Task 3 section of results/results.md: live versions plus
    the static reproducibility facts in compact form."""
    rows = [
        ["Python", f"{platform.python_version()} ({platform.system()} {platform.release()})"],
        ["numpy", _version("numpy")],
        ["qiskit", _dist_version("qiskit")],
        ["qiskit-aer", _dist_version("qiskit-aer")],
        ["qiskit-ibm-runtime", _dist_version("qiskit-ibm-runtime")],
        ["scipy", _dist_version("scipy")],
    ]
    body = []
    body.append("### Software versions (runtime)\n")
    body.append(results_md.md_table(["Component", "Version"], rows))
    body.append(
        "\n### Reproducibility facts (static code facts)\n\n"
        "| Item | Value |\n| --- | --- |\n"
        "| Shots per circuit | BB84/six-state: `shots=1` per batched circuit "
        "(one run per qubit batch); E91: `shots=count`, one shot per entangled pair |\n"
        "| Transpiler optimization_level | not applied (no explicit `transpile` step; "
        "circuits handed to `AerSimulator.run()` with Aer defaults) |\n"
        "| Random seed policy | NumPy global RNG seeded per configuration "
        "(`np.random.seed(seed)`); ci_reruns.py seeds per trial (`base_seed + trial`); "
        "Aer given no `seed_simulator` |\n"
        "| Error-reconciliation block size | 8 (`error_reconciliation(..., block_size=8)`), "
        "Cascade-style: 1 parity bit/block + binary-search bits on a mismatch |\n"
        "| Parity bits disclosed | data-dependent runtime count (`disclosed_bits`); "
        "logged per trial as `leak_EC` by ci_reruns.py |\n"
        "| Reconciliation simulated vs approximated | PROCEDURE is simulated (block parity "
        "+ binary search + bit flips + SHA-256 privacy amplification); the asymptotic SKR "
        "leakage is the analytic `2*H2(QBER)` approximation |\n"
        "| Leakage into SKR | asymptotic SKR uses `1 - 2*H2(QBER)` (Shor-Preskill); "
        "the finite-key SKR (Task 4) uses the real simulated `leak_EC` term instead |\n"
    )
    results_md.update_section(
        3, "Configuration and reproducibility report", "\n".join(body))
    print(f"\nWrote Task 3 section -> {results_md.RESULTS_MD}")


if __name__ == "__main__":
    print_versions()
    print_static_facts()
    demo_disclosed_bits()
    write_results_md()
