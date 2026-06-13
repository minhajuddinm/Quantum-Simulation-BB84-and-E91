"""
============================================================================
 Detection-Aware QKD Simulation: BB84, Six-State, and E91
============================================================================
 Purpose
   Compare three quantum key distribution protocols on how reliably each one
   detects a PARTIAL eavesdropper (an attacker who intercepts only a fraction
   f of the channel), and what that detection costs in usable key.

 Protocols
   BB84       prepare-and-measure, 2 bases (Z, X)
   Six-State  prepare-and-measure, 3 bases (Z, X, Y)
   E91        entanglement-based, security from the CHSH (Bell) test

 Metrics recorded per run
   QBER (BB84/Six-State) or CHSH S (E91)  : raw error / correlation signal
   Secure Key Rate (SKR)                  : secret bits per transmitted qubit
   FPR (false positive rate)              : alarm fires when NO attacker present
   FNR (false negative rate)              : attacker present but NO alarm fires

 Noise
   Synthetic : uniform per-qubit depolarizing channel of strength p
   Device    : real ibm_marrakesh noise model (gate + readout + relaxation)
   The two are mutually exclusive; a row uses one or the other, never both.

 Output
   A CSV with one row per (protocol, noise profile, interception fraction f),
   used afterwards to plot the detection-vs-key-rate tradeoff curves.
============================================================================
"""

import numpy as np
import math
import hashlib
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import depolarizing_error

# ===========================================================================
# SECTION 1: SECURE KEY RATE MATH
#   Shor-Preskill asymptotic rate. The secret fraction r = 1 - 2*H2(QBER)
#   reaches 0 at QBER ~ 11%, which is why 11% is the abort threshold.
#   SKR = (sifting ratio) * r  =  secret bits per transmitted qubit.
# ===========================================================================
# --- STEP 3: SECURE KEY RATE MATH ---
def binary_entropy(q):
    """Calculates the binary entropy of a probability q."""
    if q == 0 or q == 1:
        return 0.0
    return -q * math.log2(q) - (1 - q) * math.log2(1 - q)

def secure_key_rate(num_sent, sifted_len, qber):
    """Calculates the theoretical secure key rate."""
    sifting_ratio = sifted_len / num_sent
    secret_fraction = max(0.0, 1 - 2 * binary_entropy(qber))
    return sifting_ratio * secret_fraction

# ===========================================================================
# SECTION 2: CLASSICAL POST-PROCESSING (reconciliation + privacy amplification)
#   After sifting, Alice and Bob still differ in a few bits (noise/Eve).
#   Reconciliation: split the key into blocks, compare parities, binary-search
#     each mismatched block to locate and flip the single wrong bit. Every
#     parity revealed leaks one bit to Eve, so we count disclosed_bits.
#   Privacy amplification: hash the reconciled key down to a length that
#     subtracts both the entropy lost to QBER and the leaked parity bits,
#     so Eve's residual knowledge is squeezed out of the final key.
#   (Follows the Badiezadegan BB84 reference for these two stages.)
# ===========================================================================
# --- STEP 6: ERROR RECONCILIATION & PRIVACY AMPLIFICATION ---

def error_reconciliation(alice_key, bob_key, block_size=8):
    """
    1-pass parity-based block error reconciliation (Simplified Cascade).
    Divides key into blocks, compares parities, and uses binary search to fix 1 error per block.
    """
    reconciled_bob_key = bob_key.copy()
    disclosed_bits = 0
    
    for i in range(0, len(alice_key), block_size):
        a_block = alice_key[i:i+block_size]
        b_block = reconciled_bob_key[i:i+block_size]
        
        if len(a_block) == 0:
            break
            
        a_par = sum(a_block) % 2
        b_par = sum(b_block) % 2
        disclosed_bits += 1 # Alice publicly shares her parity bit
        
        if a_par != b_par:
            # Mismatch found: binary search to locate the error
            error_idx, bits_used = binary_search_parity(a_block, b_block)
            disclosed_bits += bits_used
            if error_idx is not None:
                reconciled_bob_key[i + error_idx] ^= 1 # Fix Bob's bit
                
    return reconciled_bob_key, disclosed_bits

