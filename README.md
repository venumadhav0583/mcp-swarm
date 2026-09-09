# Venu Kalluru — Research Papers Repository

**Author:** Venumadhav Venkata Kalluru  
**Email:** greenkal2026@gmail.com  
**ORCID:** 0009-0006-8250-9899  
**Location:** Orlando, Florida, USA  
**Last updated:** July 2026

---

## Papers

| # | Folder | Paper Title | Best Venue Status |
|---|--------|-------------|-------------------|
| 1 | `01_CloudFuzz/` | Adaptive Fuzzing for Enhanced Cloud-Native Application Security | ITEICS 2026 — Planned |
| 2 | `02_Declarative_IaC_DevOps/` | Continuum-Aware Declarative DevOps (CA-IaC) | Cloud2Things submitted; ITEICS planned |
| 3 | `03_IDP_Microservice_Delivery/` | A Reference Architecture for Enterprise IDPs | **IEEE BigDataSecurity 2026 — Accepted** |
| 4 | `04_Proactive_Mobile_AI/` | Proactive Conversational AI / AndroidInteraction Benchmark | ITEICS 2026 — Planned |
| 5 | `05_CSSA_Sovereign_SLM/` | Sovereign by Design — CSSA for Citizen Services | **ACM COMPASS 2026 — Accepted & Presented** · IEEE ISAIA 2026 under review |
| 6 | `06_Cloud2Things_Continuum/` | Cloud2Things Continuum Framework | SoCC 2026 submitted · SYSTOR 2026 poster |
| 8 | `08_AIOps_SLM_RAG_MCP/` | Building AIORA — Engineering & Operations Experience Report on a Sovereign Multi-Agent AIOps Platform (SLM+RAG+MCP, working prototype + measured results) | v1 IEEEtran draft complete · v2 JSS "In Practice" (elsarticle) draft + cover note complete |

---

## Folder Structure

```
papers_repo/
├── README.md                          ← this file
│
├── 01_CloudFuzz/
│   └── notes/PAPER_STATUS.md         ← tex missing — re-upload from local
│
├── 02_Declarative_IaC_DevOps/
│   ├── PAPER_STATUS.md
│   ├── v1_original_ieee/main.tex     ← original IEEE Declarative DevOps
│   ├── v2_cloud2things_acm/          ← CA-IaC / Cloud2Things ACM sigconf
│   └── figures_original/             ← 7 figures (1.png–7.png)
│
├── 03_IDP_Microservice_Delivery/
│   ├── PAPER_STATUS.md
│   ├── v1_original_lncs/             ← LNCS reference architecture (main.tex + bib.bib)
│   ├── v2_accelerating_ms/           ← Accelerating Microservice Delivery variant
│   └── figures/
│
├── 04_Proactive_Mobile_AI/
│   ├── PAPER_STATUS.md
│   ├── v1_acm_tiis_journal/          ← ACM TiiS 28-page journal main.tex + PDF
│   └── supplemental/                 ← infer scripts, evaluate.py
│
├── 05_CSSA_Sovereign_SLM/
│   ├── PAPER_STATUS.md
│   ├── compass26_poster/             ← ACM COMPASS 2026 accepted poster
│   │   ├── compass_poster_camera_ready.tex
│   │   ├── compass26-33-accepted.pdf
│   │   ├── taps_final/               ← TAPS submission source + PDF
│   │   └── versions/                 ← v1–v5 drafts
│   ├── ieee_isaia_2026/              ← IEEE ISAIA 2026 under review
│   │   ├── IEEE_ISAIA_2026_CSSA_revised.tex
│   │   ├── cssa_architecture.pdf
│   │   └── IEEE_ISAIA_2026_paper_145_original.pdf
│   └── presentation/                 ← PPTX slides + script/Q&A doc
│
├── 06_Cloud2Things_Continuum/
│   ├── PAPER_STATUS.md
│   ├── socc26_vision/                ← SoCC 2026 vision paper (submitted)
│   ├── systor26_poster/              ← SYSTOR 2026 poster + bib
│   └── cfp/                          ← call for papers reference
│
└── 08_AIOps_SLM_RAG_MCP/
    ├── PAPER_STATUS.md
    ├── v1_original_ieee/main.tex     ← AIORA experience report, IEEEtran (draft)
    ├── v2_jss_in_practice/            ← JSS "In Practice" version, elsarticle
    │   ├── main.tex                   ← restructured for Applied Research Report criteria
    │   └── cover_note.md              ← submission cover note for JSS editors
    ├── figures/                       ← architecture diagram (PDF embedded in v1 main.tex,
                                          PNG for quick viewing, regen script; v2 uses an
                                          inline TikZ figure, no external file)
    └── supplemental/                 ← working Python prototype (event bus, agents,
                                          MCP gateway, orchestrator, workload harness)
                                          + metrics.json from the 30-day validation run
                                          (shared by both v1 and v2)
```

---

## ITEICS 2026 Submission Plan

**Conference:** 3rd ICITEICS-2026 · Oct 9–10 · Vemana Institute of Technology, Bangalore  
**Format:** IEEEtran two-column · 6 pages max including references  
**Proceedings:** IEEE Xplore  
**Portal:** Check https://iteics.in/ — not yet live as of July 2026

| Paper | Track | Effort | Priority |
|-------|-------|--------|----------|
| CloudFuzz (01) | Cyber & Network Security | Low — abstract swap only | 1st |
| CA-IaC (02) | IoT & Computer Networks | Medium — ACM→IEEEtran | 2nd |
| AndroidInteraction (04) | Cognitive Computing & ML | High — 28-page journal → 6-page conf | 3rd |
| IDPRA (03) | IoT & Computer Networks | High — LNCS→IEEEtran + trim | 4th |

> **Concurrent submission check:** Confirm SoCC 2026 and ACM TiiS review status before submitting CA-IaC and AndroidInteraction to ITEICS.

---

## Format Quick Reference

| Template | Used in | Compile command |
|----------|---------|-----------------|
| `IEEEtran` conference | 01, 02 (v1), 03 (target), 04 (target), 05 ISAIA, 08 (v1) | `pdflatex main.tex` |
| `acmart sigconf` | 02 (v2), 05 COMPASS, 06 SoCC | `pdflatex → bibtex → pdflatex × 2` |
| `llncs` (Springer) | 03 (v1) | `pdflatex main.tex` |
| `acmart` journal | 04 (v1 TiiS) | `pdflatex → bibtex → pdflatex × 2` |
| `elsarticle` (Elsevier) | 08 (v2, JSS) | `pdflatex main.tex` (inline `thebibliography`, no bibtex needed) |
