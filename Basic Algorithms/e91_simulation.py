from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# Create a circuit with 2 qubits and 2 classical bits
qc_e91 = QuantumCircuit(2, 2)

# Step 1: Create a Bell State (Entangled Pair)
# Apply Hadamard to Alice's qubit (qubit 0) to put it in superposition
qc_e91.h(0)

# Apply CNOT using Alice's qubit as control, and Bob's (qubit 1) as target
qc_e91.cx(0, 1)

qc_e91.barrier()

# Step 2: Alice and Bob measure their qubits in the SAME computational Z-basis
qc_e91.measure(0, 0) # Alice measures
qc_e91.measure(1, 1) # Bob measures

# Run the simulation 1000 times to see the statistical correlation
simulator = AerSimulator()
result = simulator.run(qc_e91, shots=1000).result()
counts = result.get_counts()

print("Measurement Outcomes (AliceBob : Count):")
print(counts)