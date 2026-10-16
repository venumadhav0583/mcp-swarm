"""Offline analysis of cached per-model answers: single models, councils, rotation, ablations, failures."""
import json, itertools, math
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "results/raw"
MODELS = ["qwen2.5-1.5b","llama3.2-1b","gemma3-1b","smollm2-1.7b","granite3.1-1b","falcon3-1b","olmo2-1b"]
qs = [json.loads(l) for l in (ROOT/"data/eval300.jsonl").read_text().splitlines()]
QID = [q["qid"] for q in qs]; GOLD = np.array([q["answer"] for q in qs]); DOM = np.array([q["domain"] for q in qs])
R = {}
for m in MODELS:
    recs = {r["qid"]: r for r in map(json.loads, (RAW/f"{m}.jsonl").read_text().splitlines())}
    R[m] = [recs[q] for q in QID]
N = len(QID); B = 10000; rng0 = np.random.default_rng(20261015)
BOOT = rng0.integers(0, N, size=(B, N))
def ci(correct):
    c = np.asarray(correct, float); s = c[BOOT].mean(1)
    return float(c.mean()), float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))
def mcnemar(a, b):
    a = np.asarray(a, bool); b = np.asarray(b, bool)
    n01 = int((~a & b).sum()); n10 = int((a & ~b).sum()); n = n01 + n10
    if n == 0: return n01, n10, 1.0
    k = min(n01, n10)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n * 2
    return n01, n10, min(1.0, p)
def member(m, i): return R[m][i]
def aggregate(members, i, mode="consensus", alpha=0.5, beta=0.5):
    recs = [member(m, i) for m in members]
    ans = [r["answer"] for r in recs]; conf = [r["confidence"] for r in recs]
    valid = [j for j, a in enumerate(ans) if a is not None]
    if not valid: return None
    if mode == "plurality":
        cnt = {}
        for j in valid: cnt[ans[j]] = cnt.get(ans[j], 0) + 1
        top = max(cnt.values()); tied = [a for a, c in cnt.items() if c == top]
        if len(tied) == 1: return tied[0]
        return tied[int(rng0.integers(len(tied)))]  # random tie-break (no confidence)
    k = len(valid)
    scores = []
    for j in valid:
        agree = (sum(ans[l] == ans[j] for l in valid) - 1) / (k - 1) if k > 1 else 1.0
        c = conf[j] if mode != "agreement_only" else 0
        a = agree if mode != "confidence_only" else 0
        scores.append(alpha * c + beta * a)
    return ans[valid[int(np.argmax(scores))]]
def cost(members, i):
    recs = [member(m, i) for m in members]
    lat = [r["latency_s"] for r in recs]
    return {"seq_s": sum(lat), "par_s": max(lat), "tokens": sum(r["prompt_tokens"] + r["completion_tokens"] for r in recs)}
def evaluate(council_per_q, mode="consensus"):
    pred = [aggregate(c, i, mode) for i, c in enumerate(council_per_q)]
    correct = np.array([p == g for p, g in zip(pred, GOLD)])
    cs = [cost(c, i) for i, c in enumerate(council_per_q)]
    return correct, {k: float(np.mean([c[k] for c in cs])) for k in cs[0]}
class Rotation:
    """Eq. 1: P(select m) proportional to base weight + bonus * queries since last selection."""
    def __init__(self, seed, bonus=0.15):
        self.rng = np.random.default_rng(seed); self.idle = {m: 0 for m in MODELS}; self.bonus = bonus
        self.counts = {m: 0 for m in MODELS}
    def select(self, k=4):
        w = np.array([1.0 + self.bonus * self.idle[m] for m in MODELS]); p = w / w.sum()
        idx = self.rng.choice(len(MODELS), size=k, replace=False, p=p); ch = [MODELS[j] for j in idx]
        for m in MODELS:
            if m in ch: self.idle[m] = 0; self.counts[m] += 1
            else: self.idle[m] += 1
        return ch
out = {"n_questions": N, "bootstrap": B, "models": {}}
single_correct = {}
for m in MODELS:
    c = np.array([r["answer"] == g for r, g in zip(R[m], GOLD)]); single_correct[m] = c
    lat = np.array([r["latency_s"] for r in R[m]])
    out["models"][m] = {"acc": ci(c), "invalid": int(sum(r["answer"] is None for r in R[m])),
        "lat_mean": float(lat.mean()), "lat_p50": float(np.percentile(lat, 50)), "lat_p95": float(np.percentile(lat, 95)),
        "tokens": float(np.mean([r["prompt_tokens"] + r["completion_tokens"] for r in R[m]])),
        "by_domain": {d: float(c[DOM == d].mean()) for d in ["finance","law","technology"]}}
best = max(MODELS, key=lambda m: single_correct[m].mean()); out["best_single"] = best
configs = {}
def add(name, correct, costs, extra=None):
    a, lo, hi = ci(correct); n01, n10, p = mcnemar(single_correct[best], correct)
    configs[name] = {"acc": a, "ci": [lo, hi], **costs, "vs_best_single": {"gains": n01, "losses": n10, "p_mcnemar": p},
                     "by_domain": {d: float(np.asarray(correct)[DOM == d].mean()) for d in ["finance","law","technology"]}, **(extra or {})}