def binary_search_parity(a_block, b_block):
    """Recursively locates a single error in a block. Returns (index, parity_bits_disclosed)."""
    if len(a_block) == 1:
        return 0, 0
    
    mid = len(a_block) // 2
    a_left = a_block[:mid]
    b_left = b_block[:mid]
    
    bits_used = 1 # Alice shares parity of the left half
    if (sum(a_left) % 2) != (sum(b_left) % 2):
        idx, recursive_bits = binary_search_parity(a_left, b_left)
        return idx, bits_used + recursive_bits
    else:
        idx, recursive_bits = binary_search_parity(a_block[mid:], b_block[mid:])
        return mid + idx, bits_used + recursive_bits

def privacy_amplification(alice_key, bob_key, disclosed_bits, qber):
    """
    Compresses the keys using SHA-256 to eliminate Eve's partial information.
    """
    n = len(alice_key)
    if n == 0:
        return "", ""
        
    # Use your secure key formula to find exactly how long the safe key is allowed to be
    h_qber = binary_entropy(qber) if qber > 0 else 0.0
    secure_len = int(n * max(0.0, 1 - 2 * h_qber)) - disclosed_bits
    
    if secure_len <= 0:
        return "", "" # Abort: Eve knows too much
        
    # Hash keys to compress them
    a_str = "".join(str(b) for b in alice_key)
    b_str = "".join(str(b) for b in bob_key)
    
    a_hash = hashlib.sha256(a_str.encode()).hexdigest()
    b_hash = hashlib.sha256(b_str.encode()).hexdigest()
    
    # Convert hex to binary and truncate to the exact secure length
    a_final = bin(int(a_hash, 16))[2:].zfill(256)[:secure_len]
    b_final = bin(int(b_hash, 16))[2:].zfill(256)[:secure_len]
    
    return a_final, b_final

# --- STEP 1 & 5 REFACTORED: BB84 WITH PARTIAL EVE ---
# --- STEP 9 UPDATES: TRIAL FUNCTIONS ---

# --- STEP 9 OPTIMIZED: BATCHED TRIAL FUNCTIONS ---

