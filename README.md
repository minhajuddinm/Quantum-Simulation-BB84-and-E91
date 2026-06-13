# Noise-Aware Simulation and Statistical Eavesdropping Detection in BB84, Six-State, and E91 QKD Protocols

This repository contains the Qiskit simulation framework for a comparative study of three Quantum Key Distribution (QKD) protocols under channel noise and a partial intercept-and-resend eavesdropper. For each protocol it measures how reliably an eavesdropper is detected and what that detection costs in usable key.

The three protocols are:

1. **BB84** (prepare-and-measure, two bases)
2. **Six-State** (prepare-and-measure, three bases)
3. **E91** (entanglement-based, CHSH test)

For each protocol the framework records the error indicator (the QBER for the two prepare-and-measure protocols, the CHSH value `S` for E91), the secure key rate (SKR), and the two statistical detection metrics, the false positive rate (FPR) and the false negative rate (FNR). The eavesdropper is parameterized by an interception fraction `f` between 0 and 1, so that the same intercept-and-resend attack can range from absent to full. Every protocol is run under both a synthetic depolarizing channel and a real-hardware noise model extracted from the `ibm_marrakesh` backend.

---

## 📁 Repository Structure

```
.
├── detection_aware_qkd_varying_eve.py   # Experiment 1: sweep over interception fraction f
├── detection_aware_qkd_sample_size.py   # Experiment 2: sweep over sample size K
├── detection_aware_qkd_original.py      # Original combined experiment script (writes qkd_results.csv)
├── ibm_noise_fetch.py                   # Utility: verify IBM Quantum connection & extract noise
├── qkd_varying_eve.csv                  # Output data from Experiment 1
├── qkd_resource_cost.csv                # Output data from Experiment 2
├── README.md                            # This setup and execution guide
│
├── figures/                             # Generated figures and figure scripts
│   ├── results_fig.py                   # Result figures from CSV data (5 plots)
│   ├── fig.py                           # Conceptual & circuit figures (7 plots)
│   ├── fig_pipe.py                      # Methodology pipeline figure
│   └── *.pdf / *.svg / *.png            # Generated figure outputs
│
├── Basic Algorithms/                    # Standalone introductory scripts
│   ├── bb84_simulation.py               # Basic BB84 (no noise, no Eve)
│   ├── bb84_eve_simulation.py           # BB84 with full eavesdropper
│   ├── bb84_noise_simulation.py         # BB84 with depolarizing noise
│   ├── e91_simulation.py                # Basic E91 Bell pair demonstration
│   └── e91_chsh_simulation.py           # E91 with full CHSH test
│
└── Old/                                 # Archived earlier versions
    ├── detection_aware_qkd_old_threshold.py
    └── qkd_results_old_threshold.csv
```

### Key files

| File | Description |
| --- | --- |
| `detection_aware_qkd_varying_eve.py` | Main sweep over the interception fraction `f` for all three protocols and noise profiles. Generates `qkd_varying_eve.csv`. |
| `detection_aware_qkd_sample_size.py` | Sample-size sweep that measures how detection scales with the number of compared signals `K`. Generates `qkd_resource_cost.csv`. |
| `detection_aware_qkd_original.py` | The original monolithic experiment script combining both experiments; writes to `qkd_results.csv`. Retained for reference. |
| `figures/results_fig.py` | Reads `qkd_varying_eve.csv` and `qkd_resource_cost.csv` from the project root and regenerates the five result figures (PDF, SVG, and PNG) into the `figures/` folder. |
| `figures/fig.py` | Generates the seven conceptual and circuit-diagram figures for the paper (system model, detection decision, BB84/Six-State/E91 circuits, Bloch-sphere bases, and intro overview). |
| `figures/fig_pipe.py` | Generates the methodology pipeline diagram. |
| `ibm_noise_fetch.py` | Utility that verifies the connection to the IBM Quantum Platform and extracts the hardware noise profile. |

### Basic Algorithms

The `Basic Algorithms/` folder contains five standalone scripts that each demonstrate a single concept in isolation. They are not required for the main experiments but serve as learning aids:

