"""
============================================================================
 SCRIPT 2: VARYING THE SAMPLE SIZE
============================================================================
 Purpose
   Analyze how detection capabilities scale with the length of the string 
   exchanged. Measures FPR (on honest, noisy channels) and FNR (on fully 
   intercepted channels) as a function of the number of tested qubits/pairs.
============================================================================
"""

import numpy as np
import math
import hashlib
import csv
import time
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import depolarizing_error

# ===========================================================================
# SECTION 1: SECURE KEY RATE MATH
# ===========================================================================
def binary_entropy(q):
    if q == 0 or q == 1:
        return 0.0
    return -q * math.log2(q) - (1 - q) * math.log2(1 - q)

def secure_key_rate(num_sent, sifted_len, qber):
    sifting_ratio = sifted_len / num_sent
    secret_fraction = max(0.0, 1 - 2 * binary_entropy(qber))
    return sifting_ratio * secret_fraction

# ===========================================================================
# SECTION 2: CLASSICAL POST-PROCESSING
# ===========================================================================
def error_reconciliation(alice_key, bob_key, block_size=8):
    reconciled_bob_key = bob_key.copy()
    disclosed_bits = 0
    
    for i in range(0, len(alice_key), block_size):
        a_block = alice_key[i:i+block_size]
        b_block = reconciled_bob_key[i:i+block_size]
        
        if len(a_block) == 0:
            break
            
        a_par = sum(a_block) % 2
        b_par = sum(b_block) % 2
        disclosed_bits += 1 
        
        if a_par != b_par:
            error_idx, bits_used = binary_search_parity(a_block, b_block)
            disclosed_bits += bits_used
            if error_idx is not None:
                reconciled_bob_key[i + error_idx] ^= 1 
                
    return reconciled_bob_key, disclosed_bits

def binary_search_parity(a_block, b_block):
    if len(a_block) == 1:
        return 0, 0
    
    mid = len(a_block) // 2
    a_left = a_block[:mid]
    b_left = b_block[:mid]
    
    bits_used = 1 
    if (sum(a_left) % 2) != (sum(b_left) % 2):
        idx, recursive_bits = binary_search_parity(a_left, b_left)
        return idx, bits_used + recursive_bits
    else:
        idx, recursive_bits = binary_search_parity(a_block[mid:], b_block[mid:])
        return mid + idx, bits_used + recursive_bits

def privacy_amplification(alice_key, bob_key, disclosed_bits, qber):
    n = len(alice_key)
    if n == 0:
        return "", ""
        
    h_qber = binary_entropy(qber) if qber > 0 else 0.0
    secure_len = int(n * max(0.0, 1 - 2 * h_qber)) - disclosed_bits
    
    if secure_len <= 0:
        return "", "" 
        
    a_str = "".join(str(b) for b in alice_key)
    b_str = "".join(str(b) for b in bob_key)
    
    a_hash = hashlib.sha256(a_str.encode()).hexdigest()
    b_hash = hashlib.sha256(b_str.encode()).hexdigest()
    
    a_final = bin(int(a_hash, 16))[2:].zfill(256)[:secure_len]
    b_final = bin(int(b_hash, 16))[2:].zfill(256)[:secure_len]
    
    return a_final, b_final

# ===========================================================================
# SECTION 3: PER-PROTOCOL TRIAL FUNCTIONS
# ===========================================================================
def run_bb84_trial(num_qubits, p_noise, f_eve=0.0, device_noise_model=None, batch_size=10):
    alice_bits = np.random.randint(2, size=num_qubits)
    alice_bases = np.random.randint(2, size=num_qubits)
    bob_bases = np.random.randint(2, size=num_qubits)
    eve_presence = np.random.rand(num_qubits) < f_eve
    eve_bases = np.random.randint(2, size=num_qubits)

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
    return len(sifted_alice), errors, qber, sifted_alice, sifted_bob


def run_six_state_trial(num_qubits, p_noise, f_eve=0.0, device_noise_model=None, batch_size=10):
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
    return len(sifted_alice), errors, qber, sifted_alice, sifted_bob


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

                    if p_noise > 0 and device_noise_model is None:
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
    return abs(S), len(sifted_alice), errors, qber, sifted_alice, sifted_bob


# ===========================================================================
# SECTION 4: MONTE CARLO RUNNERS
# ===========================================================================
def monte_carlo_bb84(trials, num_qubits, p_noise=0.0, f_eve=0.0, qber_threshold=0.11, seed=None, device_noise_model=None):
    if seed is not None: np.random.seed(seed)
    qber_list, skr_list = [], []
    fp_count, fn_count = 0, 0

    for t in range(trials):
        sifted_len, errors, qber, _, _ = run_bb84_trial(num_qubits, p_noise, f_eve, device_noise_model)
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
        sifted_len, errors, qber, _, _ = run_six_state_trial(num_qubits, p_noise, f_eve, device_noise_model)
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

def monte_carlo_e91(trials, num_pairs, p_noise=0.0, f_eve=0.0, chsh_threshold=2.2, seed=None, device_noise_model=None):
    if seed is not None: np.random.seed(seed)
    s_list, qber_list, skr_list = [], [], []
    fp_count, fn_count = 0, 0

    for t in range(trials):
        S, sifted_len, errors, qber, _, _ = run_e91_trial(num_pairs, p_noise, f_eve, device_noise_model)
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