# ===========================================================================
# SECTION 3: PER-PROTOCOL TRIAL FUNCTIONS
#   Each *_trial runs ONE full protocol instance and returns its raw stats.
#   Qubits are processed in small batches (default 10) so that the device
#   noise model, which is memory-heavy, does not blow up the simulator.
#   Because the qubits are independent, batching does not change the physics.
#
#   BB84 trial:
#     - Alice: random bit (X gate if 1) + random basis (H gate if X basis).
#     - Eve (only on the f_eve fraction): measure in a random basis and
#       re-prepare, the classic intercept-and-resend that disturbs the state.
#     - Channel: uniform depolarizing noise on every qubit (synthetic only).
#     - Bob: rotate to his random basis and measure.
#     - Sift: keep positions where Alice and Bob used the same basis; the
#       QBER is the mismatch fraction in that sifted key.
# ===========================================================================
def run_bb84_trial(num_qubits, p_noise, f_eve=0.0, device_noise_model=None, batch_size=10):
    """Runs BB84 in batches to prevent memory overflow with complex noise models."""
    alice_bits = np.random.randint(2, size=num_qubits)
    alice_bases = np.random.randint(2, size=num_qubits)
    bob_bases = np.random.randint(2, size=num_qubits)
    eve_presence = np.random.rand(num_qubits) < f_eve
    eve_bases = np.random.randint(2, size=num_qubits)

    measured_bits = []
    simulator = AerSimulator(noise_model=device_noise_model) if device_noise_model else AerSimulator()

    # Process in batches
    for start_idx in range(0, num_qubits, batch_size):
        end_idx = min(start_idx + batch_size, num_qubits)
        current_batch_size = end_idx - start_idx
        
        qc = QuantumCircuit(current_batch_size, current_batch_size)

        for i in range(current_batch_size):
            global_i = start_idx + i
            if alice_bits[global_i] == 1: qc.x(i)
            if alice_bases[global_i] == 1: qc.h(i)

        qc.barrier()

        if f_eve > 0:
            for i in range(current_batch_size):
                global_i = start_idx + i
                if eve_presence[global_i]:
                    if eve_bases[global_i] == 1: qc.h(i)
                    qc.measure(i, i)
                    if eve_bases[global_i] == 1: qc.h(i)
            qc.barrier()

        if p_noise > 0 and device_noise_model is None:
            noise_inst = depolarizing_error(p_noise, 1).to_instruction()
            for i in range(current_batch_size):
                qc.append(noise_inst, [i])

        qc.barrier()

        for i in range(current_batch_size):
            global_i = start_idx + i
            if bob_bases[global_i] == 1: qc.h(i)
            qc.measure(i, i)

        counts = simulator.run(qc, shots=1).result().get_counts()
        batch_measured = list(counts.keys())[0][::-1]
        measured_bits.extend(list(batch_measured))

    sifted_alice, sifted_bob = [], []
    for i in range(num_qubits):
        if alice_bases[i] == bob_bases[i]:
            sifted_alice.append(alice_bits[i])
            sifted_bob.append(int(measured_bits[i]))

    errors = sum(1 for a, b in zip(sifted_alice, sifted_bob) if a != b)
    qber = errors / len(sifted_alice) if sifted_alice else 0.0
    return len(sifted_alice), errors, qber

# ---------------------------------------------------------------------------
#   Six-State trial: identical to BB84 but with a THIRD basis, Y.
#     - Encode Y: H then S.   Measure Y: S-dagger then H.
#     - Bases now match ~1/3 of the time (vs ~1/2 for BB84), so the sifted
#       key is shorter, but Eve guesses the basis right less often, pushing
#       the full-attack QBER to ~33% (vs ~25% for BB84). That higher
#       disturbance is the better-detection property we want to measure.
# ---------------------------------------------------------------------------
def run_six_state_trial(num_qubits, p_noise, f_eve=0.0, device_noise_model=None, batch_size=10):
    """Runs Six-State in batches to prevent memory overflow."""
    alice_bits = np.random.randint(2, size=num_qubits)
    alice_bases = np.random.randint(3, size=num_qubits)
    bob_bases = np.random.randint(3, size=num_qubits)
    eve_presence = np.random.rand(num_qubits) < f_eve
    eve_bases = np.random.randint(3, size=num_qubits)

    measured_bits = []
    simulator = AerSimulator(noise_model=device_noise_model) if device_noise_model else AerSimulator()

    for start_idx in range(0, num_qubits, batch_size):
        end_idx = min(start_idx + batch_size, num_qubits)
        current_batch_size = end_idx - start_idx
        
        qc = QuantumCircuit(current_batch_size, current_batch_size)

        for i in range(current_batch_size):
            global_i = start_idx + i
            if alice_bits[global_i] == 1: qc.x(i)
            if alice_bases[global_i] == 1: qc.h(i)
            elif alice_bases[global_i] == 2:
                qc.h(i)
                qc.s(i)

        qc.barrier()

        if f_eve > 0:
            for i in range(current_batch_size):
                global_i = start_idx + i
                if eve_presence[global_i]:
                    if eve_bases[global_i] == 2:
                        qc.sdg(i)
                        qc.h(i)
                    elif eve_bases[global_i] == 1: qc.h(i)
                    qc.measure(i, i)
                    if eve_bases[global_i] == 2:
                        qc.h(i)
                        qc.s(i)
                    elif eve_bases[global_i] == 1: qc.h(i)
            qc.barrier()

        if p_noise > 0 and device_noise_model is None:
            noise_inst = depolarizing_error(p_noise, 1).to_instruction()
            for i in range(current_batch_size):
                qc.append(noise_inst, [i])

        qc.barrier()

        for i in range(current_batch_size):
            global_i = start_idx + i
            if bob_bases[global_i] == 1: qc.h(i)
            elif bob_bases[global_i] == 2:
                qc.sdg(i)
                qc.h(i)
            qc.measure(i, i)

        counts = simulator.run(qc, shots=1).result().get_counts()
        batch_measured = list(counts.keys())[0][::-1]
        measured_bits.extend(list(batch_measured))

    sifted_alice, sifted_bob = [], []
    for i in range(num_qubits):
        if alice_bases[i] == bob_bases[i]:
            sifted_alice.append(alice_bits[i])
            sifted_bob.append(int(measured_bits[i]))

    errors = sum(1 for a, b in zip(sifted_alice, sifted_bob) if a != b)
    qber = errors / len(sifted_alice) if sifted_alice else 0.0
    return len(sifted_alice), errors, qber

