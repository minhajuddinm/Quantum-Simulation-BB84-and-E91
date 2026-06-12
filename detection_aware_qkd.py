import numpy as np
import math
import hashlib
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import depolarizing_error

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

def monte_carlo_bb84(trials=200, num_qubits=1000, p_noise=0.0, f_eve=0.0, seed=None, device_noise_model=None):
    if seed is not None: np.random.seed(seed)
    qber_list, skr_list = [], []
    for t in range(trials):
        sifted_len, errors, qber = run_bb84_trial(num_qubits, p_noise, f_eve, device_noise_model)
        skr = secure_key_rate(num_qubits, sifted_len, qber)
        qber_list.append(qber)
        skr_list.append(skr)
    return np.mean(qber_list), np.std(qber_list), np.mean(skr_list), np.std(skr_list)

def monte_carlo_six_state(trials=200, num_qubits=1000, p_noise=0.0, f_eve=0.0, seed=None, device_noise_model=None):
    if seed is not None: np.random.seed(seed)
    qber_list, skr_list = [], []
    for t in range(trials):
        sifted_len, errors, qber = run_six_state_trial(num_qubits, p_noise, f_eve, device_noise_model)
        skr = secure_key_rate(num_qubits, sifted_len, qber)
        qber_list.append(qber)
        skr_list.append(skr)
    return np.mean(qber_list), np.std(qber_list), np.mean(skr_list), np.std(skr_list)

def monte_carlo_e91(trials=50, num_pairs=8192, p_noise=0.0, f_eve=0.0, seed=None, device_noise_model=None):
    if seed is not None: np.random.seed(seed)
    s_list, qber_list, skr_list = [], [], []
    for t in range(trials):
        S, sifted_len, errors, qber = run_e91_trial(num_pairs, p_noise, f_eve, device_noise_model)
        skr = secure_key_rate(num_pairs, sifted_len, qber)
        s_list.append(S)
        qber_list.append(qber)
        skr_list.append(skr)
    return np.mean(s_list), np.std(s_list), np.mean(qber_list), np.std(qber_list), np.mean(skr_list), np.std(skr_list)

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
if __name__ == "__main__":
    import csv
    import time
    from qiskit_ibm_runtime import QiskitRuntimeService
    from qiskit_aer.noise import NoiseModel

    print("Fetching IBM hardware noise model...")
    service = QiskitRuntimeService(channel="ibm_quantum_platform")
    backend = service.backend("ibm_marrakesh") 
    real_noise_model = NoiseModel.from_backend(backend)
    print("Noise model loaded successfully!\n")

    # ==========================================
    # OVERNIGHT RUN PARAMETERS
    # ==========================================
    TRIALS = 50           # Monte Carlo trials per data point
    STD_QUBITS = 1000     # Key length for BB84 and Six-State
    E91_PAIRS = 8192      # Pairs needed for accurate CHSH statistics
    
    QBER_THRESHOLD = 0.11 # 11% abort threshold
    CHSH_THRESHOLD = 2.2  # Margin above 2.0 to account for hardware noise

    protocols = ["BB84", "Six-State", "E91"]
    
    noise_profiles = {
        "Ideal": {"p_noise": 0.0, "model": None},
        "Low_Noise": {"p_noise": 0.05, "model": None},
        "Threshold_Noise": {"p_noise": 0.22, "model": None},
        "IBM_Marrakesh": {"p_noise": 0.0, "model": real_noise_model}
    }
    
    f_eve_sweep = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

    # Initialize CSV
    csv_filename = "qkd_results.csv"
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write CSV Header
        writer.writerow(["Protocol", "Noise_Profile", "F_Eve", "Mean_QBER_or_S", "Std_QBER_or_S", "Mean_SKR", "Std_SKR", "FPR", "FNR"])

    print(f"Starting Full Experiment Sweep. Results will stream to {csv_filename}...")
    start_time = time.time()

    # Master Execution Loop
    for proto in protocols:
        print(f"\n========== RUNNING PROTOCOL: {proto} ==========")
        num_q = E91_PAIRS if proto == "E91" else STD_QUBITS

        for noise_name, params in noise_profiles.items():
            print(f"  -> Noise Profile: {noise_name}")
            p = params["p_noise"]
            model = params["model"]

            for f in f_eve_sweep:
                # 1. Run Monte Carlo for Key Rates and QBER/S
                if proto == "BB84":
                    mq, sq, mskr, sskr = monte_carlo_bb84(TRIALS, num_q, p, f, None, model)
                elif proto == "Six-State":
                    mq, sq, mskr, sskr = monte_carlo_six_state(TRIALS, num_q, p, f, None, model)
                elif proto == "E91":
                    ms, ss, mq, sq, mskr, sskr = monte_carlo_e91(TRIALS, num_q, p, f, None, model)
                    mq, sq = ms, ss # For E91, we track S as the primary detection metric in the CSV

                # 2. Run Estimator for FPR and FNR
                fpr, fnr = estimate_detection_rates(proto, TRIALS, num_q, p, f, QBER_THRESHOLD, CHSH_THRESHOLD, model)

                # 3. Log to Console & Append to CSV
                print(f"      f={f:.1f} | Metric: {mq:.4f} | SKR: {mskr:.4f} | FPR: {fpr:.2f} | FNR: {fnr:.2f}")
                
                with open(csv_filename, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([proto, noise_name, f, mq, sq, mskr, sskr, fpr, fnr])

    elapsed = (time.time() - start_time) / 60
    print(f"\nEXPERIMENT COMPLETE! Total elapsed time: {elapsed:.2f} minutes.")
    print(f"All data saved to {csv_filename}. You are ready to plot your figures!")