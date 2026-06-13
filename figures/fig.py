"""
Master figure script for the QKD paper. Each figure is a function; every figure is
saved as PDF (for LaTeX) + SVG (editable in Inkscape/Illustrator/draw.io) + PNG (preview).
Edit colours/labels here or in the SVG. Run: python paper_figures.py
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Wedge
from matplotlib.lines import Line2D

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "mathtext.fontset": "cm",
    "axes.linewidth": 0.8, "savefig.bbox": "tight", "savefig.pad_inches": 0.03,
})
INK="#1a1a1a"; HON="#2c6fbb"; EVE="#c2452d"; GREY="#777777"; LIGHT="#e8edf3"
ACC="#2c6fbb"; ACC2="#3a8a5f"; ACC3="#9a6db0"
OUT = "figures"
os.makedirs(OUT, exist_ok=True)

def save(fig, name):
    fig.savefig(f"{OUT}/{name}.pdf"); fig.savefig(f"{OUT}/{name}.svg")
    fig.savefig(f"{OUT}/{name}.png", dpi=200); plt.close(fig)

# ===========================================================================
# Re-export the two existing conceptual figures (so they also exist as SVG)
# ===========================================================================
def system_model():
    fig, ax = plt.subplots(figsize=(7.0, 2.8)); ax.set_xlim(0,10); ax.set_ylim(0,4.4); ax.axis("off")
    def party(x,y,l):
        ax.add_patch(FancyBboxPatch((x-0.85,y-0.55),1.7,1.1,boxstyle="round,pad=0.02,rounding_size=0.12",
            lw=1.3,edgecolor=INK,facecolor=LIGHT,zorder=3)); ax.text(x,y,l,ha="center",va="center",fontsize=11,zorder=4)
    party(1.2,2.0,"Alice"); party(8.8,2.0,"Bob")
    ax.annotate("",xy=(7.95,3.0),xytext=(2.05,3.0),arrowprops=dict(arrowstyle="-|>",lw=1.6,color=INK))
    ax.text(5.0,3.78,"Quantum channel:  qubits / entangled pairs",ha="center",va="bottom",fontsize=8.5)
    ax.add_patch(FancyBboxPatch((4.15,2.62),1.7,0.78,boxstyle="round,pad=0.02,rounding_size=0.10",
        lw=1.3,edgecolor=EVE,facecolor="white",zorder=5))
    ax.text(5.0,3.12,"Eve",ha="center",va="center",color=EVE,fontsize=10,zorder=6)
    ax.text(5.0,2.46,r"intercept–resend, fraction $f$",ha="center",va="top",color=EVE,fontsize=8,zorder=6)
    ax.annotate("",xy=(7.95,1.0),xytext=(2.05,1.0),arrowprops=dict(arrowstyle="<|-|>",lw=1.4,color=GREY))
    ax.text(5.0,1.18,"(Eve may listen but cannot alter)",ha="center",va="bottom",fontsize=7.5,color=GREY,style="italic")
    ax.text(5.0,0.74,"Authenticated classical channel:  sifting, reconciliation, parameter estimation",
            ha="center",va="top",fontsize=8.5,color=GREY)
    save(fig,"fig_system_model")

def _g(x,mu,sd): return np.exp(-0.5*((x-mu)/sd)**2)
def detection_decision():
    fig,axes=plt.subplots(1,2,figsize=(7.0,2.95))
    ax=axes[0]; x=np.linspace(0,0.30,700); hon=_g(x,0.090,0.027); eve=_g(x,0.185,0.033); thr=0.135
    ax.plot(x,hon,color=HON,lw=1.6); ax.plot(x,eve,color=EVE,lw=1.6)
    ax.fill_between(x[x>=thr],0,hon[x>=thr],color=HON,alpha=0.45,lw=0)
    ax.fill_between(x[x<=thr],0,eve[x<=thr],color=EVE,alpha=0.40,lw=0)
    ax.axvline(thr,color=INK,lw=1.1,ls="--")
    ax.text(0.137,1.30,"threshold 0.135",fontsize=7.0,va="top",ha="center")
    ax.text(0.090,1.06,"honest\n(noise)",color=HON,fontsize=7.6,ha="center",va="bottom")
    ax.text(0.205,1.06,"eavesdropper",color=EVE,fontsize=7.6,ha="center",va="bottom")
    ax.annotate("FPR",xy=(0.150,0.06),xytext=(0.225,0.46),fontsize=8,color=HON,arrowprops=dict(arrowstyle="-|>",color=HON,lw=0.9))
    ax.annotate("FNR",xy=(0.122,0.06),xytext=(0.018,0.46),fontsize=8,color=EVE,arrowprops=dict(arrowstyle="-|>",color=EVE,lw=0.9))
    ax.set_xlim(0,0.285); ax.set_ylim(0,1.45); ax.set_yticks([]); ax.set_xlabel("QBER")
    ax.set_title("(a) BB84 / six-state:  alarm if QBER $\\geq$ threshold",fontsize=8); ax.tick_params(labelsize=7.5)
    ax=axes[1]; x=np.linspace(1.3,2.9,700); hon=_g(x,2.22,0.12); eve=_g(x,1.80,0.15); thr=2.0
    ax.plot(x,hon,color=HON,lw=1.6); ax.plot(x,eve,color=EVE,lw=1.6)
    ax.fill_between(x[x<=thr],0,hon[x<=thr],color=HON,alpha=0.45,lw=0)
    ax.fill_between(x[x>=thr],0,eve[x>=thr],color=EVE,alpha=0.40,lw=0)
    ax.axvline(thr,color=INK,lw=1.1,ls="--")
    ax.text(2.0,1.30,"threshold $S=2$",fontsize=7.0,va="top",ha="center")
    ax.text(2.40,1.06,"honest",color=HON,fontsize=7.6,ha="center",va="bottom")
    ax.text(1.66,1.06,"eavesdropper",color=EVE,fontsize=7.6,ha="center",va="bottom")
    ax.annotate("FPR",xy=(1.90,0.06),xytext=(1.45,0.46),fontsize=8,color=HON,arrowprops=dict(arrowstyle="-|>",color=HON,lw=0.9))
    ax.annotate("FNR",xy=(2.12,0.06),xytext=(2.58,0.46),fontsize=8,color=EVE,arrowprops=dict(arrowstyle="-|>",color=EVE,lw=0.9))
    ax.set_xlim(1.35,2.85); ax.set_ylim(0,1.45); ax.set_yticks([]); ax.set_xlabel("CHSH parameter $S$")
    ax.set_title("(b) E91:  alarm if $S <$ threshold",fontsize=8); ax.tick_params(labelsize=7.5)
    handles=[Line2D([0],[0],color=HON,lw=1.6,label="honest channel (no Eve)"),
             Line2D([0],[0],color=EVE,lw=1.6,label="eavesdropper present")]
    fig.legend(handles=handles,loc="lower center",ncol=2,fontsize=7.6,frameon=False,bbox_to_anchor=(0.5,-0.04))
    fig.tight_layout(rect=[0,0.03,1,1]); save(fig,"fig_detection_decision")

# ===========================================================================
# Circuit-drawing helpers
# ===========================================================================
def wire(ax,y,x0,x1,color=INK): ax.plot([x0,x1],[y,y],color=color,lw=1.0,zorder=1)
def gate(ax,x,y,label,w=0.62,h=0.52,fc="white",ec=INK,fs=9.5):
    ax.add_patch(Rectangle((x-w/2,y-h/2),w,h,facecolor=fc,edgecolor=ec,lw=1.1,zorder=3))
    ax.text(x,y,label,ha="center",va="center",fontsize=fs,zorder=4)
def meas(ax,x,y,w=0.62,h=0.52):
    ax.add_patch(Rectangle((x-w/2,y-h/2),w,h,facecolor="white",edgecolor=INK,lw=1.1,zorder=3))
    th=np.linspace(0.18*np.pi,0.82*np.pi,40)
    ax.plot(x+0.17*np.cos(th),y-0.09+0.17*np.sin(th),color=INK,lw=0.9,zorder=4)
    ax.annotate("",xy=(x+0.13,y+0.11),xytext=(x,y-0.09),arrowprops=dict(arrowstyle="-",lw=0.9,color=INK),zorder=4)
def sep(ax,x,y0,y1,label=None):
    ax.plot([x,x],[y0,y1],color=GREY,lw=0.8,ls=(0,(3,3)),zorder=1)
    if label: ax.text(x,y1+0.12,label,ha="center",va="bottom",fontsize=7.5,color=GREY)
def note(ax,x,y,t,fs=7.0): ax.text(x,y,t,ha="center",va="top",fontsize=fs,color=GREY,style="italic")

def circuit_bb84():
    fig,ax=plt.subplots(figsize=(7.0,1.95)); ax.set_xlim(0,11.4); ax.set_ylim(-1.1,1.5); ax.axis("off")
    y=0.0; wire(ax,y,0.55,10.7)
    ax.text(0.3,y,r"$|0\rangle$",ha="right",va="center",fontsize=10)
    gate(ax,1.4,y,"$X$"); note(ax,1.4,-0.4,"bit $a$")
    gate(ax,2.4,y,"$H$"); note(ax,2.4,-0.4,"basis")
    sep(ax,3.0,-0.55,0.55)
    gate(ax,3.7,y,"$H$",ec=EVE); meas(ax,4.6,y); gate(ax,5.5,y,"$H$",ec=EVE)
    ax.add_patch(Rectangle((3.25,-0.45),2.6,0.9,fill=False,ec=EVE,lw=0.9,ls=(0,(2,2)),zorder=2))
    ax.text(4.55,0.78,"Eve  (prob. $f$)",ha="center",va="bottom",fontsize=7.8,color=EVE)
    sep(ax,6.15,-0.55,0.55)
    gate(ax,6.85,y,"$\\mathcal{N}_p$",fc="#f3eee6"); note(ax,6.85,-0.4,"noise")
    sep(ax,7.55,-0.55,0.55)
    gate(ax,8.3,y,"$H$"); note(ax,8.3,-0.4,"basis"); meas(ax,9.3,y)
    ax.text(1.9,1.18,"Alice: prepare",ha="center",fontsize=8); 
    ax.text(8.8,1.18,"Bob: measure",ha="center",fontsize=8)
    ax.text(6.85,1.18,"channel",ha="center",fontsize=8,color=GREY)
    ax.text(5.7,-0.92,"$H$ gates applied only when the random basis is the diagonal ($X$) basis",
            ha="center",fontsize=6.8,color=GREY,style="italic")
    save(fig,"fig_circuit_bb84")

def circuit_sixstate():
    fig,ax=plt.subplots(figsize=(7.0,1.95)); ax.set_xlim(0,11.8); ax.set_ylim(-1.1,1.5); ax.axis("off")
    y=0.0; wire(ax,y,0.55,11.1)
    ax.text(0.3,y,r"$|0\rangle$",ha="right",va="center",fontsize=10)
    gate(ax,1.4,y,"$X$"); note(ax,1.4,-0.4,"bit $a$")
    gate(ax,2.35,y,"$H$"); gate(ax,3.15,y,"$S$")
    note(ax,2.75,-0.4,"$Y$-basis: $SH$")
    sep(ax,3.75,-0.55,0.55)
    gate(ax,4.45,y,"$S^{\\dagger}$",ec=EVE,fs=8.5); gate(ax,5.25,y,"$H$",ec=EVE); meas(ax,6.05,y); 
    ax.add_patch(Rectangle((4.0,-0.45),2.45,0.9,fill=False,ec=EVE,lw=0.9,ls=(0,(2,2)),zorder=2))
    ax.text(5.0,0.78,"Eve  (prob. $f$)",ha="center",va="bottom",fontsize=7.8,color=EVE)
    sep(ax,6.7,-0.55,0.55)
    gate(ax,7.35,y,"$\\mathcal{N}_p$",fc="#f3eee6"); note(ax,7.35,-0.4,"noise")
    sep(ax,8.0,-0.55,0.55)
    gate(ax,8.7,y,"$S^{\\dagger}$",fs=8.5); gate(ax,9.5,y,"$H$"); meas(ax,10.3,y)
    ax.text(2.4,1.18,"Alice: prepare",ha="center",fontsize=8)
    ax.text(9.5,1.18,"Bob: measure",ha="center",fontsize=8)
    ax.text(7.35,1.18,"channel",ha="center",fontsize=8,color=GREY)
    ax.text(5.9,-0.92,"third basis $Y$ uses $SH$ to prepare and $S^{\\dagger}H$ to measure; $Z,X$ as in BB84",
            ha="center",fontsize=6.8,color=GREY,style="italic")
    save(fig,"fig_circuit_sixstate")

def circuit_e91():
    fig,ax=plt.subplots(figsize=(7.0,2.6)); ax.set_xlim(0,11.6); ax.set_ylim(-2.2,1.9); ax.axis("off")
    yA=0.7; yB=-0.7; wire(ax,yA,0.75,10.9); wire(ax,yB,0.75,10.9)
    ax.text(0.5,yA,r"$|0\rangle$",ha="right",va="center",fontsize=10)
    ax.text(0.5,yB,r"$|0\rangle$",ha="right",va="center",fontsize=10)
    ax.text(0.62,yA+0.55,"Alice",ha="center",fontsize=7.5,color=GREY)
    ax.text(0.62,yB-0.55,"Bob",ha="center",fontsize=7.5,color=GREY)
    # Bell pair
    gate(ax,1.5,yA,"$H$")
    ax.add_patch(Circle((2.4,yA),0.075,color=INK,zorder=4))           # control
    ax.plot([2.4,2.4],[yA,yB],color=INK,lw=1.0,zorder=2)              # vertical
    ax.add_patch(Circle((2.4,yB),0.18,fill=False,ec=INK,lw=1.1,zorder=4)) # target
    ax.plot([2.22,2.58],[yB,yB],color=INK,lw=1.0,zorder=5); ax.plot([2.4,2.4],[yB-0.18,yB+0.18],color=INK,lw=1.0,zorder=5)
    ax.text(1.95,1.6,"Bell source",ha="center",fontsize=8)
    sep(ax,3.1,-1.05,1.05)
    gate(ax,3.8,yA,"$\\mathcal{N}_p$",fc="#f3eee6"); gate(ax,3.8,yB,"$\\mathcal{N}_p$",fc="#f3eee6")
    ax.text(3.8,1.6,"channel",ha="center",fontsize=8,color=GREY)
    sep(ax,4.5,-1.05,1.05)
    # Eve on Bob's qubit
    gate(ax,5.2,yB,"$R_y(\\theta_E)$",w=0.95,ec=EVE,fs=8); meas(ax,6.25,yB); gate(ax,7.2,yB,"$R_y(\\!-\\theta_E)$",w=1.0,ec=EVE,fs=8)
    ax.add_patch(Rectangle((4.65,yB-0.5),3.05,1.0,fill=False,ec=EVE,lw=0.9,ls=(0,(2,2)),zorder=2))
    ax.text(6.15,yB-0.66,"Eve  (prob. $f$)",ha="center",va="top",fontsize=7.8,color=EVE)
    sep(ax,8.05,-1.05,1.05)
    # measurements along chosen axes
    gate(ax,8.9,yA,"$R_y(a)$",w=0.9,fs=8.5); meas(ax,10.0,yA)
    gate(ax,8.9,yB,"$R_y(b)$",w=0.9,fs=8.5); meas(ax,10.0,yB)
    ax.text(9.5,1.6,"measure",ha="center",fontsize=8)
    ax.text(5.8,-1.98,"matched axes form the key; the CHSH settings estimate $S$",
            ha="center",fontsize=6.8,color=GREY,style="italic")
    save(fig,"fig_circuit_e91")

# ===========================================================================
# Mutually unbiased bases: BB84 (Z,X) vs six-state (Z,X,Y)
# ===========================================================================
def basis_sphere(ax,title,three=False):
    ax.set_aspect("equal"); ax.axis("off"); ax.set_xlim(-1.6,1.6); ax.set_ylim(-1.7,1.8)
    ax.add_patch(Circle((0,0),1.0,fill=False,ec=GREY,lw=1.0))
    ax.add_patch(Wedge((0,0),1.0,0,360,width=0.0))
    # equator ellipse
    th=np.linspace(0,2*np.pi,100); ax.plot(np.cos(th),0.28*np.sin(th),color=GREY,lw=0.7,ls=(0,(2,2)))
    # Z axis (vertical)
    ax.annotate("",xy=(0,1.18),xytext=(0,-1.18),arrowprops=dict(arrowstyle="-|>",color=ACC,lw=1.6))
    ax.text(0,1.30,r"$|0\rangle$",ha="center",fontsize=8.5,color=ACC)
    ax.text(0,-1.34,r"$|1\rangle$",ha="center",fontsize=8.5,color=ACC)
    # X axis (horizontal)
    ax.annotate("",xy=(1.22,0),xytext=(-1.22,0),arrowprops=dict(arrowstyle="-|>",color=ACC2,lw=1.6))
    ax.text(1.34,0.02,r"$|+\rangle$",ha="left",fontsize=8.5,color=ACC2)
    ax.text(-1.34,0.02,r"$|-\rangle$",ha="right",fontsize=8.5,color=ACC2)
    if three:
        # Y axis (into page) -> draw as diagonal to suggest 3D depth
        ax.annotate("",xy=(0.86,0.60),xytext=(-0.86,-0.60),arrowprops=dict(arrowstyle="-|>",color=ACC3,lw=1.6))
        ax.text(0.95,0.66,r"$|{+}i\rangle$",ha="left",fontsize=8.5,color=ACC3)
        ax.text(-0.95,-0.66,r"$|{-}i\rangle$",ha="right",fontsize=8.5,color=ACC3)
    ax.text(0,-1.66,title,ha="center",va="top",fontsize=8.5)

def three_basis():
    fig,axes=plt.subplots(1,2,figsize=(6.4,3.0))
    basis_sphere(axes[0],"BB84:  two bases  $Z, X$",three=False)
    basis_sphere(axes[1],"Six-state:  three bases  $Z, X, Y$",three=True)
    fig.suptitle("Adding the third mutually unbiased basis", fontsize=9, y=1.0)
    fig.tight_layout(); save(fig,"fig_basis_mub")

# ===========================================================================
# Intro overview: the three protocols at a glance
# ===========================================================================
def intro_overview():
    fig,ax=plt.subplots(figsize=(7.0,3.0)); ax.set_xlim(0,12); ax.set_ylim(0,7.4); ax.axis("off")
    cards=[("BB84", ACC, ["Prepare-and-measure","2 bases  $Z, X$","Sifting  $\\approx 1/2$",
                          "Full attack QBER  $\\approx 25\\%$","Signal: QBER"]),
           ("Six-state", ACC2, ["Prepare-and-measure","3 bases  $Z, X, Y$","Sifting  $\\approx 1/3$",
                          "Full attack QBER  $\\approx 33\\%$","Signal: QBER"]),
           ("E91", ACC3, ["Entanglement-based","Bell pairs, random axes","Key from matched axes",
                          "Full attack  $S\\!\\to\\!1.4$","Signal: CHSH $S$"])]
    xs=[0.4,4.3,8.2]; w=3.4
    for (name,col,items),x0 in zip(cards,xs):
        ax.add_patch(FancyBboxPatch((x0,0.5),w,6.3,boxstyle="round,pad=0.04,rounding_size=0.15",
            lw=1.4,edgecolor=col,facecolor="white"))
        ax.add_patch(Rectangle((x0,6.0),w,0.8,facecolor=col,edgecolor=col,alpha=0.16,lw=0))
        ax.text(x0+w/2,6.4,name,ha="center",va="center",fontsize=12,color=col)
        for i,it in enumerate(items):
            ax.text(x0+0.25,5.45-i*0.95,"$\\bullet$",ha="left",va="center",fontsize=8,color=col)
            ax.text(x0+0.55,5.45-i*0.95,it,ha="left",va="center",fontsize=8.3)
    save(fig,"fig_intro_overview")

system_model(); detection_decision()
circuit_bb84(); circuit_sixstate(); circuit_e91()
three_basis(); intro_overview()
print("done: regenerated 2, built 5 new (3 circuits, basis, intro overview)")