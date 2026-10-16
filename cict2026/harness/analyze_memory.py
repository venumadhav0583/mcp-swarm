import json
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
recs = [json.loads(l) for l in (ROOT/"results/memory_raw.jsonl").read_text().splitlines()]
cal = json.loads((ROOT/"results/memory_calibration.json").read_text())
out = {"tau": cal["tau"], "conditions": {}}
rng = np.random.default_rng(7)
for c in ["none", "full", "rag_top5", "adaptive"]:
    R = [r for r in recs if r["cond"] == c]
    def acc(t): 
        x = np.array([r["correct"] for r in R if r["type"] == t], float)
        b = x[rng.integers(0, len(x), (5000, len(x)))].mean(1)
        return [float(x.mean()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5)), len(x)]
    mem = [r for r in R if r["type"] == "memory"]; gen = [r for r in R if r["type"] == "general"]
    red = [1 - (1 / r["n_mem"]) if r["gold_in_context"] else 1.0 for r in mem if r["n_mem"] > 0]
    out["conditions"][c] = {"acc_memory": acc("memory"), "acc_general": acc("general"),
        "prompt_tokens_mean": float(np.mean([r["prompt_tokens"] for r in R])),
        "prompt_tokens_memory_q": float(np.mean([r["prompt_tokens"] for r in mem])),
        "prompt_tokens_general_q": float(np.mean([r["prompt_tokens"] for r in gen])),
        "latency_mean_s": float(np.mean([r["latency_s"] for r in R])),
        "latency_p95_s": float(np.percentile([r["latency_s"] for r in R], 95)),
        "gold_in_context": float(np.mean([bool(r["gold_in_context"]) for r in mem])),
        "general_with_memory": float(np.mean([r["n_mem"] > 0 for r in gen])),
        "mean_entries": float(np.mean([r["n_mem"] for r in R])),
        "redundant_entry_share": float(np.mean(red)) if red else 0.0}
# tau sensitivity (retrieval only)
import sys; sys.path.insert(0, str(ROOT/"harness")); __file__x = None
import chromadb
from chromadb.utils import embedding_functions as ef
T = json.loads((ROOT/"data/memory_task.json").read_text())
col = chromadb.EphemeralClient().create_collection("memsweep", embedding_function=ef.DefaultEmbeddingFunction(), metadata={"hnsw:space": "cosine"})
col.add(ids=[m["id"] for m in T["memory"]], documents=[m["text"] for m in T["memory"]])
ret = {}
for q in T["test"]:
    r = col.query(query_texts=[q["q"]], n_results=5); ret[q["id"]] = list(zip(r["documents"][0], [1 - d for d in r["distances"][0]]))
sweep = []
for tau in [0.1, 0.15, 0.22, 0.3, 0.4, 0.5, 0.6, 0.7]:
    mem = [q for q in T["test"] if q["type"] == "memory"]; gen = [q for q in T["test"] if q["type"] == "general"]
    sweep.append({"tau": tau, "gold_recall": float(np.mean([any(d == q["gold_text"] and s >= tau for d, s in ret[q["id"]]) for q in mem])),
        "entries_memory_q": float(np.mean([sum(s >= tau for _, s in ret[q["id"]]) for q in mem])),
        "general_activation": float(np.mean([any(s >= tau for _, s in ret[q["id"]]) for q in gen]))})
out["tau_sweep"] = sweep
(ROOT/"results/memory_analysis.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