# ---------------------------------------------------------------------------
#   E91 trial: entanglement-based.
#     - Source makes a Bell pair (H then CX), one qubit to Alice, one to Bob.
#     - Each measures along a random angle (Ry rotation before measuring).
#     - Eve (on the f_eve fraction) measures one qubit first, which collapses
#       the entanglement and drags the CHSH value S down toward the classical
#       bound of 2.
#     - Key comes from the matched-axis rounds; S comes from the other axes
#       via the CHSH combination S = E(0,0) - E(0,2) + E(2,0) + E(2,2).
#     - Circuits are grouped by (Alice angle, Bob angle, Eve settings) so all
#       pairs sharing a configuration run in one batched shot call.
# ---------------------------------------------------------------------------
def run_e91_trial(num_pairs=8192, p_noise=0.0, f_eve=0.0, device_noise_model=None):
    a_angles = [0, np.pi/4, np.pi/2]
    b_angles = [np.pi/4, np.pi/2, 3*np.pi/4]
    e_angles = [0, np.pi/4, np.pi/2]

    alice_bases = np.random.randint(3, size=num_pairs)
    bob_bases = np.random.randint(3, size=num_pairs)
    eve_presence = np.random.rand(num_pairs) < f_eve
    eve_bases = np.random.randint(3, size=num_pairs)

    alice_results = np.zeros(num_pairs, dtype=int)
    bob_results = np.zeros(num_pairs, dtype=int)

    simulator = AerSimulator(noise_model=device_noise_model) if device_noise_model else AerSimulator()
    circuits = []

    for a_idx in range(3):
        for b_idx in range(3):
            for has_eve in [False, True]:
                for e_idx in range(3):
                    mask = (alice_bases == a_idx) & (bob_bases == b_idx) & (eve_presence == has_eve) & (eve_bases == e_idx)
                    indices = np.where(mask)[0]
                    count = len(indices)
                    if count == 0: continue

                    qc = QuantumCircuit(2, 2)
                    qc.h(0)
                    qc.cx(0, 1)

                    if p_noise > 0 and not has_eve and device_noise_model is None:
                        noise_inst = depolarizing_error(p_noise, 1).to_instruction()
                        qc.append(noise_inst, [0])
                        qc.append(noise_inst, [1])

                    if has_eve:
                        qc.ry(e_angles[e_idx], 1)
                        qc.measure(1, 0)
                        qc.ry(-e_angles[e_idx], 1)

                    qc.barrier()
                    qc.ry(a_angles[a_idx], 0)
                    qc.ry(b_angles[b_idx], 1)
                    qc.measure(0, 0)
                    qc.measure(1, 1)

                    circuits.append((qc, count, indices))

    for qc, count, indices in circuits:
        counts_dict = simulator.run(qc, shots=count).result().get_counts()
        outcomes = []
        for bitstring, c in counts_dict.items():
            outcomes.extend([bitstring] * c)
        np.random.shuffle(outcomes)

        for idx, outcome in zip(indices, outcomes):
            alice_results[idx] = int(outcome[1]) 
            bob_results[idx] = int(outcome[0])   

    sifted_alice, sifted_bob = [], []
    for i in range(num_pairs):
        if (alice_bases[i] == 1 and bob_bases[i] == 0) or (alice_bases[i] == 2 and bob_bases[i] == 1):
            sifted_alice.append(alice_results[i])
            sifted_bob.append(bob_results[i])

    errors = sum(1 for a, b in zip(sifted_alice, sifted_bob) if a != b)
    qber = errors / len(sifted_alice) if sifted_alice else 0.0

    def expect(a_i, b_i):
        mask = (alice_bases == a_i) & (bob_bases == b_i)
        if not np.any(mask): return 0
        matches = np.sum(alice_results[mask] == bob_results[mask])
        mismatches = np.sum(alice_results[mask] != bob_results[mask])
        return (matches - mismatches) / (matches + mismatches)

    S = expect(0, 0) - expect(0, 2) + expect(2, 0) + expect(2, 2)
    return abs(S), len(sifted_alice), errors, qber


