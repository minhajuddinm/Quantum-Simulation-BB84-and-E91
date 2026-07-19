"""
Priority 1 figure: fixed classical-bound threshold (S=2.0) vs the
noise-calibrated threshold (S*) for E91 CHSH-based eavesdropper detection.

Shows the full detection-error curve across the whole attack fraction f
(not just the honest channel f=0), for both threshold schemes, one small
panel per noise profile:
  - at f=0 the plotted quantity is FPR (false alarm on an honest channel)
  - at f>0 it is FNR (missed detection under a partial attacker)
  these are mutually exclusive by construction (see monte_carlo_e91 in
  detection_aware_qkd_varying_eve.py: fpr is only computed at f_eve==0.0,
  fnr only at f_eve>0.0), so plotting them as one continuous "detection
  error rate" curve is standard practice for this kind of result and
  matches how the existing fig_tradeoff() panel already treats FNR.

Reads:
  qkd_varying_eve.csv       (existing fixed-threshold results)
  qkd_e91_calibrated.csv    (new calibrated-threshold results, includes
                             the IBM_Marrakesh hardware-noise profile)

Writes fig_e91_calibrated_threshold.{pdf,svg,png} into this folder.
Run: python fig_e91_calibrated_threshold.py
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
OUT = "figures"
os.makedirs(OUT, exist_ok=True)

ve = pd.read_csv("data/qkd_varying_eve.csv")
cal = pd.read_csv("data/qkd_e91_calibrated.csv")

PROFILES = ["Ideal_0%", "Noise_2%", "Noise_5%", "Noise_8%", "Threshold_11%", "IBM_Marrakesh"]
TITLES = ["Ideal 0%", "Noise 2%", "Noise 5%", "Noise 8%", "Threshold 11%", "IBM Marrakesh"]

OLD_COLOR = "#c0524a"
NEW_COLOR = "#4a8fc0"


def save(fig, name):
    fig.savefig(f"{OUT}/{name}.pdf")
    fig.savefig(f"{OUT}/{name}.svg")
    fig.savefig(f"{OUT}/{name}.png", dpi=200)
    plt.close(fig)


def error_curve(df, is_calibrated):
    """Returns (f_values, error_rate) where error_rate = FPR at f=0 and
    FNR at f>0, sorted by f."""
    d = df.sort_values("F_Eve")
    f = d["F_Eve"].values
    err = np.where(f == 0.0, d["FPR"].values, d["FNR"].values)
    return f, err


def full_sweep_figure():
    fig, axes = plt.subplots(2, 3, figsize=(9.8, 5.8), sharey=True, sharex=True)

    for ax, prof, title in zip(axes.flat, PROFILES, TITLES):
        o = ve[(ve.Protocol == "E91") & (ve.Noise_Profile == prof)]
        n = cal[cal.Noise_Profile == prof]
        s_star = n["S_star"].values[0]

        fo, eo = error_curve(o, is_calibrated=False)
        fn_, en = error_curve(n, is_calibrated=True)

        ax.plot(fo, eo, color=OLD_COLOR, marker="o", ms=4, lw=1.3, ls="--",
                 label="Fixed $S=2.0$")
        ax.plot(fn_, en, color=NEW_COLOR, marker="s", ms=4, lw=1.3, ls="-",
                 label="Calibrated $S^*$")

        # Mark the honest-channel point (f=0, i.e. FPR) distinctly, since
        # that's the specific headline result -- a filled star on top of
        # each curve's own f=0 marker, in the curve's own color.
        ax.scatter([0], [eo[0]], color=OLD_COLOR, marker="*", s=110,
                    zorder=5, edgecolor="k", linewidth=0.4)
        ax.scatter([0], [en[0]], color=NEW_COLOR, marker="*", s=110,
                    zorder=5, edgecolor="k", linewidth=0.4)

        ax.set_title(f"{title}   ($S^*$={s_star:.2f})", fontsize=8.3)
        ax.set_ylim(-0.05, 1.08)
        ax.set_xlim(-0.03, 1.03)
        ax.tick_params(labelsize=7)
        ax.axhline(0.0, color="#999", lw=0.5, zorder=0)

    for ax in axes[-1, :]:
        ax.set_xlabel("interception fraction $f$", fontsize=7.5)
    for ax in axes[:, 0]:
        ax.set_ylabel("FPR ($f=0$)  /  FNR ($f>0$)", fontsize=7.5)

    handles, labels = axes.flat[0].get_legend_handles_labels()
    star_old = plt.Line2D([], [], color=OLD_COLOR, marker="*", ms=11, ls="",
                            markeredgecolor="k", markeredgewidth=0.4, label="FPR, fixed (f=0)")
    star_new = plt.Line2D([], [], color=NEW_COLOR, marker="*", ms=11, ls="",
                            markeredgecolor="k", markeredgewidth=0.4, label="FPR, calibrated (f=0)")
    fig.legend(handles=handles + [star_old, star_new], loc="lower center",
                ncol=4, fontsize=7.5, frameon=False, bbox_to_anchor=(0.5, -0.02))

    fig.suptitle("E91 detection error across the full attack sweep: fixed vs. noise-calibrated CHSH threshold",
                  fontsize=9.5, y=1.01)
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    save(fig, "fig_e91_calibrated_threshold")


if __name__ == "__main__":
    full_sweep_figure()
    print("Saved fig_e91_calibrated_threshold.{pdf,svg,png} in", os.path.abspath(OUT))
