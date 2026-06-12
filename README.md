# Noise-Aware Simulation and Comparison of BB84, Six-State, and E91 QKD Protocols

This repository contains the simulation framework for the research project analyzing Quantum Key Distribution (QKD) protocols under realistic noise and partial-interception eavesdropping attacks. 

The framework is built using IBM's Qiskit and evaluates three distinct protocols:
1. **BB84** (Prepare-and-Measure, 2 Bases)
2. **Six-State** (Prepare-and-Measure, 3 Bases)
3. **E91** (Entanglement-Based)

The simulation extracts exact error rates (QBER), Secure Key Rates (SKR), False Positive Rates (FPR), and False Negative Rates (FNR) to quantify the stealth-versus-efficiency tradeoff of partial eavesdroppers across both synthetic channel noise and real quantum hardware noise (`ibm_marrakesh`).

## 📁 Repository Contents

* `detection_aware_qkd.py`: The master simulation pipeline. It includes the unified environment, the mathematical post-processing (Error Reconciliation & Privacy Amplification limits), the Monte Carlo batched runners, and the final CSV data generator.
* `ibm_noise_fetch.py`: A utility script to verify the connection to IBM Quantum Platform and extract the hardware noise profile.
* `README.md`: This setup and execution guide.

---

## ⚙️ Installation and Setup

### 1. Prerequisites
Ensure you have Python 3.8+ installed. It is recommended to use a virtual environment.

Install the required quantum computing libraries:
```bash
pip install qiskit qiskit-aer qiskit-ibm-runtime numpy

```

### 2. IBM Quantum API Configuration (CRITICAL)

To pull real hardware noise, you must link your local environment to an IBM Quantum account. **Never hardcode your API key into scripts that you push to public repositories.**

1. Create a free account at the [IBM Quantum Platform](https://quantum.ibm.com/).
2. Copy your unique API Token from the dashboard.
3. Open your local Python terminal or create a temporary script containing the code below.
4. Replace `"PASTE_YOUR_API_KEY_HERE"` with your actual token.
5. Run the script **once**, and then delete the file. This safely saves your credentials to your machine's hidden configuration files.

```python
from qiskit_ibm_runtime import QiskitRuntimeService

# Run this ONE TIME on your local machine to save your credentials securely
QiskitRuntimeService.save_account(
    channel="ibm_quantum_platform", 
    token="PASTE_YOUR_API_KEY_HERE", 
    overwrite=True
)
print("Account successfully saved to your local machine.")

```

6. You can verify your connection is working by running:

```bash
python ibm_noise_fetch.py

```

If successful, it will print the name of the real quantum computer it connected to (e.g., `ibm_marrakesh`).

---

## 🚀 Running the Master Experiment

Once the setup is complete, you can generate the core dataset.

The main script is configured to run a highly intensive, batched Monte Carlo simulation testing thousands of qubits under varying noise channels and eavesdropper fractions (f = 0.0 to 1.0).

```bash
python detection_aware_qkd.py

```

### What to Expect:

Because extracting the full density matrix for hardware noise requires substantial CPU overhead, the script batches independent qubits (in groups of 10) to bypass memory limits.

The console will stream the results live:

```text
========== RUNNING PROTOCOL: BB84 ==========
  -> Noise Profile: Ideal
      f=0.0 | Metric: 0.0000 | SKR: 0.5010 | FPR: 0.00 | FNR: 0.00
      f=0.2 | Metric: 0.0515 | SKR: 0.2085 | FPR: 0.00 | FNR: 1.00

```

As it processes, it automatically appends the calculated metrics to **`qkd_results.csv`**.

*Note: Depending on the configured `TRIALS` variable inside the script, a full parametric sweep across all three protocols can take several hours to complete.*
