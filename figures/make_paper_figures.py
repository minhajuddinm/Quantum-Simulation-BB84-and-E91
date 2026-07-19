"""
=============================================================================
 REGENERATE THE SIX DATA FIGURES FOR THE JOURNAL MANUSCRIPT
=============================================================================
 Reads ONLY the existing result CSVs and produces vector PDFs (plus SVG/PNG)
 into figures/. NO Qiskit/Aer simulation is run: every number is read from a
 CSV or derived from per-trial values by arithmetic (means and t-distribution
 95% confidence intervals).

 Run from the PROJECT ROOT (so the CWD-relative CSV paths resolve):

     python figures/make_paper_figures.py              # all six
     python figures/make_paper_figures.py --only 3     # just fig 3
     python figures/make_paper_figures.py --only 1,2,4 # a subset

 Figure -> file (names the manuscript's \\includegraphics expects):
     1  fig_metric_vs_f.pdf        (a) QBER vs f      (b) CHSH S vs f
     2  fig_tradeoff.pdf           (a) FNR vs f       (b) SKR vs f
     3  fig_fpr_vs_noise.pdf       honest FPR vs noise (E91 fixed S=2 + calib S*)
     4  fig_resource_cost.pdf      (a) FPR vs K @11%   (b) FNR vs K clean
     5  fig_detection_decision.pdf schematic (relabelled to S*)
     6  fig_device.pdf             (a) honest SKR bars (b) FNR vs f on device

 Global style: one colour per protocol (BB84 blue, six-state green, E91
 purple); 95% CI shading from per-trial values via the t-distribution (never
 one standard deviation); (a)/(b) panel labels; IEEE column-readable fonts.

 SOURCES
   results/ci_pertrial_fsweep_ideal.csv   per-trial sweep_a (QBER/S, SKR, FNR)
   results/ci_pertrial_fpr_noise.csv      per-trial sweep_b (honest FPR, S)
   qkd_resource_cost.csv                  BB84/six-state FPR/FNR vs K
   results/qkd_e91_resource_cost_sstar.csv E91 FPR/FNR vs K (fixed 2.0 & S*)
   qkd_varying_eve.csv                    device (ibm_marrakesh) SKR/FNR
   qkd_e91_calibrated.csv                 E91 device FNR under calibrated S*
=============================================================================
"""
import argparse
import csv
import os
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

try:
    from scipy.stats import t as _tdist
    def t_crit(df):
        return float(_tdist.ppf(0.975, df))
except Exception:                                   # pragma: no cover
    _T = {1: 12.706, 2: 4.303, 5: 2.571, 9: 2.262, 24: 2.064,
          29: 2.045, 49: 2.010, 99: 1.984, 199: 1.972}
    def t_crit(df):
        for k in sorted(_T):
            if df <= k:
                return _T[k]
        return 1.96

# ---------------------------------------------------------------------------
# Global style
# ---------------------------------------------------------------------------
plt.rcParams.update({
    "font.family": "serif", "font.size": 8, "mathtext.fontset": "cm",
    "axes.linewidth": 0.8, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
})
C = {"BB84": "#2c6fbb", "Six-State": "#3a8a5f", "E91": "#9a6db0"}
M = {"BB84": "o", "Six-State": "s", "E91": "^"}
HON, EVE, GREY = "#2c6fbb", "#c2452d", "#777777"
INK = "#1a1a1a"
PROT = ["BB84", "Six-State", "E91"]
OUT = "figures"
os.makedirs(OUT, exist_ok=True)

# E91 calibrated CHSH thresholds S* per honest-noise profile (journal Table III)
S_STAR = {"Ideal_0%": 2.124, "Noise_2%": 1.945, "Noise_5%": 1.722,
          "Noise_8%": 1.499, "Threshold_11%": 1.293}
NOISE = [("Ideal_0%", 0), ("Noise_2%", 2), ("Noise_5%", 5),
         ("Noise_8%", 8), ("Threshold_11%", 11)]


# ---------------------------------------------------------------------------
# Statistics helpers (mean + 95% t-CI from per-trial values)
# ---------------------------------------------------------------------------
def mean_ci(vals):
    """Return (mean, lo, hi) with a two-sided 95% t-distribution CI."""
    v = np.asarray(vals, float)
    n = v.size
    m = float(v.mean())
    if n < 2:
        return m, m, m
    se = v.std(ddof=1) / np.sqrt(n)
    d = t_crit(n - 1) * se
    return m, m - d, m + d


