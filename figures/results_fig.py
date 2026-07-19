"""
Results figures for the QKD paper. Reads qkd_varying_eve.csv and
qkd_resource_cost.csv from the current folder and writes PDF + SVG + PNG into
a local 'figures' folder. Rerun after the CSVs change and the figures refresh.
Run: python results_figures.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "mathtext.fontset": "cm",
    "axes.linewidth": 0.8, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
})
C = {"BB84": "#2c6fbb", "Six-State": "#3a8a5f", "E91": "#9a6db0"}
M = {"BB84": "o", "Six-State": "s", "E91": "^"}
GREY = "#777777"
CSV_DIR = "."
OUT = "figures"
os.makedirs(OUT, exist_ok=True)

ve = pd.read_csv(os.path.join(CSV_DIR, "qkd_varying_eve.csv"))
rc = pd.read_csv(os.path.join(CSV_DIR, "qkd_resource_cost.csv"))
PROT = ["BB84", "Six-State", "E91"]

# --- E91 threshold-dependent outputs under the noise-calibrated S* -----------
# BB84 and six-state curves still come from ve / rc above (untouched, fixed-QBER
# thresholds). Only the E91 DETECTION curves (FNR-vs-f, and FPR/FNR-vs-K) are
# re-read from the calibrated-S* sweeps. E91 SKR and CHSH signal stay in ve.
e91_cal = pd.read_csv(os.path.join(CSV_DIR, "qkd_e91_calibrated.csv"))          # FNR-vs-f under S*
e91_rc = pd.read_csv(os.path.join(CSV_DIR, "qkd_e91_resource_cost_calibrated.csv"))  # FPR/FNR-vs-K under S*

def e91_fnr_vs_f(profile):
    d = e91_cal[e91_cal.Noise_Profile == profile].sort_values("F_Eve")
    return d.F_Eve.values, d.FNR.values

def series(proto, profile="Ideal_0%"):
    return ve[(ve.Protocol == proto) & (ve.Noise_Profile == profile)].sort_values("F_Eve")

def honest(proto, profile, col):
    r = ve[(ve.Protocol == proto) & (ve.Noise_Profile == profile) & (ve.F_Eve == 0.0)]
    return r[col].values[0]

def save(fig, name):
    fig.savefig(f"{OUT}/{name}.pdf"); fig.savefig(f"{OUT}/{name}.svg")
    fig.savefig(f"{OUT}/{name}.png", dpi=200); plt.close(fig)


def metric_vs_f():
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.9))
    for p, thr in [("BB84", 0.135), ("Six-State", 0.167)]:
        d = series(p)
        ax[0].plot(d.F_Eve, d.Mean_Metric, color=C[p], marker=M[p], ms=3.5, lw=1.4, label=p)
        ax[0].fill_between(d.F_Eve, d.Mean_Metric - d.Std_Metric, d.Mean_Metric + d.Std_Metric,
                           color=C[p], alpha=0.12, lw=0)
        ax[0].axhline(thr, color=C[p], ls="--", lw=0.9)
    ax[0].text(0.02, 0.135, " 0.135", color=C["BB84"], fontsize=6.5, va="bottom")
    ax[0].text(0.02, 0.167, " 0.167", color=C["Six-State"], fontsize=6.5, va="bottom")
    ax[0].set_xlabel("interception fraction $f$"); ax[0].set_ylabel("QBER")
    ax[0].set_title("(a) QBER vs attack fraction", fontsize=8)
    ax[0].legend(fontsize=7, frameon=False, loc="lower right"); ax[0].tick_params(labelsize=7.5)
    ax[0].set_xlim(0, 1)
    d = series("E91")
    ax[1].plot(d.F_Eve, d.Mean_Metric, color=C["E91"], marker=M["E91"], ms=3.5, lw=1.4, label="E91")
    ax[1].fill_between(d.F_Eve, d.Mean_Metric - d.Std_Metric, d.Mean_Metric + d.Std_Metric,
                       color=C["E91"], alpha=0.12, lw=0)
    ax[1].axhline(2.0, color="#444", ls="--", lw=0.9); ax[1].text(0.02, 2.0, " $S=2$", fontsize=6.8, va="bottom")
    ax[1].axhline(2*np.sqrt(2), color=GREY, ls=":", lw=0.8)
    ax[1].text(0.60, 2.83, "Tsirelson $2\\sqrt{2}$", fontsize=6.3, color=GREY, va="bottom")
    ax[1].set_xlabel("interception fraction $f$"); ax[1].set_ylabel("CHSH $S$")
    ax[1].set_title("(b) CHSH $S$ vs attack fraction (E91)", fontsize=8)
    ax[1].set_xlim(0, 1); ax[1].tick_params(labelsize=7.5)
    fig.tight_layout(); save(fig, "fig_metric_vs_f")


def tradeoff():
    fig, ax = plt.subplots(2, 1, figsize=(5.2, 4.4), sharex=True)
    for p in PROT:
        d = series(p)
        if p == "E91":
            xf, yfnr = e91_fnr_vs_f("Ideal_0%")   # FNR under calibrated S*_ideal = 2.124
            ax[0].plot(xf, yfnr, color=C[p], marker=M[p], ms=3.5, lw=1.4, label=p)
        else:
            ax[0].plot(d.F_Eve, d.FNR, color=C[p], marker=M[p], ms=3.5, lw=1.4, label=p)
        ax[1].plot(d.F_Eve, d.Mean_SKR, color=C[p], marker=M[p], ms=3.5, lw=1.4, label=p)
    for a in ax:
        a.axvspan(0.0, 0.3, color=GREY, alpha=0.10, lw=0)
    ax[0].text(0.15, 0.5, "stealth\nwindow", ha="center", va="center", fontsize=7, color=GREY)
    ax[0].axhline(0.5, color=GREY, ls=":", lw=0.8)
    ax[0].set_ylabel("FNR (missed detection)"); ax[0].set_ylim(-0.05, 1.08)
    ax[0].set_title("(a) detection miss rate vs attack fraction", fontsize=8)
    ax[0].legend(fontsize=7, frameon=False, loc="center right"); ax[0].tick_params(labelsize=7.5)
    ax[1].set_ylabel("secure key rate"); ax[1].set_xlabel("interception fraction $f$")
    ax[1].set_title("(b) secure key rate vs attack fraction", fontsize=8)
    ax[1].tick_params(labelsize=7.5); ax[1].set_xlim(0, 1)
    fig.tight_layout(); save(fig, "fig_tradeoff")


def fpr_vs_noise():
    prof = [("Ideal_0%", 0), ("Noise_2%", 2), ("Noise_5%", 5), ("Noise_8%", 8), ("Threshold_11%", 11)]
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    for p in PROT:
        xs, ys = [], []
        for name, lvl in prof:
            r = ve[(ve.Protocol == p) & (ve.Noise_Profile == name) & (ve.F_Eve == 0.0)]
            if len(r): xs.append(lvl); ys.append(r.FPR.values[0])
        ax.plot(xs, ys, color=C[p], marker=M[p], ms=4, lw=1.4, label=p)
    ax.set_xlabel("synthetic channel noise level (%)"); ax.set_ylabel("FPR (false alarm rate)")
    ax.set_title("False alarms on an honest channel", fontsize=8.5)
    ax.legend(fontsize=7.5, frameon=False, loc="upper left"); ax.tick_params(labelsize=7.5)
    ax.set_ylim(-0.05, 1.08)
    fig.tight_layout(); save(fig, "fig_fpr_vs_noise")


def resource_cost():
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.9))
    for p in PROT:
        # E91 K-sweep re-read under calibrated S* (FPR@S*_5%, FNR@S*_ideal);
        # BB84/six-state stay on their published fixed-QBER-threshold rows.
        d = e91_rc[e91_rc.Protocol == "E91"].sort_values("K") if p == "E91" \
            else rc[rc.Protocol == p].sort_values("K")
        ax[0].plot(d.K, d.FPR, color=C[p], marker=M[p], ms=4, lw=1.4, label=p)
        ax[1].plot(d.K, d.FNR, color=C[p], marker=M[p], ms=4, lw=1.4, label=p)
    for a in ax:
        a.set_xscale("log"); a.axhline(0.05, color=GREY, ls=":", lw=0.8)
        a.set_xlabel("compared signals $K$"); a.tick_params(labelsize=7.5)
    ax[0].text(110, 0.065, "5%", fontsize=6.5, color=GREY)
    ax[0].set_ylabel("FPR"); ax[0].set_title("(a) false alarms vs sample size", fontsize=8)
    ax[1].set_ylabel("FNR"); ax[1].set_title("(b) missed full attacker vs sample size", fontsize=8)
    ax[0].legend(fontsize=7, frameon=False); ax[0].set_ylim(-0.02, 0.30); ax[1].set_ylim(-0.01, 0.14)
    fig.tight_layout(); save(fig, "fig_resource_cost")


def device_noise():
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.9))
    ideal = [honest(p, "Ideal_0%", "Mean_SKR") for p in PROT]
    dev = [honest(p, "IBM_Marrakesh", "Mean_SKR") for p in PROT]
    x = np.arange(3); w = 0.36
    ax[0].bar(x - w/2, ideal, w, label="ideal", color="#cfcfcf", edgecolor="k", lw=0.6)
    ax[0].bar(x + w/2, dev, w, label="ibm_marrakesh", color="#6a9fd0", edgecolor="k", lw=0.6)
    ax[0].set_xticks(x); ax[0].set_xticklabels(PROT, fontsize=7.5)
    ax[0].set_ylabel("honest secure key rate")
    ax[0].set_title("(a) honest key rate: ideal vs device", fontsize=8)
    ax[0].legend(fontsize=7, frameon=False); ax[0].tick_params(labelsize=7.5)
    for p in PROT:
        if p == "E91":
            xf, yfnr = e91_fnr_vs_f("IBM_Marrakesh")   # FNR under calibrated S*_marrakesh = 2.048
            ax[1].plot(xf, yfnr, color=C[p], marker=M[p], ms=4, lw=1.4, label=p)
        else:
            d = series(p, "IBM_Marrakesh")
            ax[1].plot(d.F_Eve, d.FNR, color=C[p], marker=M[p], ms=4, lw=1.4, label=p)
    ax[1].axhline(0.5, color=GREY, ls=":", lw=0.8)
    ax[1].set_xlabel("interception fraction $f$"); ax[1].set_ylabel("FNR")
    ax[1].set_title("(b) detection on ibm_marrakesh", fontsize=8)
    ax[1].legend(fontsize=7, frameon=False, loc="upper right"); ax[1].tick_params(labelsize=7.5)
    ax[1].set_xlim(0, 1); ax[1].set_ylim(-0.05, 1.08)
    fig.tight_layout(); save(fig, "fig_device")


metric_vs_f(); tradeoff(); fpr_vs_noise(); resource_cost(); device_noise()
print("wrote 5 results figures to", OUT)