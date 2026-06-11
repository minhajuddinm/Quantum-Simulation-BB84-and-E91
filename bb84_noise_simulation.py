from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import numpy as np

def generate_bb84_states(num_qubits):
    # Alice generates random bits and random bases (0 for Z, 1 for X)
    alice_bits = np.random.randint(2, size=num_qubits)
    alice_bases = np.random.randint(2, size=num_qubits)
    
    # Bob generates random measurement bases
    bob_bases = np.random.randint(2, size=num_qubits)
    
    qc = QuantumCircuit(num_qubits, num_qubits)
    
    # Alice's Encoding
    for i in range(num_qubits):
        if alice_bits[i] == 1:
            qc.x(i) # Bit flip for state |1>
        if alice_bases[i] == 1:
            qc.h(i) # Change to X basis
            
    qc.barrier()
    
    # Quantum Channel (Noise will be injected here later)
    
    qc.barrier()
    
    # Bob's Measurement
    for i in range(num_qubits):
        if bob_bases[i] == 1:
            qc.h(i) # Change to X basis for measurement
        qc.measure(i, i)
        
    return qc, alice_bits, alice_bases, bob_bases

# Example execution
num_qubits = 100
qc, alice_bits, alice_bases, bob_bases = generate_bb84_states(num_qubits)

# Run simulation
simulator = AerSimulator()
result = simulator.run(qc, shots=1).result()
counts = result.get_counts()
measured_bits = list(counts.keys())[0][::-1] # Reverse string to match qubit order

print("Alice Bits:  ", alice_bits)
print("Alice Bases: ", alice_bases)
print("Bob Bases:   ", bob_bases)
print("Bob Measured:", [int(b) for b in measured_bits])

def sift_keys(alice_bits, alice_bases, bob_bases, bob_measured_bits):
    sifted_key_alice = []
    sifted_key_bob = []
    
    # Compare bases and keep bits where bases match
    for i in range(len(alice_bases)):
        if alice_bases[i] == bob_bases[i]:
            # Use int() to convert from np.int32 to standard Python integer
            sifted_key_alice.append(int(alice_bits[i]))
            sifted_key_bob.append(int(bob_measured_bits[i]))
            
    return sifted_key_alice, sifted_key_bob
    
# Run the sifting process (using the variables from your previous code block)
alice_key, bob_key = sift_keys(alice_bits, alice_bases, bob_bases, [int(b) for b in measured_bits])

print("\n--- SIFTING PHASE ---")
print("Alice's Sifted Key:", alice_key)
print("Bob's Sifted Key:  ", bob_key)

# Calculate Quantum Bit Error Rate (QBER)
errors = 0
for i in range(len(alice_key)):
    if alice_key[i] != bob_key[i]:
        errors += 1

if len(alice_key) > 0:
    qber = errors / len(alice_key)
else:
    qber = 0.0

print(f"Errors in sifted key: {errors}")
print(f"Baseline QBER: {qber * 100}%")
from qiskit_aer.noise import NoiseModel, depolarizing_error

# 1. Define the noise model
noise_model = NoiseModel()

# Create a depolarizing error probability of 5% (0.05)
error_prob = 0.05
error_gate = depolarizing_error(error_prob, 1) # 1 specifies a single-qubit error

# Apply this error to the basic gates used in your BB84 circuit
noise_model.add_all_qubit_quantum_error(error_gate, ['x', 'h'])

# 2. Run the simulation using the new noise model
noisy_simulator = AerSimulator(noise_model=noise_model)
noisy_result = noisy_simulator.run(qc, shots=1).result()
noisy_counts = noisy_result.get_counts()

# Extract the noisy measured bits
noisy_measured_bits = list(noisy_counts.keys())[0][::-1]

# 3. Run the sifting process on the noisy data
noisy_alice_key, noisy_bob_key = sift_keys(
    alice_bits, 
    alice_bases, 
    bob_bases, 
    [int(b) for b in noisy_measured_bits]
)

# Calculate the new Noisy QBER
noisy_errors = 0
for i in range(len(noisy_alice_key)):
    if noisy_alice_key[i] != noisy_bob_key[i]:
        noisy_errors += 1

noisy_qber = (noisy_errors / len(noisy_alice_key)) if len(noisy_alice_key) > 0 else 0.0

print("\n--- NOISY CHANNEL RESULTS ---")
print(f"Total Sifted Bits: {len(noisy_alice_key)}")
print(f"Errors in noisy key: {noisy_errors}")
print(f"Noisy QBER: {noisy_qber * 100}%")