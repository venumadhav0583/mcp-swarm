"""Camera-ready addition: council size k = 1..7 over every fixed council of that size (exhaustive, no sampling),
using the same logged outputs, aggregation rule (Eq. 2) and cost model as analyze.py."""
import json, itertools, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze as A  # re-runs analyze.py and reuses its loaded data and functions

out = {"note": "every fixed council of size k; Eq. (2) consensus; parallel latency = slowest member", "sizes": {}}
for k in range(1, 8):
    rows = []
    for cb in itertools.combinations(A.MODELS, k):
        c, cost = A.evaluate([list(cb)] * A.N)
        rows.append({"members": list(cb), "acc": float(c.mean()), **cost})
    accs = np.array([r["acc"] for r in rows])
    best = max(rows, key=lambda r: r["acc"])
    out["sizes"][k] = {
        "n_councils": len(rows), "acc_mean": float(accs.mean()), "acc_min": float(accs.min()),
        "acc_median": float(np.median(accs)), "acc_max": float(accs.max()), "best_members": best["members"],
        "share_beating_best_single": float(np.mean(accs > A.single_correct[A.best].mean())),
        "tokens": float(np.mean([r["tokens"] for r in rows])), "seq_s": float(np.mean([r["seq_s"] for r in rows])),
        "par_s": float(np.mean([r["par_s"] for r in rows])),
        "cpu_s_per_correct": float(np.mean([r["seq_s"] / r["acc"] for r in rows])),
    }
# strong-member council: the three models clearly above chance (Table I), chosen from accuracy, not post hoc on councils
strong = ["qwen2.5-1.5b", "gemma3-1b", "falcon3-1b"]
c, cost = A.evaluate([strong] * A.N)
a, lo, hi = A.ci(c); g, l, p = A.mcnemar(A.single_correct[A.best], c)
out["strong3"] = {"members": strong, "acc": a, "ci": [lo, hi], **cost, "gains": g, "losses": l, "p_mcnemar": p,
                  "note": "members chosen by single-model accuracy on the same 300 questions; optimistic"}
c, cost = A.evaluate([strong] * A.N, "confidence_only")
out["strong3_confidence_only"] = {"acc": float(c.mean())}
b = A.out["configs"]["single_best"]
out["best_single_cpu_s_per_correct"] = b["seq_s"] / b["acc"]
(A.ROOT / "results/analysis_scaling.json").write_text(json.dumps(out, indent=1))
for k, v in out["sizes"].items():
    print(f"k={k} n={v['n_councils']:2d} acc mean={v['acc_mean']:.3f} med={v['acc_median']:.3f} max={v['acc_max']:.3f} "
          f"beat={v['share_beating_best_single']:.2f} tok={v['tokens']:.0f} seq={v['seq_s']:.2f} par={v['par_s']:.2f} cpu/correct={v['cpu_s_per_correct']:.2f}")
print("strong3", json.dumps(out["strong3"]), out["strong3_confidence_only"], "best cpu/correct", out["best_single_cpu_s_per_correct"])
