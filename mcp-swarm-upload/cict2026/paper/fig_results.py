"""Fig. 2 (camera-ready): (a) accuracy of single models and councils; (b) accuracy and cost against council size.
Readable in greyscale print: groups are separated by marker shape and labels, not by colour alone."""
import json, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
a = json.load(open("../results/analysis.json")); w = json.load(open("../results/analysis_weighted.json"))
s = json.load(open("../results/analysis_scaling.json")); C = a["configs"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.linewidth": 0.6,
                     "xtick.major.width": 0.6, "ytick.major.width": 0.6, "pdf.fonttype": 42})
INK, MUTED, GRID = "#28251D", "#6B6A66", "#E4E3DF"
BEST, ROT, OTHER = "#0F5C66", "#C2570C", "#5F5E5A"
best = C["single_best"]["acc"] * 100
# (label, acc, sd, ci, tokens, colour, marker)
rows = [
 ("Best single model (Qwen2.5)", C["single_best"], None, BEST, "D"),
 ("Fixed-4, best on test set", C["fixed4_best_oracle"], None, OTHER, "s"),
 ("Rotational, quality-weighted*", {"acc": w["sel_and_vote"]["acc"], "tokens": w["tokens"]}, w["sel_and_vote"]["sd"], ROT, "o"),
 ("Fixed-4 a priori, Eq. 2", C["fixed4_apriori_consensus"], None, OTHER, "s"),
 ("Rotational, confidence only", C["rotational4_confidence_only"], C["rotational4_confidence_only"]["acc_sd"], ROT, "o"),
 ("All seven, Eq. 2", C["council_all7_consensus"], None, OTHER, "s"),
 ("Random-4, Eq. 2", C["random4_consensus"], C["random4_consensus"]["acc_sd"], OTHER, "^"),
 ("Rotational, Eq. 2", C["rotational4_consensus"], C["rotational4_consensus"]["acc_sd"], ROT, "o"),
 ("Rotational, plurality vote", C["rotational4_plurality"], C["rotational4_plurality"]["acc_sd"], ROT, "o"),
 ("Round-robin single model", C["single_round_robin"], None, OTHER, "D"),
]
fig, (ax, bx) = plt.subplots(2, 1, figsize=(3.45, 4.35), gridspec_kw={"height_ratios": [1.35, 1]})
n = len(rows)
for k, (lab, d, sd, col, mk) in enumerate(rows):
    y = n - 1 - k
    ax.errorbar(d["acc"] * 100, y, xerr=sd * 100 if sd else None, fmt=mk, ms=5, color=col, mec="white", mew=0.6,
                capsize=2.2, elinewidth=1.0, zorder=3)
    ax.text(70.5, y, f"{d['tokens']:.0f}", va="center", ha="right", fontsize=7.5, color=INK)
ax.text(70.5, n - 0.35, "tokens/query", va="bottom", ha="right", fontsize=7, color=MUTED)
ax.set_yticks(range(n)); ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=7.5)
ax.axvline(best, color=BEST, lw=0.8, ls=":", zorder=1)
ax.axvline(25, color=MUTED, lw=0.7, ls="--", zorder=1); ax.text(25.6, -0.75, "chance", fontsize=7, color=MUTED)
ax.set_xlim(22, 71.5); ax.set_ylim(-1.0, n - 0.1)
ax.set_xticks([30, 40, 50, 60]); ax.set_xlabel("Accuracy on 300 questions (%)", fontsize=8, labelpad=2)

# (b) council size
ks = list(range(1, 8)); S = s["sizes"]
mean = [S[str(k)]["acc_mean"] * 100 for k in ks]; lo = [S[str(k)]["acc_min"] * 100 for k in ks]
hi = [S[str(k)]["acc_max"] * 100 for k in ks]
bx.fill_between(ks, lo, hi, color="#D9D8D3", lw=0, zorder=1, label="range, all councils of size $k$")
bx.plot(ks, mean, "-o", color=ROT, ms=4.5, lw=1.4, mec="white", mew=0.6, zorder=3, label="mean")
bx.axhline(best, color=BEST, lw=0.9, ls=":", zorder=2); bx.text(7.15, best + 0.8, "best single", fontsize=7, color=BEST, ha="right")
bx.axhline(25, color=MUTED, lw=0.7, ls="--"); bx.text(7.15, 25.8, "chance", fontsize=7, color=MUTED, ha="right")
bx.set_xticks(ks)
bx.set_xticklabels([f"{k}\n{S[str(k)]['tokens']:.0f}\n{S[str(k)]['par_s']:.1f}" for k in ks], fontsize=7.5)
bx.text(0.25, -0.115, "$k$\ntokens\npar. s", transform=bx.get_xaxis_transform(), ha="right", va="top", fontsize=7,
        color=MUTED, linespacing=1.18)
bx.set_xlim(0.7, 7.3); bx.set_ylim(22, 62); bx.set_yticks([30, 40, 50, 60]); bx.set_ylabel("Accuracy (%)", fontsize=8)

for g in (ax, bx):
    for sp in ("top", "right"): g.spines[sp].set_visible(False)
    g.tick_params(colors=INK, length=2.5)
ax.grid(axis="x", color=GRID, lw=0.5); bx.grid(axis="y", color=GRID, lw=0.5)
for g in (ax, bx): g.set_axisbelow(True)
L, R = 0.475, 0.985
ax.set_position([L, 0.535, R - L, 0.415]); bx.set_position([L, 0.12, R - L, 0.27])
fig.text(0.01, 0.985, "(a) Single model vs. councils; bars: $\\pm$1 SD over 10 seeds", fontsize=8, va="top", color=INK)
fig.text(0.01, 0.428, "(b) Council size $k$: all $\\binom{7}{k}$ fixed councils, Eq. 2", fontsize=8, va="top", color=INK)
fig.savefig("figs/fig2_council.pdf"); fig.savefig("figs/fig2_council.png", dpi=600)