| File | Description |
| --- | --- |
| `bb84_simulation.py` | Minimal BB84: encoding, measurement, sifting, and QBER on an ideal channel. |
| `bb84_eve_simulation.py` | BB84 with a full intercept-and-resend eavesdropper (no noise). |
| `bb84_noise_simulation.py` | BB84 with a depolarizing noise model applied to gates. |
| `e91_simulation.py` | Basic E91 Bell-pair creation and measurement correlation. |
| `e91_chsh_simulation.py` | Full CHSH inequality test on entangled pairs. |

Both main simulation scripts share the same building blocks: the unified protocol environment, the secure-key-rate math, the classical post-processing (error reconciliation and privacy amplification), and the batched Monte Carlo runners.

---

## ⚙️ Installation and Setup

### 1. Prerequisites

Use Python 3.8 or newer, ideally in a virtual environment. Install the required libraries:

```bash
pip install qiskit qiskit-aer qiskit-ibm-runtime numpy matplotlib pandas
```

`matplotlib` and `pandas` are needed only by the figure scripts; the simulation scripts themselves require only `qiskit`, `qiskit-aer`, `qiskit-ibm-runtime`, and `numpy`.

### 2. IBM Quantum API Configuration

The device noise profile is pulled from real IBM hardware, so the `IBM_Marrakesh` runs require a linked IBM Quantum account. **Never hardcode your API token into scripts that are pushed to a public repository.**