c, k = evaluate([[best]] * N); add("single_best", c, k)
mean_single = float(np.mean([single_correct[m].mean() for m in MODELS]))
# round-robin single model (rotation without consensus)
rr = [[MODELS[i % 7]] for i in range(N)]; c, k = evaluate(rr); add("single_round_robin", c, k)
c, k = evaluate([MODELS] * N); add("council_all7_consensus", c, k)
c, k = evaluate([MODELS] * N, "plurality"); add("council_all7_plurality", c, k)
combos = list(itertools.combinations(MODELS, 4)); fixed = []
for cb in combos:
    cc, kk = evaluate([list(cb)] * N); fixed.append((cb, cc.mean(), kk))
fixed.sort(key=lambda x: x[1])
out["fixed4_distribution"] = {"n": len(fixed), "min": fixed[0][1], "median": float(np.median([f[1] for f in fixed])),
    "max": fixed[-1][1], "best_combo": fixed[-1][0], "worst_combo": fixed[0][0]}
# a-priori fixed council: four largest models by parameter count
apriori = ["smollm2-1.7b", "qwen2.5-1.5b", "llama3.2-1b", "gemma3-1b"]
c, k = evaluate([apriori] * N); add("fixed4_apriori_consensus", c, k, {"members": apriori})
c, k = evaluate([list(fixed[-1][0])] * N); add("fixed4_best_oracle", c, k, {"members": list(fixed[-1][0]), "note": "selected on test set; optimistic"})
seeds = list(range(1, 11)); rot_runs = {"consensus": [], "plurality": [], "confidence_only": [], "agreement_only": []}
rand_runs = []; cvs = []
for s in seeds:
    rot = Rotation(s); councils = [rot.select() for _ in range(N)]
    v = np.array(list(rot.counts.values()), float); cvs.append(float(v.std() / v.mean()))
    for mode in rot_runs:
        cc, kk = evaluate(councils, mode); rot_runs[mode].append((cc, kk))
    r2 = np.random.default_rng(1000 + s); rc = [[MODELS[j] for j in r2.choice(7, 4, replace=False)] for _ in range(N)]
    cc, kk = evaluate(rc); rand_runs.append((cc, kk))
def summarize(runs, name):
    accs = [r[0].mean() for r in runs]
    gains = [mcnemar(single_correct[best], r[0]) for r in runs]
    configs[name] = {"acc": float(np.mean(accs)), "acc_sd": float(np.std(accs, ddof=1)), "acc_min": float(min(accs)), "acc_max": float(max(accs)),
        "seq_s": float(np.mean([r[1]["seq_s"] for r in runs])), "par_s": float(np.mean([r[1]["par_s"] for r in runs])),
        "tokens": float(np.mean([r[1]["tokens"] for r in runs])), "seeds": len(runs),
        "seeds_beating_best_single": int(sum(a > single_correct[best].mean() for a in accs)),
        "max_p_mcnemar": float(max(g[2] for g in gains)), "min_p_mcnemar": float(min(g[2] for g in gains)),
        "by_domain": {d: float(np.mean([r[0][DOM == d].mean() for r in runs])) for d in ["finance","law","technology"]}}
for mode, runs in rot_runs.items(): summarize(runs, f"rotational4_{mode}")
summarize(rand_runs, "random4_consensus")
out["rotation_selection_cv"] = {"mean": float(np.mean(cvs)), "max": float(max(cvs))}
# timeout / failure handling on the rotational consensus council (seed 1 councils)
rot = Rotation(1); councils = [rot.select() for _ in range(N)]
lat_all = np.array([[member(m, i)["latency_s"] for m in MODELS] for i in range(N)])
fail = {}
for pct in [50, 75, 90, 100]:
    D = float(np.percentile(lat_all, pct)) if pct < 100 else float("inf")
    surv = [[m for m in c if member(m, i)["latency_s"] <= D] for i, c in enumerate(councils)]
    pred = [aggregate(sv, i) if sv else None for i, sv in enumerate(surv)]
    corr = np.array([p == g for p, g in zip(pred, GOLD)])
    bound = [min(D, max(member(m, i)["latency_s"] for m in c)) for i, c in enumerate(councils)]
    fail[f"deadline_p{pct}"] = {"deadline_s": D, "acc": float(corr.mean()), "mean_members": float(np.mean([len(s) for s in surv])),
        "no_answer": int(sum(p is None for p in pred)), "par_bound_s": float(np.mean(bound)), "p95_par_bound_s": float(np.percentile(bound, 95))}
for pf in [0.25, 0.5]:
    accs = []
    for s in range(10):
        r3 = np.random.default_rng(500 + s)
        surv = [[m for m in c if r3.random() > pf] for c in councils]
        pred = [aggregate(sv, i) if sv else None for i, sv in enumerate(surv)]
        accs.append(np.mean([p == g for p, g in zip(pred, GOLD)]))
    fail[f"random_member_failure_{pf}"] = {"acc_mean": float(np.mean(accs)), "acc_sd": float(np.std(accs, ddof=1))}
out["failure"] = fail; out["configs"] = configs; out["mean_single_acc"] = mean_single
# oracle upper bound: any member correct
anyc = np.any(np.stack([single_correct[m] for m in MODELS]), 0); out["oracle_any_of_7"] = float(anyc.mean())
# pairwise error correlation
E = np.stack([~single_correct[m] for m in MODELS]).astype(float); out["mean_pairwise_error_corr"] = float(np.mean(np.corrcoef(E)[np.triu_indices(7, 1)]))
(ROOT/"results/analysis.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps({k: out[k] for k in ["best_single","mean_single_acc","oracle_any_of_7","mean_pairwise_error_corr"]}, indent=1))
for n, v in configs.items(): print(f"{n:32s} acc={v['acc']:.3f} seq={v['seq_s']:.2f}s par={v['par_s']:.2f}s tok={v['tokens']:.0f}")
