from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import numpy as np

def chsh_circuit(theta_a, theta_b):
    qc = QuantumCircuit(2, 2)
    
    # 1. Create the Entangled Bell State
    qc.h(0)
    qc.cx(0, 1)
    qc.barrier()
    
    # 2. Rotate measurement bases to the specific CHSH angles
    qc.ry(theta_a, 0) # Alice rotates her measurement
    qc.ry(theta_b, 1) # Bob rotates his measurement
    qc.barrier()
    
    # 3. Measure
    qc.measure(0, 0)
    qc.measure(1, 1)
    return qc

def calculate_expectation(counts, shots):
    # Expectation value formula: E = (P(00) + P(11)) - (P(01) + P(10))
    c00 = counts.get('00', 0)
    c11 = counts.get('11', 0)
    c01 = counts.get('01', 0)
    c10 = counts.get('10', 0)
    return (c00 + c11 - c01 - c10) / shots

# The 4 standard measurement angles for the CHSH inequality
angles = {
    'A1_B1': (0, np.pi/4),
    'A1_B2': (0, 3*np.pi/4),
    'A2_B1': (np.pi/2, np.pi/4),
    'A2_B2': (np.pi/2, 3*np.pi/4)
}

simulator = AerSimulator()
shots = 1024
E = {}

print("--- Running CHSH Test ---")
for name, (theta_a, theta_b) in angles.items():
    qc = chsh_circuit(theta_a, theta_b)
    result = simulator.run(qc, shots=shots).result()
    counts = result.get_counts()
    
    # Calculate the expectation value for this pair of angles
    E[name] = calculate_expectation(counts, shots)
    print(f"Expectation {name}: {E[name]:.3f}")

# Calculate Final CHSH Parameter S
# S = E(A1,B1) - E(A1,B2) + E(A2,B1) + E(A2,B2)
S = E['A1_B1'] - E['A1_B2'] + E['A2_B1'] + E['A2_B2']

print(f"\nFINAL CHSH PARAMETER (S): {abs(S):.3f}")
if abs(S) > 2.0:
    print("Result: QUANTUM ENTANGLEMENT VERIFIED (Secure!)")
else:
    print("Result: CLASSICAL BOUNDARY NOT BROKEN (Eve detected or too much noise!)")