1. Create a free account at the [IBM Quantum Platform](https://quantum.ibm.com/).
2. Copy your API token from the dashboard.
3. In a local Python session or a temporary script, run the code below with your token in place of `PASTE_YOUR_API_KEY_HERE`.
4. Run it **once**, then delete the file. This stores your credentials in your machine's hidden configuration so the scripts can authenticate without the token appearing in code.

```python
from qiskit_ibm_runtime import QiskitRuntimeService

# Run this ONE TIME on your local machine to save your credentials securely.
QiskitRuntimeService.save_account(
    channel="ibm_quantum_platform",
    token="PASTE_YOUR_API_KEY_HERE",
    overwrite=True,
)
print("Account successfully saved to your local machine.")
```

5. Verify the connection:

```bash
python ibm_noise_fetch.py
```

On success it prints the name of the backend it connected to (for example, `ibm_marrakesh`).

If you only need the synthetic-noise results, the IBM account is optional: the synthetic profiles run entirely on the local Aer simulator.

---

## 🚀 Running the Experiments

There are two independent experiments. Each streams progress to the console and appends results to its own CSV.

### Experiment 1: Varying the attacker fraction

```bash
python detection_aware_qkd_varying_eve.py
```

This sweeps the interception fraction `f` across every protocol and noise profile and writes `qkd_varying_eve.csv`. It produces the detection-signal, stealth-window, tradeoff, noise-robustness, and device-noise results.

### Experiment 2: Varying the sample size

```bash
python detection_aware_qkd_sample_size.py
```

This sweeps the number of compared signals `K` and writes `qkd_resource_cost.csv`, which gives the resource-cost results (how many signals are needed to drive the FPR and FNR down).

### Console output

Both scripts begin with a post-processing validation block and a set of sanity checks against the known analytic limits, then stream results live, for example:

```text
========== RUNNING PROTOCOL: BB84 ==========
  -> Noise Profile: Ideal_0%
      f=0.00 | Metric: 0.0000 | SKR: 0.4980 | FPR: 0.00 | FNR: 0.00
      f=0.20 | Metric: 0.0480 | SKR: 0.2240 | FPR: 0.00 | FNR: 1.00
```

`Metric` is the QBER for BB84 and Six-State and the CHSH value `S` for E91.

---

## 📊 Reproducing the Figures

### Result figures

After both CSV files exist, regenerate the five result figures used in the paper:

```bash
python figures/results_fig.py
```

It reads `qkd_varying_eve.csv` and `qkd_resource_cost.csv` from the current directory and writes the following into the `figures/` folder, each as PDF, SVG, and PNG:

| Figure | Content |
| --- | --- |
| `fig_metric_vs_f` | Detection signal (QBER and CHSH `S`) versus attack fraction. |
| `fig_tradeoff` | False negative rate and secure key rate versus attack fraction (the stealth window). |
| `fig_fpr_vs_noise` | False positive rate versus synthetic channel noise. |
| `fig_device` | Honest key rate and detection under the `ibm_marrakesh` device model. |
| `fig_resource_cost` | False positive and false negative rates versus the number of compared signals. |

### Conceptual and circuit figures

```bash
python figures/fig.py
```

This generates seven figures (each as PDF, SVG, and PNG) in the `figures/` folder:

| Figure | Content |
| --- | --- |
| `fig_system_model` | System model diagram: Alice, Eve, Bob, and the two channels. |
| `fig_detection_decision` | Detection-decision illustration showing FPR/FNR regions for BB84 and E91. |
| `fig_circuit_bb84` | Circuit diagram for the BB84 protocol. |
| `fig_circuit_sixstate` | Circuit diagram for the Six-State protocol. |
| `fig_circuit_e91` | Circuit diagram for the E91 protocol. |
| `fig_basis_mub` | Bloch-sphere comparison of BB84 (2 bases) vs Six-State (3 bases). |
| `fig_intro_overview` | Overview card for all three protocols at a glance. |

### Pipeline figure

```bash
python figures/fig_pipe.py
```

| Figure | Content |
| --- | --- |
| `fig_pipeline` | Methodology pipeline: circuit construction → noise → Eve → sifting → reconciliation → privacy amplification → detection stats. |

---

## 🔧 Experiment Configuration

The key parameters are set near the top of each script's main block.

**Detection thresholds**

| Protocol | Indicator | Alarm condition |
| --- | --- | --- |
| BB84 | QBER | `QBER >= 0.135` |
| Six-State | QBER | `QBER >= 0.167` |
| E91 | CHSH `S` | `S < 2.0` |

**Synthetic noise profiles** (depolarizing strength `p`; the honest QBER is approximately `p/2`)

| Profile | `p` | Approx. honest QBER |
| --- | --- | --- |
| `Ideal_0%` | 0.00 | 0% |
| `Noise_2%` | 0.04 | 2% |
| `Noise_5%` | 0.10 | 5% |
| `Noise_8%` | 0.16 | 8% |
| `Threshold_11%` | 0.22 | 11% |
| `IBM_Marrakesh` | device model | hardware-defined |

**Sweep settings**

* `detection_aware_qkd_varying_eve.py`: 50 trials per synthetic point and 30 per device point; 1000 qubits per trial for BB84 and Six-State and 8192 entangled pairs for E91 (200 qubits or 1024 pairs on the device); `f` from 0.0 to 1.0 in steps of 0.1 for the synthetic channels and {0, 0.25, 0.5, 0.75, 1.0} on the device.
* `detection_aware_qkd_sample_size.py`: 200 trials per point; `K` in {100, 200, 300, 500, 1000, 2000, 3000}. The FPR is measured on an honest noisy channel held at an 11% error rate (`p=0.22`) for BB84 and Six-State and at 5% (`p=0.10`) for E91, so each protocol is stressed near its own marginal-honest regime; the FNR is measured against a full attacker (`f = 1`) on a clean channel.

To keep memory use bounded when sampling hardware noise, the prepare-and-measure runners batch independent qubits in groups of 10. Depending on the trial counts above, a full sweep across all three protocols can take several hours.

---

## 🗃️ Output Data Schema

**`qkd_varying_eve.csv`**

`Protocol, Noise_Profile, F_Eve, QBER_Threshold, CHSH_Threshold, Mean_Metric, Std_Metric, Mean_SKR, Std_SKR, FPR, FNR`

`Mean_Metric` is the mean QBER for BB84 and Six-State and the mean CHSH `S` for E91. `FPR` is populated only on honest rows (`F_Eve = 0`) and `FNR` only on attacked rows (`F_Eve > 0`).

**`qkd_resource_cost.csv`**

`Protocol, K, Trials, FPR, FNR`

`K` is the number of compared signals (qubits or entangled pairs) per trial.