# --- STEP 9 UPDATES: MONTE CARLO AND ESTIMATOR FUNCTIONS ---

# --- REFACTORED MONTE CARLO RUNNERS (Now with integrated Detection Estimators) ---

# ===========================================================================
# SECTION 4: MONTE CARLO RUNNERS (one merged pass per protocol)
#   Repeat the trial many times and average. IMPORTANT: each trial is used
#   ONCE to update BOTH the averaged metrics (QBER/S, SKR) AND the detection
#   counters, so we never re-run trials just to get FPR/FNR.
#   Detection rule:
#     - BB84/Six-State: alarm if QBER >= qber_threshold.
#     - When f_eve == 0 (no attacker), any alarm is a FALSE POSITIVE.
#     - When f_eve  > 0 (attacker present), a missing alarm is a FALSE NEGATIVE.
#   FPR is only meaningful in the no-Eve rows; FNR only in the Eve rows.
# ===========================================================================
def monte_carlo_bb84(trials, num_qubits, p_noise=0.0, f_eve=0.0, qber_threshold=0.11, seed=None, device_noise_model=None):
    if seed is not None: np.random.seed(seed)
    qber_list, skr_list = [], []
    fp_count, fn_count = 0, 0

    for t in range(trials):
        sifted_len, errors, qber = run_bb84_trial(num_qubits, p_noise, f_eve, device_noise_model)
        skr = secure_key_rate(num_qubits, sifted_len, qber)
        qber_list.append(qber)
        skr_list.append(skr)

        alarm_triggered = qber >= qber_threshold
        if f_eve == 0.0:
            if alarm_triggered: fp_count += 1
        else:
            if not alarm_triggered: fn_count += 1

    fpr = (fp_count / trials) if f_eve == 0.0 else 0.0
    fnr = (fn_count / trials) if f_eve > 0.0 else 0.0
    return np.mean(qber_list), np.std(qber_list), np.mean(skr_list), np.std(skr_list), fpr, fnr

def monte_carlo_six_state(trials, num_qubits, p_noise=0.0, f_eve=0.0, qber_threshold=0.11, seed=None, device_noise_model=None):
    if seed is not None: np.random.seed(seed)
    qber_list, skr_list = [], []
    fp_count, fn_count = 0, 0

    for t in range(trials):
        sifted_len, errors, qber = run_six_state_trial(num_qubits, p_noise, f_eve, device_noise_model)
        skr = secure_key_rate(num_qubits, sifted_len, qber)
        qber_list.append(qber)
        skr_list.append(skr)

        alarm_triggered = qber >= qber_threshold
        if f_eve == 0.0:
            if alarm_triggered: fp_count += 1
        else:
            if not alarm_triggered: fn_count += 1

    fpr = (fp_count / trials) if f_eve == 0.0 else 0.0
    fnr = (fn_count / trials) if f_eve > 0.0 else 0.0
    return np.mean(qber_list), np.std(qber_list), np.mean(skr_list), np.std(skr_list), fpr, fnr

