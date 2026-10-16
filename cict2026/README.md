# CICT 2026 Paper 348 - reproducibility package

Runtime: llama.cpp b11671 (CPU), 7 open-weight GGUF models (Q4_K_M), 2 CPU cores, 7 GB RAM.
Models: Qwen2.5-1.5B-Instruct, Llama-3.2-1B-Instruct, Gemma-3-1B-it, SmolLM2-1.7B-Instruct,
Granite-3.1-1B-A400M-Instruct, Falcon3-1B-Instruct, OLMo-2-0425-1B-Instruct (not included; download from Hugging Face).

1. `python3 harness/build_dataset.py`  -> data/eval300.jsonl (MMLU test split, seed 20261015, sha256 f65916c4...)
2. `python3 harness/run_models.py`     -> results/raw/<model>.jsonl (temperature 0, 1 token, top-20 logprobs)
3. `python3 harness/analyze.py`        -> results/analysis.json (Tables I-II, deadlines, failures)
4. `python3 harness/analyze_weighted.py` -> results/analysis_weighted.json (exploratory quality-weighted rotation)
5. `python3 harness/build_memory_task.py` -> data/memory_task.json (synthetic, fictional entities)
6. `python3 harness/run_memory.py`     -> results/memory_raw.jsonl, memory_calibration.json
7. `python3 harness/analyze_memory.py` -> results/memory_analysis.json (Table III, tau sweep)

Latency values depend on hardware; accuracy values are deterministic given the same model files and runtime.
Security results in Sec. IV-E come from an earlier workstation run (MCP Python SDK + Ollama) and are not re-run here.
