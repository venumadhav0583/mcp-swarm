import json, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
a = json.load(open("../results/analysis.json")); w = json.load(open("../results/analysis_weighted.json")); C = a["configs"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7})
rows = [("Best single model (Qwen2.5)", C["single_best"]["acc"], None, C["single_best"]["tokens"], "#20808D"),
        ("Fixed-4 best, test-selected", C["fixed4_best_oracle"]["acc"], None, C["fixed4_best_oracle"]["tokens"], "#7A7974"),
        ("Rotational, quality-weighted*", w["sel_and_vote"]["acc"], w["sel_and_vote"]["sd"], w["tokens"], "#DA7101"),
        ("Fixed-4 a priori, Eq. 2", C["fixed4_apriori_consensus"]["acc"], None, C["fixed4_apriori_consensus"]["tokens"], "#7A7974"),
        ("Rotational, confidence only", C["rotational4_confidence_only"]["acc"], C["rotational4_confidence_only"]["acc_sd"], C["rotational4_confidence_only"]["tokens"], "#1B474D"),
        ("All seven, Eq. 2", C["council_all7_consensus"]["acc"], None, C["council_all7_consensus"]["tokens"], "#7A7974"),
        ("Random-4, Eq. 2", C["random4_consensus"]["acc"], C["random4_consensus"]["acc_sd"], C["random4_consensus"]["tokens"], "#7A7974"),
        ("Rotational, Eq. 2", C["rotational4_consensus"]["acc"], C["rotational4_consensus"]["acc_sd"], C["rotational4_consensus"]["tokens"], "#1B474D"),
        ("Rotational, plurality vote", C["rotational4_plurality"]["acc"], C["rotational4_plurality"]["acc_sd"], C["rotational4_plurality"]["tokens"], "#1B474D"),
        ("Round-robin single model", C["single_round_robin"]["acc"], None, C["single_round_robin"]["tokens"], "#7A7974"),
        ("Mean of seven single models", a["mean_single_acc"], None, 141, "#7A7974")]
fig, ax = plt.subplots(figsize=(3.45, 2.75))
for k, (lab, acc, sd, tok, col) in enumerate(rows):
    y = len(rows) - 1 - k
    ax.errorbar(acc*100, y, xerr=sd*100 if sd else None, fmt="o", ms=4.5, color=col, capsize=2, lw=0.9)
    ax.text(66.5, y, f"{tok:.0f}", va="center", ha="right", fontsize=6.8, color="#28251D")
ax.text(66.5, len(rows) - 0.3, "tokens", va="bottom", ha="right", fontsize=6.8, color="#7A7974")
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=6.8)
ax.axvline(C["single_best"]["acc"]*100, color="#20808D", lw=0.7, ls=":")
ax.axvline(25, color="#BAB9B4", lw=0.7, ls="--"); ax.text(25.4, -0.85, "chance", fontsize=6.3, color="#7A7974")
ax.set_xlim(22, 67); ax.set_ylim(-1.1, len(rows) - 0.1); ax.set_xlabel("Accuracy on 300 MMLU questions (%)")
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.grid(axis="x", color="#EAE9E5", lw=0.5); ax.set_axisbelow(True)
fig.tight_layout(pad=0.3); fig.savefig("figs/fig2_council.pdf"); fig.savefig("figs/fig2_council.png", dpi=600)