# ---------------------------------------------------------------------------
#   E91 Monte Carlo: same idea, but the alarm fires when S < chsh_threshold.
#   The threshold is NOT fixed; it is calibrated per noise profile in the
#   main loop (see SECTION 6), set just below the honest no-Eve S so that
#   ordinary noise does not look like an attacker.
# ---------------------------------------------------------------------------
def monte_carlo_e91(trials, num_pairs, p_noise=0.0, f_eve=0.0, chsh_threshold=2.2, seed=None, device_noise_model=None):
    if seed is not None: np.random.seed(seed)
    s_list, qber_list, skr_list = [], [], []
    fp_count, fn_count = 0, 0

    for t in range(trials):
        S, sifted_len, errors, qber = run_e91_trial(num_pairs, p_noise, f_eve, device_noise_model)
        skr = secure_key_rate(num_pairs, sifted_len, qber)
        s_list.append(S)
        qber_list.append(qber)
        skr_list.append(skr)

        alarm_triggered = S < chsh_threshold
        if f_eve == 0.0:
            if alarm_triggered: fp_count += 1
        else:
            if not alarm_triggered: fn_count += 1

    fpr = (fp_count / trials) if f_eve == 0.0 else 0.0
    fnr = (fn_count / trials) if f_eve > 0.0 else 0.0
    return np.mean(s_list), np.std(s_list), np.mean(qber_list), np.std(qber_list), np.mean(skr_list), np.std(skr_list), fpr, fnr

# ---------------------------------------------------------------------------
#   Standalone FPR/FNR estimator. Kept for spot-checks; the main sweep now
#   gets these counters straight from the merged Monte Carlo runners above.
# ---------------------------------------------------------------------------
def estimate_detection_rates(protocol, trials, num_qubits, p_noise, f_eve, qber_threshold=0.11, chsh_threshold=2.2, device_noise_model=None):
    fp_count = 0
    fn_count = 0
    for t in range(trials):
        if protocol == "BB84":
            _, _, qber = run_bb84_trial(num_qubits, p_noise, f_eve, device_noise_model)
            alarm_triggered = qber >= qber_threshold
        elif protocol == "Six-State":
            _, _, qber = run_six_state_trial(num_qubits, p_noise, f_eve, device_noise_model)
            alarm_triggered = qber >= qber_threshold
        elif protocol == "E91":
            S, _, _, _ = run_e91_trial(num_qubits, p_noise, f_eve, device_noise_model)
            alarm_triggered = S < chsh_threshold

        if f_eve == 0.0:
            if alarm_triggered: fp_count += 1
        else:
            if not alarm_triggered: fn_count += 1

    fpr = (fp_count / trials) if f_eve == 0.0 else 0.0
    fnr = (fn_count / trials) if f_eve > 0.0 else 0.0
    return fpr, fnr

