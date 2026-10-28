import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams.update({"font.family": "DejaVu Sans", "mathtext.fontset": "dejavusans"})
fig, ax = plt.subplots(figsize=(7.0, 3.35)); ax.set_xlim(0, 100); ax.set_ylim(-5, 100); ax.axis("off")
TEAL, GREY, INK = "#1B474D", "#6B6A66", "#28251D"
def box(x, y, w, h, title, sub, dashed=False, fill="#FFFFFF"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", lw=1.3,
        ec=GREY if dashed else TEAL, fc=fill, ls=(0, (4, 2)) if dashed else "-"))
    ax.text(x + w/2, y + h - 2.5, title, ha="center", va="top", fontsize=9.6, weight="bold", color=INK)
    ax.text(x + w/2, y + h - 9.0, sub, ha="center", va="top", fontsize=8.0, color=INK, linespacing=1.3)
def arrow(x1, y1, x2, y2, both=True):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="<|-|>" if both else "-|>", lw=1.1, color=INK, mutation_scale=9))
box(0.5, 76, 27, 21, "Enterprise client", "query in, answer out\nstatus stream (SSE)", dashed=True)
box(33, 76, 66.5, 21, "Supervisor agent", "task decomposition, routing, per-node deadlines\norchestration designed as a LangGraph StateGraph", dashed=True)
arrow(27.5, 86.5, 33, 86.5)
box(0.5, 37, 32, 31, "Rotational council", "select 4 of 7 models (Eq. 1)\nparallel calls with a deadline\nscore $S_i=\\alpha C_i+\\beta A_i$ (Eq. 2)", fill="#EEF6F7")
box(34, 37, 32, 31, "Persistent memory", "ChromaDB + MiniLM vectors\ninject only if sim. $\\geq\\tau$ (Eq. 3)\nprovenance, retention rules", fill="#EEF6F7")
box(67.5, 37, 32, 31, "MCP gateway", "task-scoped signed tokens\nscope and expiry checks\napproval for high-risk calls", fill="#EEF6F7")
for x in (16.25, 50, 83.75): arrow(x, 76, x, 68)
box(0.5, 4, 55, 24, "MCP servers", "Resources / Prompts / Tools\ninternal records and business APIs")
box(60, 4, 39.5, 24, "Document parsing service", "exposed as an MCP resource\nnot evaluated in this paper", dashed=True)
arrow(75, 37, 40, 28, both=False); arrow(90, 37, 85, 28, both=False)
ax.text(28, 32.5, "authorized calls only", fontsize=8.2, color=GREY, ha="center", va="center", style="italic")
ax.plot([62, 66], [-2.6, -2.6], color=TEAL, lw=1.2); ax.text(66.8, -2.6, "evaluated", fontsize=8.2, va="center")
ax.plot([78, 82], [-2.6, -2.6], color=GREY, lw=1.2, ls=(0, (4, 2))); ax.text(82.8, -2.6, "design only", fontsize=8.2, va="center")
fig.savefig("figs/fig1_arch.pdf", bbox_inches="tight", pad_inches=0.02); fig.savefig("figs/fig1_arch.png", dpi=600, bbox_inches="tight", pad_inches=0.02)
