"""
Combined three-panel circuit figure: (a) BB84, (b) six-state, (c) E91.
Replaces fig_circuit_bb84 / _sixstate / _e91 with a single figure for the
short-format paper. Run: python figures/fig_circuits_panel.py
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from matplotlib.lines import Line2D

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "mathtext.fontset": "cm",
    "axes.linewidth": 0.8, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
})
INK = "#1a1a1a"; EVE = "#c2452d"; GREY = "#777777"; NOISE = "#f3eee6"
OUT = "figures"
os.makedirs(OUT, exist_ok=True)

def wire(ax, y, x0, x1, color=INK): ax.plot([x0, x1], [y, y], color=color, lw=1.0, zorder=1)

def gate(ax, x, y, label, w=0.62, h=0.52, fc="white", ec=INK, fs=9.0):
    ax.add_patch(Rectangle((x-w/2, y-h/2), w, h, facecolor=fc, edgecolor=ec, lw=1.1, zorder=3))
    ax.text(x, y, label, ha="center", va="center", fontsize=fs, zorder=4)

def meas(ax, x, y, w=0.62, h=0.52):
    ax.add_patch(Rectangle((x-w/2, y-h/2), w, h, facecolor="white", edgecolor=INK, lw=1.1, zorder=3))
    th = np.linspace(0.18*np.pi, 0.82*np.pi, 40)
    ax.plot(x+0.17*np.cos(th), y-0.09+0.17*np.sin(th), color=INK, lw=0.9, zorder=4)
    ax.annotate("", xy=(x+0.13, y+0.11), xytext=(x, y-0.09),
                arrowprops=dict(arrowstyle="-", lw=0.9, color=INK), zorder=4)

def sep(ax, x, y0, y1): ax.plot([x, x], [y0, y1], color=GREY, lw=0.8, ls=(0, (3, 3)), zorder=1)

def note(ax, x, y, t, fs=6.6): ax.text(x, y, t, ha="center", va="top", fontsize=fs, color=GREY, style="italic")

def panel_label(ax, x, y, t): ax.text(x, y, t, ha="left", va="center", fontsize=9.5)

def eve_box(ax, x0, y0, w, h, lx, ly, va="bottom"):
    ax.add_patch(Rectangle((x0, y0), w, h, fill=False, ec=EVE, lw=0.9, ls=(0, (2, 2)), zorder=2))
    ax.text(lx, ly, "Eve  (prob. $f$)", ha="center", va=va, fontsize=7.2, color=EVE)


# --------------------------------------------------------------------------
# Panels. All three share the x-range so the stage columns line up vertically.
# --------------------------------------------------------------------------
def panel_bb84(ax):
    ax.set_xlim(-0.2, 12.0); ax.set_ylim(-0.95, 1.20); ax.axis("off")
    y = 0.0; wire(ax, y, 1.15, 11.3)
    panel_label(ax, -0.2, 1.02, "(a) BB84")
    ax.text(1.0, y, r"$|0\rangle$", ha="right", va="center", fontsize=9.5)
    gate(ax, 1.9, y, "$X$"); note(ax, 1.9, -0.36, "bit $a$")
    gate(ax, 2.8, y, "$H$"); note(ax, 2.8, -0.36, "basis")
    sep(ax, 3.4, -0.5, 0.5)
    gate(ax, 4.2, y, "$H$", ec=EVE); meas(ax, 5.1, y); gate(ax, 6.0, y, "$H$", ec=EVE)
    eve_box(ax, 3.75, -0.45, 2.7, 0.9, 5.1, 0.52)
    sep(ax, 6.7, -0.5, 0.5)
    gate(ax, 7.5, y, "$\\mathcal{N}_p$", fc=NOISE); note(ax, 7.5, -0.36, "noise")
    sep(ax, 8.2, -0.5, 0.5)
    gate(ax, 9.0, y, "$H$"); note(ax, 9.0, -0.36, "basis"); meas(ax, 9.9, y)
    note(ax, 6.0, -0.62, "$H$ applied only when the random basis is $X$")

def panel_sixstate(ax):
    ax.set_xlim(-0.2, 12.0); ax.set_ylim(-0.95, 1.20); ax.axis("off")
    y = 0.0; wire(ax, y, 1.15, 11.3)
    panel_label(ax, -0.2, 1.02, "(b) Six-state")
    ax.text(1.0, y, r"$|0\rangle$", ha="right", va="center", fontsize=9.5)
    gate(ax, 1.9, y, "$X$"); note(ax, 1.9, -0.36, "bit $a$")
    gate(ax, 2.72, y, "$H$"); gate(ax, 3.44, y, "$S$"); note(ax, 3.08, -0.36, "$Y$-basis: $SH$")
    sep(ax, 3.95, -0.5, 0.5)
    gate(ax, 4.65, y, "$S^{\\dagger}$", ec=EVE, fs=8.0); gate(ax, 5.4, y, "$H$", ec=EVE); meas(ax, 6.15, y)
    eve_box(ax, 4.22, -0.45, 2.3, 0.9, 5.4, 0.52)
    sep(ax, 6.75, -0.5, 0.5)
    gate(ax, 7.5, y, "$\\mathcal{N}_p$", fc=NOISE); note(ax, 7.5, -0.36, "noise")
    sep(ax, 8.2, -0.5, 0.5)
    gate(ax, 8.95, y, "$S^{\\dagger}$", fs=8.0); gate(ax, 9.7, y, "$H$"); meas(ax, 10.45, y)
    note(ax, 6.0, -0.62, "third basis $Y$: prepare with $SH$, measure with $S^{\\dagger}H$;  $Z,X$ as in BB84")

def panel_e91(ax):
    ax.set_xlim(-0.2, 12.0); ax.set_ylim(-1.65, 1.75); ax.axis("off")
    yA, yB = 0.62, -0.62
    wire(ax, yA, 1.35, 11.3); wire(ax, yB, 1.35, 11.3)
    panel_label(ax, -0.2, 1.55, "(c) E91")
    ax.text(1.2, yA, r"$|0\rangle$", ha="right", va="center", fontsize=9.5)
    ax.text(1.2, yB, r"$|0\rangle$", ha="right", va="center", fontsize=9.5)
    ax.text(1.25, yA+0.42, "Alice", ha="center", va="bottom", fontsize=7.0, color=GREY)
    ax.text(1.25, yB-0.42, "Bob", ha="center", va="top", fontsize=7.0, color=GREY)
    # Bell pair
    gate(ax, 2.1, yA, "$H$")
    ax.add_patch(Circle((2.9, yA), 0.070, color=INK, zorder=4))
    ax.plot([2.9, 2.9], [yA, yB], color=INK, lw=1.0, zorder=2)
    ax.add_patch(Circle((2.9, yB), 0.165, fill=False, ec=INK, lw=1.1, zorder=4))
    ax.plot([2.74, 3.06], [yB, yB], color=INK, lw=1.0, zorder=5)
    ax.plot([2.9, 2.9], [yB-0.165, yB+0.165], color=INK, lw=1.0, zorder=5)
    ax.text(2.5, 1.30, "Bell source", ha="center", fontsize=7.6)
    sep(ax, 3.5, -1.0, 1.0)
    gate(ax, 4.2, yA, "$\\mathcal{N}_p$", fc=NOISE); gate(ax, 4.2, yB, "$\\mathcal{N}_p$", fc=NOISE)
    ax.text(4.2, 1.30, "channel", ha="center", fontsize=7.6, color=GREY)
    sep(ax, 4.9, -1.0, 1.0)
    # Eve intercepts Bob's qubit
    gate(ax, 5.7, yB, "$R_y(\\theta_E)$", w=0.95, ec=EVE, fs=7.5)
    meas(ax, 6.75, yB)
    gate(ax, 7.7, yB, "$R_y(\\!-\\theta_E)$", w=1.0, ec=EVE, fs=7.5)
    eve_box(ax, 5.15, yB-0.48, 3.05, 0.96, 6.65, yB+0.52, va="bottom")
    sep(ax, 8.5, -1.0, 1.0)
    gate(ax, 9.3, yA, "$R_y(a)$", w=0.9, fs=8.0); meas(ax, 10.4, yA)
    gate(ax, 9.3, yB, "$R_y(b)$", w=0.9, fs=8.0); meas(ax, 10.4, yB)
    ax.text(9.85, 1.30, "measure", ha="center", fontsize=7.6)
    note(ax, 6.0, -1.22, "matched axes form the key; the CHSH settings estimate $S$")


def circuits_panel(name="fig_circuits_all"):
    fig, axes = plt.subplots(3, 1, figsize=(7.0, 5.15),
                             gridspec_kw={"height_ratios": [1.0, 1.0, 1.62], "hspace": 0.10})
    panel_bb84(axes[0]); panel_sixstate(axes[1]); panel_e91(axes[2])
    # stage headers on the top panel only: (a) and (b) share the same column layout
    axes[0].text(2.35, 0.72, "prepare", ha="center", fontsize=7.6)
    axes[0].text(7.5, 0.72, "channel", ha="center", fontsize=7.6, color=GREY)
    axes[0].text(9.45, 0.72, "measure", ha="center", fontsize=7.6)
    handles = [
        Line2D([0], [0], marker="s", color="none", markerfacecolor="white",
               markeredgecolor=INK, markersize=7, label="protocol gate / measurement"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor="white",
               markeredgecolor=EVE, markersize=7, label="Eve: intercept–resend, fraction $f$"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor=NOISE,
               markeredgecolor=INK, markersize=7, label="depolarising channel $\\mathcal{N}_p$"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=7.4,
               frameon=False, bbox_to_anchor=(0.5, 0.030), handletextpad=0.4, columnspacing=1.6)
    fig.savefig(f"{OUT}/{name}.pdf"); fig.savefig(f"{OUT}/{name}.svg")
    fig.savefig(f"{OUT}/{name}.png", dpi=220); plt.close(fig)


if __name__ == "__main__":
    circuits_panel()
    print(f"wrote {OUT}/fig_circuits_all.{{pdf,svg,png}}")
