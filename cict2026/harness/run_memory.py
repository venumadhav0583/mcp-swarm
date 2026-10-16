"""Memory-activation experiment: none vs full history vs fixed top-5 RAG vs adaptive threshold (ChromaDB)."""
import json, time, subprocess, requests, sys
from pathlib import Path
import numpy as np, chromadb
from chromadb.utils import embedding_functions as ef
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/"harness"))
from run_models import SERVER, MODELS
T = json.loads((ROOT/"data/memory_task.json").read_text())
emb = ef.DefaultEmbeddingFunction()
client = chromadb.EphemeralClient()
col = client.create_collection("mem", embedding_function=emb, metadata={"hnsw:space": "cosine"})
col.add(ids=[m["id"] for m in T["memory"]], documents=[m["text"] for m in T["memory"]])
def retrieve(q, k=5):
    r = col.query(query_texts=[q], n_results=k)
    return list(zip(r["documents"][0], [1 - d for d in r["distances"][0]]))
# calibrate tau on calibration split only (retrieval statistics, no LLM calls)
cal = T["calibration"]
gen_max = max(retrieve(q["q"], 1)[0][1] for q in cal if q["type"] == "general")
mem_gold_sims = [dict(retrieve(q["q"], 5)).get(q["gold_text"], 0) for q in cal if q["type"] == "memory"]
TAU = round(gen_max + 0.05, 3)
calib_info = {"general_max_top1_similarity": gen_max, "memory_gold_similarities": mem_gold_sims, "tau": TAU,
              "rule": "tau = highest top-1 similarity of any general (memory-free) calibration query + 0.05"}
SYSTEM = "You are an enterprise assistant with access to remembered notes from earlier sessions. Answer briefly."
def build(q, cond):
    if cond == "none": mem = []
    elif cond == "full": mem = [m["text"] for m in T["memory"]]
    elif cond == "rag_top5": mem = [d for d, s in retrieve(q["q"], 5)]
    elif cond == "adaptive": mem = [d for d, s in retrieve(q["q"], 5) if s >= TAU]
    ctx = ("Remembered notes:\n" + "\n".join(f"- {m}" for m in mem) + "\n\n") if mem else ""
    return mem, ctx + f"Question: {q['q']}"
def start(port):
    p = subprocess.Popen([str(SERVER), "-m", str(ROOT/"models"/MODELS["qwen2.5-1.5b"]), "--port", str(port),
        "-c", "4096", "-t", "2", "--no-webui", "-np", "1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(240):
        try:
            if requests.get(f"http://127.0.0.1:{port}/health", timeout=2).status_code == 200: return p
        except Exception: pass
        time.sleep(1)
if __name__ == "__main__":
    out = ROOT/"results/memory_raw.jsonl"
    (ROOT/"results/memory_calibration.json").write_text(json.dumps(calib_info, indent=1))
    p = start(8092)
    try:
        with out.open("w") as f:
            for q in T["test"]:
                for cond in ["none", "full", "rag_top5", "adaptive"]:
                    mem, user = build(q, cond)
                    body = {"messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
                            "temperature": 0, "max_tokens": 24, "cache_prompt": False}
                    t0 = time.perf_counter()
                    r = requests.post("http://127.0.0.1:8092/v1/chat/completions", json=body, timeout=600).json()
                    lat = time.perf_counter() - t0
                    txt = r["choices"][0]["message"]["content"]
                    ok = q["a"].lower() in txt.lower().replace(",", "")
                    f.write(json.dumps({"id": q["id"], "type": q["type"], "cond": cond, "n_mem": len(mem),
                        "gold_in_context": (q["gold_text"] in mem) if q["gold_text"] else None,
                        "mem_chars": sum(len(m) for m in mem), "prompt_tokens": r["usage"]["prompt_tokens"],
                        "completion_tokens": r["usage"]["completion_tokens"], "latency_s": lat,
                        "correct": ok, "response": txt}) + "\n"); f.flush()
    finally:
        p.terminate()
    print("MEMDONE")
