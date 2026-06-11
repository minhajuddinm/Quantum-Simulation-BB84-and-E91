from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import numpy as np

# 1. UPGRADED CIRCUIT GENERATOR (Now with Eve!)
def generate_bb84_states(num_qubits, eavesdropper_present=False):
    alice_bits = np.random.randint(2, size=num_qubits)
    alice_bases = np.random.randint(2, size=num_qubits)
    bob_bases = np.random.randint(2, size=num_qubits)
    eve_bases = np.random.randint(2, size=num_qubits)
    
    qc = QuantumCircuit(num_qubits, num_qubits)
    
    # ALICE ENCODING
    for i in range(num_qubits):
        if alice_bits[i] == 1:
            qc.x(i)
        if alice_bases[i] == 1:
            qc.h(i)
            
    qc.barrier()
    
    # EVE INTERCEPTION
    if eavesdropper_present:
        for i in range(num_qubits):
            if eve_bases[i] == 1:
                qc.h(i)
            qc.measure(i, i) # Eve measures
            
            if eve_bases[i] == 1:
                qc.h(i) # Eve prepares the state to send to Bob
        qc.barrier()
    
    # BOB MEASUREMENT
    for i in range(num_qubits):
        if bob_bases[i] == 1:
            qc.h(i)
        qc.measure(i, i)
        
    return qc, alice_bits, alice_bases, bob_bases

# 2. SIFTING FUNCTION (with the integer fix)
def sift_keys(alice_bits, alice_bases, bob_bases, bob_measured_bits):
    sifted_key_alice = []
    sifted_key_bob = []
    for i in range(len(alice_bases)):
        if alice_bases[i] == bob_bases[i]:
            sifted_key_alice.append(int(alice_bits[i]))
            sifted_key_bob.append(int(bob_measured_bits[i]))
    return sifted_key_alice, sifted_key_bob

# 3. RUN THE SIMULATION (Testing 1024 qubits with Eve)
num_qubits = 1024

# Generate circuit WITH Eve turned on
qc_eve, alice_bits, alice_bases, bob_bases = generate_bb84_states(num_qubits, eavesdropper_present=True)

# Run ideal simulation (no hardware noise, only Eve's disturbance)
simulator = AerSimulator()
result_eve = simulator.run(qc_eve, shots=1).result()
counts_eve = result_eve.get_counts()
measured_bits_eve = list(counts_eve.keys())[0][::-1]

# Sift the keys
alice_key_eve, bob_key_eve = sift_keys(
    alice_bits, 
    alice_bases, 
    bob_bases, 
    [int(b) for b in measured_bits_eve]
)

# Calculate QBER caused by Eve
errors_eve = sum(1 for i in range(len(alice_key_eve)) if alice_key_eve[i] != bob_key_eve[i])
qber_eve = (errors_eve / len(alice_key_eve)) if len(alice_key_eve) > 0 else 0.0

print("\n--- EAVESDROPPER RESULTS ---")
print(f"Total Sifted Bits: {len(alice_key_eve)}")
print(f"Errors caused by Eve: {errors_eve}")
print(f"Eve QBER: {qber_eve * 100}%")