def mean_ci_ms(mean, std, n):
    """95% t-CI from an already-aggregated mean/std over n trials."""
    if n < 2 or std == 0:
        return mean, mean
    d = t_crit(n - 1) * std / np.sqrt(n)
    return mean - d, mean + d


def wilson(k, n, z=1.96):
    """Wilson 95% CI for a binomial proportion (device rates have no per-trial CSV)."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - half), min(1.0, c + half)


def curve(rows, proto, value_col, metric_name=None, fmin=None):
    """Per-f mean + 95% CI of `value_col`, optionally filtered to a Metric_Name
    and to F_Eve > fmin. Returns arrays f, mean, lo, hi (sorted by f)."""
    sel = [r for r in rows if r["Protocol"] == proto]
    if metric_name is not None:
        sel = [r for r in sel if r["Metric_Name"] == metric_name]
    if fmin is not None:
        sel = [r for r in sel if float(r["F_Eve"]) > fmin]
    groups = defaultdict(list)
    for r in sel:
        groups[float(r["F_Eve"])].append(float(r[value_col]))
    out = []
    for f in sorted(groups):
        m, lo, hi = mean_ci(groups[f])
        out.append((f, m, lo, hi))
    a = np.array(out).T
    return a[0], a[1], a[2], a[3]


def band(ax, x, lo, hi, color, lo_clip=None, hi_clip=None):
    if lo_clip is not None:
        lo = np.clip(lo, lo_clip, None)
    if hi_clip is not None:
        hi = np.clip(hi, None, hi_clip)
    ax.fill_between(x, lo, hi, color=color, alpha=0.15, lw=0)


def panel(ax, tag):
    ax.set_title(tag, fontsize=8.5, loc="left")


def save(fig, name):
    paths = {}
    for ext in ("pdf", "svg", "png"):
        p = f"{OUT}/{name}.{ext}"
        fig.savefig(p, dpi=200 if ext == "png" else None)
        paths[ext] = p
    plt.close(fig)
    return paths["pdf"]


# ---------------------------------------------------------------------------
# Lazy CSV loaders (only read what a requested figure needs)
# ---------------------------------------------------------------------------
_cache = {}
def load(path):
    """Read a CSV into a list of dict rows (values kept as strings)."""
    if path not in _cache:
        with open(path, newline="") as f:
            _cache[path] = list(csv.DictReader(f))
    return _cache[path]


def where(rows, **eq):
    """Rows whose columns equal the given values (string or numeric compare)."""
    out = []
    for r in rows:
        ok = True
        for k, v in eq.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if float(r[k]) != float(v):
                    ok = False; break
            elif r[k] != v:
                ok = False; break
        if ok:
            out.append(r)
    return out


def fcol(rows, name):
    """Extract a column as a float numpy array."""
    return np.array([float(r[name]) for r in rows])


# ===========================================================================
# FIGURE 1 -- fig_metric_vs_f.pdf   (two panels, full text width)
# ===========================================================================
def fig1():
    pt = load("results/ci_pertrial_fsweep_ideal.csv")
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.9))

    # (a) QBER vs f for BB84 and six-state, dashed thresholds, CI bands
    for p, thr in [("BB84", 0.135), ("Six-State", 0.167)]:
        f, m, lo, hi = curve(pt, p, "Metric", metric_name="QBER")
        ax[0].plot(f, m, color=C[p], marker=M[p], ms=3.5, lw=1.4, label=p)
        band(ax[0], f, lo, hi, C[p])
        ax[0].axhline(thr, color=C[p], ls="--", lw=0.9)
    ax[0].text(0.02, 0.135, " 0.135", color=C["BB84"], fontsize=6.5, va="bottom")
    ax[0].text(0.02, 0.167, " 0.167", color=C["Six-State"], fontsize=6.5, va="bottom")
    ax[0].set_xlabel("interception fraction $f$")
    ax[0].set_ylabel("QBER")
    ax[0].set_xlim(0, 1)
    ax[0].legend(fontsize=7, frameon=False, loc="lower right")
    ax[0].tick_params(labelsize=7.5)
    panel(ax[0], "(a)")

    # (b) E91 CHSH S vs f, three reference lines, CI band
    f, m, lo, hi = curve(pt, "E91", "Metric", metric_name="CHSH_S")
    ax[1].plot(f, m, color=C["E91"], marker=M["E91"], ms=3.5, lw=1.4, label="E91")
    band(ax[1], f, lo, hi, C["E91"])
    ax[1].axhline(2 * np.sqrt(2), color=GREY, ls=":", lw=0.9)
    ax[1].axhline(2.0, color="#444", ls="--", lw=0.9)
    ax[1].axhline(2.124, color=C["E91"], ls="-.", lw=1.0)
    ax[1].text(0.98, 2 * np.sqrt(2), "Tsirelson $2\\sqrt{2}$ ", fontsize=6.3,
               color=GREY, va="bottom", ha="right")
    ax[1].text(0.02, 2.0, " $S=2$", fontsize=6.5, va="bottom")
    ax[1].text(0.40, 2.124, "$S^*$ (calibrated)", fontsize=6.5,
               color=C["E91"], va="bottom")
    ax[1].set_xlabel("interception fraction $f$")
    ax[1].set_ylabel("CHSH $S$")
    ax[1].set_xlim(0, 1)
    ax[1].legend(fontsize=7, frameon=False, loc="lower left")
    ax[1].tick_params(labelsize=7.5)
    panel(ax[1], "(b)")

    fig.tight_layout()
    return save(fig, "fig_metric_vs_f")


# ===========================================================================
# FIGURE 2 -- fig_tradeoff.pdf   (two stacked panels, column width)
# ===========================================================================
def fig2():
    pt = load("results/ci_pertrial_fsweep_ideal.csv")
    fig, ax = plt.subplots(2, 1, figsize=(3.5, 4.7), sharex=True)

    # (a) FNR vs f (attacked points only; f=0 is a false-positive point)
    for p in PROT:
        f, m, lo, hi = curve(pt, p, "Detection_Outcome", fmin=0.0)
        ax[0].plot(f, m, color=C[p], marker=M[p], ms=3.5, lw=1.4, label=p)
        band(ax[0], f, lo, hi, C[p], lo_clip=0.0, hi_clip=1.0)
    # (b) asymptotic SKR vs f
    for p in PROT:
        f, m, lo, hi = curve(pt, p, "SKR")
        ax[1].plot(f, m, color=C[p], marker=M[p], ms=3.5, lw=1.4, label=p)
        band(ax[1], f, lo, hi, C[p], lo_clip=0.0)

    for a in ax:
        a.axvspan(0.0, 0.3, color=GREY, alpha=0.10, lw=0)
        a.set_xlim(0, 1)
        a.tick_params(labelsize=7.5)
    ax[0].axhline(0.5, color=GREY, ls=":", lw=0.8)
    ax[0].text(0.15, 0.5, "stealth\nwindow", ha="center", va="center",
               fontsize=6.8, color=GREY)
    ax[0].set_ylabel("FNR (missed detection)")
    ax[0].set_ylim(-0.05, 1.08)
    ax[0].legend(fontsize=6.8, frameon=False, loc="center right", ncol=1)
    panel(ax[0], "(a)")
    ax[1].set_ylabel("secure key rate")
    ax[1].set_xlabel("interception fraction $f$")
    panel(ax[1], "(b)")

    fig.tight_layout()
    return save(fig, "fig_tradeoff")


# ===========================================================================
# FIGURE 3 -- fig_fpr_vs_noise.pdf   (single panel, column width)
# ===========================================================================
def fig3():
    pt = load("results/ci_pertrial_fpr_noise.csv")
    fig, ax = plt.subplots(figsize=(3.6, 3.0))

    # BB84 / six-state honest FPR from the alarm indicator (Alarm_FP)
    for p in ["BB84", "Six-State"]:
        xs, ys, los, his = [], [], [], []
        for prof, lvl in NOISE:
            g = where(pt, Protocol=p, Noise_Profile=prof)
            if g:
                m, lo, hi = mean_ci(fcol(g, "Alarm_FP"))
                xs.append(lvl); ys.append(m); los.append(max(0, lo)); his.append(hi)
        ax.plot(xs, ys, color=C[p], marker=M[p], ms=4, lw=1.4, label=p)
        ax.fill_between(xs, los, his, color=C[p], alpha=0.15, lw=0)

    # E91 FIXED rule S < 2.0 (derived from per-trial S) -- the failure mode
    xs, ys, los, his = [], [], [], []
    for prof, lvl in NOISE:
        s = fcol(where(pt, Protocol="E91", Noise_Profile=prof), "Metric")
        k = int((s < 2.0).sum()); n = s.size
        lo, hi = wilson(k, n)
        xs.append(lvl); ys.append(k / n); los.append(lo); his.append(hi)
    ax.plot(xs, ys, color=C["E91"], marker=M["E91"], ms=4, lw=1.4,
            ls="--", label="E91 (fixed $S=2.0$)")
    ax.fill_between(xs, los, his, color=C["E91"], alpha=0.12, lw=0)

    # E91 CALIBRATED S* (honest alarm indicator already uses per-profile S*)
    xs, ys = [], []
    for prof, lvl in NOISE:
        g = where(pt, Protocol="E91", Noise_Profile=prof)
        xs.append(lvl); ys.append(float(fcol(g, "Alarm_FP").mean()))
    ax.plot(xs, ys, color=C["E91"], marker="D", ms=3.5, lw=1.4,
            ls="-", label="E91 (calibrated $S^*$)")

    ax.set_xlabel("synthetic channel noise level (%)")
    ax.set_ylabel("FPR (false alarm rate)")
    ax.set_xticks([lvl for _, lvl in NOISE])
    ax.set_ylim(-0.05, 1.08)
    ax.legend(fontsize=6.6, frameon=False, loc="upper left")
    ax.tick_params(labelsize=7.5)
    fig.tight_layout()
    return save(fig, "fig_fpr_vs_noise")


# ===========================================================================
# FIGURE 4 -- fig_resource_cost.pdf   (two panels, full text width)
# ===========================================================================
def _rc(rc, proto, col):
    d = sorted(where(rc, Protocol=proto), key=lambda r: float(r["K"]))
    return fcol(d, "K"), fcol(d, col)


def _ss(ss, curve_name, channel):
    d = [r for r in ss if r["Threshold_Mode"] == "Sstar" and r["Curve"] == curve_name
         and r["Channel"].startswith(channel)]
    d.sort(key=lambda r: float(r["K"]))
    return fcol(d, "K"), fcol(d, "Rate")


def fig4():
    rc = load("data/qkd_resource_cost.csv")
    ss = load("results/qkd_e91_resource_cost_sstar.csv")
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.9))

    # (a) FPR vs K on the worst-case honest 11% channel
    for p in ["BB84", "Six-State"]:
        k, y = _rc(rc, p, "FPR")
        ax[0].plot(k, y, color=C[p], marker=M[p], ms=4, lw=1.4, label=p)
    k, r = _ss(ss, "FPR", "Threshold_11%")
    ax[0].plot(k, r, color=C["E91"], marker=M["E91"], ms=4, lw=1.4,
               label="E91 ($S^*$)")
    # (b) FNR vs K against a full attacker on a clean channel
    for p in ["BB84", "Six-State"]:
        k, y = _rc(rc, p, "FNR")
        ax[1].plot(k, y, color=C[p], marker=M[p], ms=4, lw=1.4, label=p)
    k, r = _ss(ss, "FNR", "Ideal_0%")
    ax[1].plot(k, r, color=C["E91"], marker=M["E91"], ms=4, lw=1.4,
               label="E91 ($S^*$)")

    for a in ax:
        a.set_xscale("log")
        a.axhline(0.05, color=GREY, ls=":", lw=0.8)
        a.set_xlabel("compared signals $K$")
        a.tick_params(labelsize=7.5)
        a.legend(fontsize=7, frameon=False)
    ax[0].text(105, 0.065, "5%", fontsize=6.5, color=GREY)
    ax[1].text(105, 0.065, "5%", fontsize=6.5, color=GREY)
    ax[0].set_ylabel("FPR (false alarm rate)")
    ax[1].set_ylabel("FNR (missed full attacker)")
    panel(ax[0], "(a)")
    panel(ax[1], "(b)")
    fig.tight_layout()
    return save(fig, "fig_resource_cost")


# ===========================================================================
# FIGURE 5 -- fig_detection_decision.pdf   (schematic, full text width)
# ===========================================================================
def _gauss(x, mu, sd):
    return np.exp(-0.5 * ((x - mu) / sd) ** 2)


def fig5():
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.95))

    # (a) QBER schematic -- unchanged
    ax = axes[0]
    x = np.linspace(0, 0.30, 700)
    hon = _gauss(x, 0.090, 0.027); eve = _gauss(x, 0.185, 0.033); thr = 0.135
    ax.plot(x, hon, color=HON, lw=1.6); ax.plot(x, eve, color=EVE, lw=1.6)
    ax.fill_between(x[x >= thr], 0, hon[x >= thr], color=HON, alpha=0.45, lw=0)
    ax.fill_between(x[x <= thr], 0, eve[x <= thr], color=EVE, alpha=0.40, lw=0)
    ax.axvline(thr, color=INK, lw=1.1, ls="--")
    ax.text(0.137, 1.30, "threshold 0.135", fontsize=7.0, va="top", ha="center")
    ax.text(0.090, 1.06, "honest\n(noise)", color=HON, fontsize=7.6, ha="center", va="bottom")
    ax.text(0.205, 1.06, "eavesdropper", color=EVE, fontsize=7.6, ha="center", va="bottom")
    ax.annotate("FPR", xy=(0.150, 0.06), xytext=(0.225, 0.46), fontsize=8, color=HON,
                arrowprops=dict(arrowstyle="-|>", color=HON, lw=0.9))
    ax.annotate("FNR", xy=(0.122, 0.06), xytext=(0.018, 0.46), fontsize=8, color=EVE,
                arrowprops=dict(arrowstyle="-|>", color=EVE, lw=0.9))
    ax.set_xlim(0, 0.285); ax.set_ylim(0, 1.45); ax.set_yticks([])
    ax.set_xlabel("QBER")
    ax.set_title("(a) BB84 / six-state:  alarm if QBER $\\geq$ threshold", fontsize=8)
    ax.tick_params(labelsize=7.5)

    # (b) CHSH schematic -- threshold relabelled S=2 -> S*
    ax = axes[1]
    x = np.linspace(1.3, 2.9, 700)
    hon = _gauss(x, 2.30, 0.12); eve = _gauss(x, 1.85, 0.15); thr = 2.124
    ax.plot(x, hon, color=HON, lw=1.6); ax.plot(x, eve, color=EVE, lw=1.6)
    ax.fill_between(x[x <= thr], 0, hon[x <= thr], color=HON, alpha=0.45, lw=0)
    ax.fill_between(x[x >= thr], 0, eve[x >= thr], color=EVE, alpha=0.40, lw=0)
    ax.axvline(thr, color=INK, lw=1.1, ls="-.")
    ax.text(2.124, 1.30, "threshold $S^*$", fontsize=7.0, va="top", ha="center")
    ax.text(2.48, 1.06, "honest", color=HON, fontsize=7.6, ha="center", va="bottom")
    ax.text(1.70, 1.06, "eavesdropper", color=EVE, fontsize=7.6, ha="center", va="bottom")
    ax.annotate("FPR", xy=(2.02, 0.06), xytext=(1.55, 0.46), fontsize=8, color=HON,
                arrowprops=dict(arrowstyle="-|>", color=HON, lw=0.9))
    ax.annotate("FNR", xy=(2.24, 0.06), xytext=(2.62, 0.46), fontsize=8, color=EVE,
                arrowprops=dict(arrowstyle="-|>", color=EVE, lw=0.9))
    ax.set_xlim(1.35, 2.85); ax.set_ylim(0, 1.45); ax.set_yticks([])
    ax.set_xlabel("CHSH parameter $S$")
    ax.set_title("(b) E91:  alarm if $S < S^*$", fontsize=8)
    ax.tick_params(labelsize=7.5)

    handles = [Line2D([0], [0], color=HON, lw=1.6, label="honest channel (no Eve)"),
               Line2D([0], [0], color=EVE, lw=1.6, label="eavesdropper present")]
    fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=7.6,
               frameon=False, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    return save(fig, "fig_detection_decision")


# ===========================================================================
# FIGURE 6 -- fig_device.pdf   (two panels, full text width)  [device data only]
# ===========================================================================
def fig6():
    ve = load("data/qkd_varying_eve.csv")
    if not where(ve, Noise_Profile="IBM_Marrakesh"):
        return None                                 # no device data -> SKIP
    e91c = load("data/qkd_e91_calibrated.csv")
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.9))

    # (a) honest secure key rate: ideal vs device, with 95% t-CI error bars
    def honest(proto, profile):
        r = where(ve, Protocol=proto, Noise_Profile=profile, F_Eve=0.0)[0]
        return float(r["Mean_SKR"]), float(r["Std_SKR"])
    x = np.arange(3); w = 0.36
    for off, prof, n, lbl, col in [(-w / 2, "Ideal_0%", 200, "ideal", "#c9c9c9"),
                                   (w / 2, "IBM_Marrakesh", 30, "ibm_marrakesh", "#6a9fd0")]:
        means, errs = [], []
        for p in PROT:
            m, sd = honest(p, prof)
            lo, _ = mean_ci_ms(m, sd, n)
            means.append(m); errs.append(m - lo)
        ax[0].bar(x + off, means, w, yerr=errs, capsize=2.5, label=lbl,
                  color=col, edgecolor="k", lw=0.6,
                  error_kw=dict(lw=0.8, ecolor="#333"))
    ax[0].set_xticks(x); ax[0].set_xticklabels(PROT, fontsize=7.5)
    ax[0].set_ylabel("honest secure key rate")
    ax[0].legend(fontsize=7, frameon=False)
    ax[0].tick_params(labelsize=7.5)
    panel(ax[0], "(a)")

    # (b) FNR vs f on the device (BB84/six-state from ve, E91 from calibrated S*)
    for p in PROT:
        src = e91c if p == "E91" else ve
        d = where(src, Noise_Profile="IBM_Marrakesh") if p == "E91" \
            else where(ve, Protocol=p, Noise_Profile="IBM_Marrakesh")
        d = sorted(d, key=lambda r: float(r["F_Eve"]))
        xf, yf = fcol(d, "F_Eve"), fcol(d, "FNR")
        ax[1].plot(xf, yf, color=C[p], marker=M[p], ms=4, lw=1.4, label=p)
        los = [wilson(int(round(v * 30)), 30)[0] for v in yf]
        his = [wilson(int(round(v * 30)), 30)[1] for v in yf]
        ax[1].fill_between(xf, los, his, color=C[p], alpha=0.12, lw=0)
    ax[1].axhline(0.5, color=GREY, ls=":", lw=0.8)
    ax[1].set_xlabel("interception fraction $f$")
    ax[1].set_ylabel("FNR (missed detection)")
    ax[1].set_xlim(0, 1); ax[1].set_ylim(-0.05, 1.08)
    ax[1].legend(fontsize=7, frameon=False, loc="upper right")
    ax[1].tick_params(labelsize=7.5)
    panel(ax[1], "(b)")

    fig.tight_layout()
    return save(fig, "fig_device")


# ===========================================================================
# DRIVER
# ===========================================================================
FIGS = {1: ("fig_metric_vs_f.pdf", fig1), 2: ("fig_tradeoff.pdf", fig2),
        3: ("fig_fpr_vs_noise.pdf", fig3), 4: ("fig_resource_cost.pdf", fig4),
        5: ("fig_detection_decision.pdf", fig5), 6: ("fig_device.pdf", fig6)}


def verify_pdf(path):
    """Confirm a non-empty vector PDF was written."""
    if not path or not os.path.exists(path):
        return False, 0
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        head = f.read(5)
    return (head == b"%PDF-" and size > 1500), size


def main():
    ap = argparse.ArgumentParser(description="Regenerate the six data figures.")
    ap.add_argument("--only", default="", help="comma list of figure numbers, e.g. 1,3,6")
    args = ap.parse_args()
    which = sorted(int(x) for x in args.only.split(",")) if args.only else sorted(FIGS)

    print("Regenerating figures (no simulation; CSV-driven)\n" + "-" * 52)
    results = []
    for n in which:
        name, fn = FIGS[n]
        try:
            pdf = fn()
            if pdf is None:
                results.append((name, "SKIPPED (no device data)", 0))
                continue
            ok, size = verify_pdf(pdf)
            results.append((name, "OK" if ok else "FAIL (not vector/empty)", size))
        except Exception as e:                       # pragma: no cover
            results.append((name, f"ERROR: {e}", 0))

    print("\nCHECKLIST")
    print("-" * 52)
    for name, status, size in results:
        kb = f"{size/1024:6.1f} kB" if size else "     -- "
        print(f"  {name:28s} {kb}  {status}")
    print("-" * 52)


if __name__ == "__main__":
    main()