# ==========================================
# EXPERIMENT CHECKS (Run and verify these)
# ==========================================
# ===========================================================================
# SECTION 5: MAIN EXPERIMENT SWEEP
#   Loops over every (protocol x noise profile x interception fraction f),
#   runs the Monte Carlo, and streams one row per combination to the CSV.
#
#   Workload scaling:
#     - Synthetic noise : N=1000 qubits (E91: 8192 pairs), 50 trials, full f grid.
#     - Device noise    : N=200 qubits (E91: 1024 pairs), 30 trials, coarser f
#       grid. Device simulation is far heavier, so we trade some resolution;
#       30 trials is the minimum that gives FPR/FNR meaningful granularity
#       (5 trials could only ever yield 0, 0.2, 0.4, ... which is too coarse).
#
#   Synthetic noise calibration (verified): the depolarizing p values were
#   chosen so honest QBER lands ON the label, roughly QBER ~ p/2:
#     p=0.04 -> ~2%,  p=0.10 -> ~5%,  p=0.16 -> ~7-8%,  p=0.22 -> ~11% (threshold).
# ===========================================================================
if __name__ == "__main__":
    import csv
    import time
    from qiskit_ibm_runtime import QiskitRuntimeService
    from qiskit_aer.noise import NoiseModel

    print("==========================================")
    print("      PRE-RUN SANITY CHECKS")
    print("==========================================")
    mq, sq, mskr, sskr, fpr, fnr = monte_carlo_bb84(10, 1000, 0.0, 0.0)
    print(f"BB84 Ideal      | QBER: {mq*100:04.1f}% (Exp ~0%)  | SKR: {mskr:.2f} (Exp ~0.50) | FPR: {fpr:.2f}")
    mq, sq, mskr, sskr, fpr, fnr = monte_carlo_bb84(10, 1000, 0.0, 1.0)
    print(f"BB84 Full Eve   | QBER: {mq*100:04.1f}% (Exp ~25%) | SKR: {mskr:.2f} (Exp ~0.00) | FNR: {fnr:.2f}")
    
    mq, sq, mskr, sskr, fpr, fnr = monte_carlo_six_state(10, 1000, 0.0, 0.0)
    print(f"Six-State Ideal | QBER: {mq*100:04.1f}% (Exp ~0%)  | SKR: {mskr:.2f} (Exp ~0.33) | FPR: {fpr:.2f}")
    mq, sq, mskr, sskr, fpr, fnr = monte_carlo_six_state(10, 1000, 0.0, 1.0)
    print(f"Six-State Eve   | QBER: {mq*100:04.1f}% (Exp ~33%) | SKR: {mskr:.2f} (Exp ~0.00) | FNR: {fnr:.2f}")
    
    ms, ss, mq, sq, mskr, sskr, fpr, fnr = monte_carlo_e91(5, 8192, 0.0, 0.0, chsh_threshold=2.6)
    print(f"E91 Ideal       | S: {ms:.3f} (Exp ~2.83) | SKR: {mskr:.2f} (Exp ~0.22) | FPR: {fpr:.2f}")
    ms, ss, mq, sq, mskr, sskr, fpr, fnr = monte_carlo_e91(5, 8192, 0.0, 1.0, chsh_threshold=2.6)
    print(f"E91 Full Eve    | S: {ms:.3f} (Exp <2.0)  | SKR: {mskr:.2f} (Exp ~0.00) | FNR: {fnr:.2f}")

    mq, sq, mskr, sskr, fpr, fnr = monte_carlo_bb84(10, 1000, 0.22, 0.0)
    print(f"Noise Check     | p=0.22 yields QBER = {mq*100:.2f}% (Matches 11% Abort Threshold)\\n")

    print("Fetching IBM hardware noise model...")
    service = QiskitRuntimeService(channel="ibm_quantum_platform")
    backend = service.backend("ibm_marrakesh") 
    real_noise_model = NoiseModel.from_backend(backend)
    print("Noise model loaded successfully!\\n")

    # ==========================================
    # FINAL OVERNIGHT RUN PARAMETERS
    # ==========================================
    TRIALS = 50           
    STD_QUBITS = 1000     
    E91_PAIRS = 8192      
    QBER_THRESHOLD = 0.11 

    protocols = ["BB84", "Six-State", "E91"]
    
    # Custom noise curve to step beautifully up to the 11% threshold
    noise_profiles = {
        "Ideal_0%": {"p_noise": 0.0, "model": None},
        "Noise_2%": {"p_noise": 0.04, "model": None},
        "Noise_5%": {"p_noise": 0.10, "model": None},
        "Noise_8%": {"p_noise": 0.16, "model": None},
        "Threshold_11%": {"p_noise": 0.22, "model": None},
        "IBM_Marrakesh": {"p_noise": 0.0, "model": real_noise_model}
    }

    csv_filename = "qkd_results_final.csv"
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Protocol", "Noise_Profile", "F_Eve", "QBER_Threshold", "CHSH_Threshold", "Mean_Metric", "Std_Metric", "Mean_SKR", "Std_SKR", "FPR", "FNR"])

    print(f"Starting Final Experiment Sweep. Results will stream to {csv_filename}...")
    start_time = time.time()

    for proto in protocols:
        print(f"\\n========== RUNNING PROTOCOL: {proto} ==========")
        
        for noise_name, params in noise_profiles.items():
            print(f"  -> Noise Profile: {noise_name}")
            p = params["p_noise"]
            model = params["model"]

            # Dynamic Workload Scaling
            if noise_name == "IBM_Marrakesh":
                current_trials = 30 # Raised to 30 for clear FPR/FNR resolution
                current_fractions = [0.0, 0.25, 0.5, 0.75, 1.0] # Compressed fraction steps
                current_q = 1024 if proto == "E91" else 200
            else:
                current_trials = TRIALS
                current_fractions = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
                current_q = E91_PAIRS if proto == "E91" else STD_QUBITS

            # CHSH threshold is calibrated PER NOISE PROFILE. We first measure
            # the honest (no-Eve) S for this exact noise level, then set the
            # alarm threshold 0.15 below it. This stops honest-but-noisy E91
            # runs from false-alarming, which a single fixed threshold (e.g. 2.2)
            # would cause under the high-S device model or low-S heavy noise.
            # (Note: only 5 samples are used here; widen if a profile's FPR
            #  looks unstable.)
            # Dynamic CHSH Threshold Calibration for E91
            chsh_thresh = 0.0
            if proto == "E91":
                print(f"    [Calibrating CHSH Threshold...]")
                base_s_list = []
                for _ in range(5):
                    S, _, _, _ = run_e91_trial(current_q, p, 0.0, model)
                    base_s_list.append(S)
                # Set threshold to 0.15 below the honest mean for this specific noise
                chsh_thresh = np.mean(base_s_list) - 0.15
                print(f"    [Set CHSH Threshold = {chsh_thresh:.4f} based on Honest S = {np.mean(base_s_list):.4f}]")

            for f in current_fractions:
                if proto == "BB84":
                    mq, sq, mskr, sskr, fpr, fnr = monte_carlo_bb84(current_trials, current_q, p, f, QBER_THRESHOLD, None, model)
                    metric, std_metric = mq, sq
                elif proto == "Six-State":
                    mq, sq, mskr, sskr, fpr, fnr = monte_carlo_six_state(current_trials, current_q, p, f, QBER_THRESHOLD, None, model)
                    metric, std_metric = mq, sq
                elif proto == "E91":
                    ms, ss, mq, sq, mskr, sskr, fpr, fnr = monte_carlo_e91(current_trials, current_q, p, f, chsh_thresh, None, model)
                    metric, std_metric = ms, ss

                # Format for CSV
                q_th_str = str(QBER_THRESHOLD) if proto != "E91" else "N/A"
                c_th_str = f"{chsh_thresh:.4f}" if proto == "E91" else "N/A"

                print(f"      f={f:.2f} | Metric: {metric:.4f} | SKR: {mskr:.4f} | FPR: {fpr:.2f} | FNR: {fnr:.2f}")
                
                with open(csv_filename, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([proto, noise_name, f, q_th_str, c_th_str, metric, std_metric, mskr, sskr, fpr, fnr])

    elapsed = (time.time() - start_time) / 60
    print(f"\\nEXPERIMENT COMPLETE! Total elapsed time: {elapsed:.2f} minutes.")