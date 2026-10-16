"""Exploratory, cross-fitted: Eq.1 base weights w_m from held-out-fold accuracy above chance."""
import json, numpy as np
from analyze import *  # reruns base analysis (deterministic), reuses helpers
fold = np.array([i % 2 for i in range(N)])
def weights(train_mask):
    return {m: max(single_correct[m][train_mask].mean() - 0.25, 0.01) for m in MODELS}
class WRot(Rotation):
    def __init__(self, seed, w, bonus=0.15):
        super().__init__(seed, bonus); self.w = w; self.scale = np.mean(list(w.values()))
    def select(self, k=4):
        wt = np.array([self.w[m] / self.scale + self.bonus * self.idle[m] for m in MODELS]); p = wt / wt.sum()
        idx = self.rng.choice(7, size=k, replace=False, p=p); ch = [MODELS[j] for j in idx]
        for m in MODELS:
            if m in ch: self.idle[m] = 0; self.counts[m] += 1
            else: self.idle[m] += 1
        return ch
def wagg(members, i, w):
    recs = [member(m, i) for m in members]; tot = sum(w[m] for m in members); sc = {}
    for m, r in zip(members, recs):
        agree = sum(w[o] for o, ro in zip(members, recs) if ro["answer"] == r["answer"] and o != m) / max(tot - w[m], 1e-9)
        s = 0.5 * r["confidence"] + 0.5 * agree
        sc[r["answer"]] = max(sc.get(r["answer"], -1), s)
    return max(sc, key=sc.get)
res = {"sel_only": [], "sel_and_vote": [], "selection_share": []}
for s in range(1, 11):
    corrA = np.zeros(N, bool); corrB = np.zeros(N, bool); cnt = {m: 0 for m in MODELS}; lat = []; tok = []
    for f in (0, 1):
        w = weights(fold != f); rot = WRot(s * 10 + f, w)
        for i in np.where(fold == f)[0]:
            c = rot.select(); corrA[i] = aggregate(c, i) == GOLD[i]; corrB[i] = wagg(c, i, w) == GOLD[i]
            k = cost(c, i); lat.append(k["par_s"]); tok.append(k["tokens"])
        for m in MODELS: cnt[m] += rot.counts[m]
    res["sel_only"].append((corrA.mean(), mcnemar(single_correct[best], corrA)))
    res["sel_and_vote"].append((corrB.mean(), mcnemar(single_correct[best], corrB)))
    res["selection_share"].append({m: cnt[m] / (4 * N) for m in MODELS})
o = {}
for k in ("sel_only", "sel_and_vote"):
    a = [x[0] for x in res[k]]; p = [x[1][2] for x in res[k]]
    o[k] = {"acc": float(np.mean(a)), "sd": float(np.std(a, ddof=1)), "min": float(min(a)), "max": float(max(a)),
            "p_range": [float(min(p)), float(max(p))], "gains_losses_seed1": res[k][0][1][:2]}
o["selection_share_mean"] = {m: float(np.mean([d[m] for d in res["selection_share"]])) for m in MODELS}
o["par_s"] = float(np.mean(lat)); o["tokens"] = float(np.mean(tok))
(ROOT/"results/analysis_weighted.json").write_text(json.dumps(o, indent=1)); print(json.dumps(o, indent=1))
