from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_aer.noise import NoiseModel

# This will automatically find the credentials you just saved
service = QiskitRuntimeService(channel="ibm_quantum_platform")

# Find the least busy machine
backend = service.least_busy(operational=True, simulator=False)
print(f"Successfully connected to: {backend.name}")

# Extract noise model
real_noise_model = NoiseModel.from_backend(backend)
print(f"Noise model extracted from {backend.name}.")
