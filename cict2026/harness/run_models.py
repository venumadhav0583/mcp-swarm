"""Query each local model once per question (temperature 0) via llama-server.
Records answer letter, letter-probability confidence, wall latency and token counts."""
import json, subprocess, time, sys, math, requests, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "llama/llama-b11671/llama-server"
MODELS = {
 "qwen2.5-1.5b": "Qwen2.5-1.5B-Instruct-Q4_K_M.gguf",
 "llama3.2-1b": "Llama-3.2-1B-Instruct-Q4_K_M.gguf",
 "gemma3-1b": "google_gemma-3-1b-it-Q4_K_M.gguf",
 "smollm2-1.7b": "SmolLM2-1.7B-Instruct-Q4_K_M.gguf",
 "granite3.1-1b": "granite-3.1-1b-a400m-instruct-Q4_K_M.gguf",
 "falcon3-1b": "Falcon3-1B-Instruct-Q4_K_M.gguf",
 "olmo2-1b": "OLMo-2-0425-1B-Instruct-Q4_K_M.gguf",
}
SYSTEM = "You are an enterprise knowledge assistant. Answer multiple-choice questions with a single letter."
def prompt(q):
    opts = "\n".join(f"{l}. {c}" for l, c in zip("ABCD", q["choices"]))
    return f"Question: {q['question']}\n{opts}\nRespond with only the letter (A, B, C, or D) of the correct answer."
def start(model_file, port):
    p = subprocess.Popen([str(SERVER), "-m", str(ROOT/"models"/model_file), "--port", str(port),
        "-c", "2048", "-t", "2", "--no-webui", "-np", "1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(240):
        try:
            if requests.get(f"http://127.0.0.1:{port}/health", timeout=2).status_code == 200: return p
        except Exception: pass
        time.sleep(1)
    p.kill(); raise RuntimeError("server did not start")
def ask(port, q):
    body = {"messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt(q)}],
            "temperature": 0, "max_tokens": 1, "logprobs": True, "top_logprobs": 20, "cache_prompt": False}
    t0 = time.perf_counter()
    r = requests.post(f"http://127.0.0.1:{port}/v1/chat/completions", json=body, timeout=300).json()
    lat = time.perf_counter() - t0
    tops = r["choices"][0]["logprobs"]["content"][0]["top_logprobs"]
    probs = {}
    for t in tops:
        k = t["token"].strip().upper().rstrip(".)")
        if k in ("A", "B", "C", "D"): probs[k] = probs.get(k, 0) + math.exp(t["logprob"])
    text = r["choices"][0]["message"]["content"]
    if probs:
        z = sum(probs.values()); probs = {k: v / z for k, v in probs.items()}
        ans = max(probs, key=probs.get); conf = probs[ans]
    else:
        ans, conf = None, 0.0
    u = r["usage"]
    return {"answer": ans, "confidence": conf, "letter_probs": probs, "raw": text, "latency_s": lat,
            "prompt_tokens": u["prompt_tokens"], "completion_tokens": u["completion_tokens"]}
if __name__ == "__main__":
    names = sys.argv[1:] or list(MODELS)
    qs = [json.loads(l) for l in (ROOT/"data/eval300.jsonl").read_text().splitlines()]
    outdir = ROOT / "results/raw"; outdir.mkdir(parents=True, exist_ok=True)
    for name in names:
        out = outdir / f"{name}.jsonl"
        done = {json.loads(l)["qid"] for l in out.read_text().splitlines()} if out.exists() else set()
        if len(done) == len(qs): continue
        p = start(MODELS[name], 8090)
        try:
            with out.open("a") as f:
                for q in qs:
                    if q["qid"] in done: continue
                    for attempt in range(3):
                        try:
                            res = ask(8090, q); break
                        except Exception as e:
                            print("retry", name, q["qid"], repr(e)[:120], flush=True)
                            p.terminate(); p.wait(); time.sleep(3); p = start(MODELS[name], 8090)
                    else:
                        raise RuntimeError("repeated failure")
                    rec = {"model": name, "qid": q["qid"], "domain": q["domain"], "gold": q["answer"], **res, "attempts": attempt + 1}
                    f.write(json.dumps(rec) + "\n"); f.flush()
        finally:
            p.terminate(); p.wait()
        print("finished", name, flush=True)
