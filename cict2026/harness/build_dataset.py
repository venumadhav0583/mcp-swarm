"""Build the fixed 300-question evaluation set from public MMLU (cais/mmlu, test split)."""
import pandas as pd, json, hashlib
from pathlib import Path
D = Path(__file__).resolve().parent.parent / "data"
PLAN = {"finance": ["professional_accounting", "high_school_macroeconomics"],
        "law": ["jurisprudence", "international_law"],
        "technology": ["computer_security", "college_computer_science"]}
SEED = 20261015
rows = []
for domain, subs in PLAN.items():
    for s in subs:
        d = pd.read_parquet(D / f"{s}.parquet").sample(n=50, random_state=SEED).reset_index()
        for _, r in d.iterrows():
            rows.append({"qid": f"{s}-{int(r['index'])}", "domain": domain, "subject": s,
                         "question": r["question"], "choices": list(r["choices"]),
                         "answer": "ABCD"[int(r["answer"])]})
out = D / "eval300.jsonl"
out.write_text("".join(json.dumps(r) + "\n" for r in rows))
print(len(rows), hashlib.sha256(out.read_bytes()).hexdigest())
