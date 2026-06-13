"""
Methodology pipeline figure (Fig. 5) for the QKD paper.
Saves PDF (LaTeX) + SVG (editable) + PNG (preview) into a local 'figures' folder.
Run: python fig_pipeline.py
Edit box labels, colours, or spacing below and rerun.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "mathtext.fontset": "cm",
    "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
})
INK = "#1a1a1a"; HON = "#2c6fbb"; EVE = "#c2452d"; GREY = "#777777"
OUT = "figures"
os.makedirs(OUT, exist_ok=True)


def box(ax, x, y, title, sub=None, w=2.2, h=1.0, ec=INK, fc="white", tfs=7.0):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                 boxstyle="round,pad=0.03,rounding_size=0.10",
                 lw=1.2, edgecolor=ec, facecolor=fc, zorder=3))
    if sub:
        ax.text(x, y + 0.17, title, ha="center", va="center", fontsize=tfs, zorder=4)
        ax.text(x, y - 0.25, sub, ha="center", va="center", fontsize=5.8,
                color=GREY, style="italic", zorder=4)
    else:
        ax.text(x, y, title, ha="center", va="center", fontsize=tfs, zorder=4)


def arrow(ax, p0, p1):
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle="-|>", lw=1.3, color=INK))


def pipeline():
    fig, ax = plt.subplots(figsize=(7.5, 2.55))
    ax.set_xlim(0, 17.2); ax.set_ylim(0, 5); ax.axis("off")
    ym = 2.45
    hw = 1.1                                                  # half box width (w=2.2)
    s = [1.25, 3.7, 6.15, 8.4, 10.65, 12.9, 15.4]             # slot x-centres

    box(ax, s[0], ym, "Circuit\nconstruction", sub="BB84, 6-state, E91")
    box(ax, s[1], 3.55, "Synthetic noise", sub=r"depolarizing $\mathcal{N}_p$", h=0.86, ec=HON)
    box(ax, s[1], 1.35, "Device noise", sub=r"$\mathtt{ibm\_marrakesh}$", h=0.86, ec=HON)
    ax.text(s[1], 4.5, "Noise injection", ha="center", fontsize=7.2, color=GREY)
    box(ax, s[2], ym, "Partial\neavesdropper", sub=r"fraction $f$", ec=EVE)
    box(ax, s[3], ym, "Sifting", sub="basis reconc.")
    box(ax, s[4], ym, "Error\nreconciliation")
    box(ax, s[5], ym, "Privacy\namplification")
    box(ax, s[6], ym, "Detection stats", sub=r"FPR, FNR, $S$, SKR", w=2.6)

    arrow(ax, (s[0] + hw, ym), (s[1] - hw, 3.55))
    arrow(ax, (s[0] + hw, ym), (s[1] - hw, 1.35))
    arrow(ax, (s[1] + hw, 3.55), (s[2] - hw, ym))
    arrow(ax, (s[1] + hw, 1.35), (s[2] - hw, ym))
    for a, b in zip(s[2:6], s[3:7]):
        rhw = 1.3 if b == s[6] else hw                        # detection box is wider
        arrow(ax, (a + hw, ym), (b - rhw, ym))

    fig.savefig(f"{OUT}/fig_pipeline.pdf")
    fig.savefig(f"{OUT}/fig_pipeline.svg")
    fig.savefig(f"{OUT}/fig_pipeline.png", dpi=200)
    plt.close(fig)
    print(f"wrote {OUT}/fig_pipeline.[pdf|svg|png]")


pipeline()