def estimate_detection_rates(protocol, trials, num_qubits, p_noise, f_eve, qber_threshold=0.11, chsh_threshold=2.2, device_noise_model=None):
    fp_count = 0
    fn_count = 0
    for t in range(trials):
        if protocol == "BB84":
            _, _, qber, _, _ = run_bb84_trial(num_qubits, p_noise, f_eve, device_noise_model)
            alarm_triggered = qber >= qber_threshold
        elif protocol == "Six-State":
            _, _, qber, _, _ = run_six_state_trial(num_qubits, p_noise, f_eve, device_noise_model)
            alarm_triggered = qber >= qber_threshold
        elif protocol == "E91":
            S, _, _, _, _, _ = run_e91_trial(num_qubits, p_noise, f_eve, device_noise_model)
            alarm_triggered = S < chsh_threshold

        if f_eve == 0.0:
            if alarm_triggered: fp_count += 1
        else:
            if not alarm_triggered: fn_count += 1

    fpr = (fp_count / trials) if f_eve == 0.0 else 0.0
    fnr = (fn_count / trials) if f_eve > 0.0 else 0.0
    return fpr, fnr

def validate_post_processing():
    """
    Validates and runs the full classical error reconciliation and 
    privacy amplification pipelines on a mock honest but noisy channel.
    (Note: Both Six-State and E91 rely on these exact same classical routines 
     for generating the final verified key.)
    """
    print("\n==========================================")
    print("      POST-PROCESSING VALIDATION")
    print("==========================================")
    p_noise = 0.02
    f_eve = 0.0
    
    sifted_len, errors, qber, sifted_alice, sifted_bob = run_bb84_trial(num_qubits=1000, p_noise=p_noise, f_eve=f_eve)
    
    match_before = (1.0 - qber) * 100
    print(f"Match percentage BEFORE reconciliation: {match_before:.2f}%")
    
    reconciled_bob_key, disclosed_bits = error_reconciliation(sifted_alice, sifted_bob)
    
    errors_after = sum(1 for a, b in zip(sifted_alice, reconciled_bob_key) if a != b)
    match_after = (1.0 - (errors_after / len(sifted_alice))) * 100 if len(sifted_alice) > 0 else 0
    print(f"Match percentage AFTER reconciliation:  {match_after:.2f}% (Disclosed bits: {disclosed_bits})")
    
    final_alice, final_bob = privacy_amplification(sifted_alice, reconciled_bob_key, disclosed_bits, qber)
    
    keys_match = (final_alice == final_bob) and len(final_alice) > 0
    print(f"Privacy amplification complete. Keys identical? {keys_match}. Final secure length: {len(final_alice)}")
    print("==========================================\n")

# ===========================================================================
# SECTION 5: SAMPLE SIZE SWEEP (K-Sweep)
# ===========================================================================
if __name__ == "__main__":
    validate_post_processing()

    BB84_QBER_THRESHOLD = 0.135       
    SIXSTATE_QBER_THRESHOLD = 0.167   
    E91_CHSH_THRESHOLD = 2.0          

    K_VALUES = [100, 200, 300, 500, 1000, 2000, 3000] 
    TRIALS = 200
    protocols = ["BB84", "Six-State", "E91"]

    csv_filename = "qkd_resource_cost.csv"
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Protocol", "K", "Trials", "FPR", "FNR"])

    print(f"Starting K-Sweep Experiment. Results will stream to {csv_filename}...")
    start_time = time.time()

    for proto in protocols:
        print(f"\n========== PROTOCOL: {proto} ==========")
        # For E91, note that smaller K implies larger variance in measured CHSH S
        # which strongly drives error detection accuracy in sparse runs.
        
        for K in K_VALUES:
            
            # Condition 1: FPR (False Positive Rate) -> f_eve = 0.0, noise near detection threshold
            p_noise_fpr = 0.10 if proto == "E91" else 0.22
            
            # Condition 2: FNR (False Negative Rate) -> f_eve = 1.0, clean channel 
            p_noise_fnr = 0.0
            
            if proto == "BB84":
                _, _, _, _, fpr_val, _ = monte_carlo_bb84(TRIALS, K, p_noise=p_noise_fpr, f_eve=0.0, qber_threshold=BB84_QBER_THRESHOLD)
                _, _, _, _, _, fnr_val = monte_carlo_bb84(TRIALS, K, p_noise=p_noise_fnr, f_eve=1.0, qber_threshold=BB84_QBER_THRESHOLD)
            
            elif proto == "Six-State":
                _, _, _, _, fpr_val, _ = monte_carlo_six_state(TRIALS, K, p_noise=p_noise_fpr, f_eve=0.0, qber_threshold=SIXSTATE_QBER_THRESHOLD)
                _, _, _, _, _, fnr_val = monte_carlo_six_state(TRIALS, K, p_noise=p_noise_fnr, f_eve=1.0, qber_threshold=SIXSTATE_QBER_THRESHOLD)
            
            elif proto == "E91":
                _, _, _, _, _, _, fpr_val, _ = monte_carlo_e91(TRIALS, K, p_noise=p_noise_fpr, f_eve=0.0, chsh_threshold=E91_CHSH_THRESHOLD)
                _, _, _, _, _, _, _, fnr_val = monte_carlo_e91(TRIALS, K, p_noise=p_noise_fnr, f_eve=1.0, chsh_threshold=E91_CHSH_THRESHOLD)
                if K <= 300:
                    print(f"  [Note: E91 K={K} pairs yield highly sparse CHSH samples, expecting elevated noise.]")

            print(f"  K={K:<5} | FPR: {fpr_val:.3f} | FNR: {fnr_val:.3f}")
            
            with open(csv_filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([proto, K, TRIALS, fpr_val, fnr_val])

    elapsed = (time.time() - start_time) / 60
    print(f"\nEXPERIMENT COMPLETE! Total elapsed time: {elapsed:.2f} minutes.")