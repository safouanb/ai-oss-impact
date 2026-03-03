# AI OSS Impact

[![Research](https://img.shields.io/badge/Research-MSc%20Thesis-black)](./thesis_proposal.md)
[![Status](https://img.shields.io/badge/Status-Active%20Development-0a7d34)](#project-status)
[![Method](https://img.shields.io/badge/Method-Mixed%20Methods-1f6feb)](#study-design)
[![Reproducibility](https://img.shields.io/badge/Reproducibility-Protocol%20Driven-6f42c1)](./docs/case_selection_protocol.md)

> **When code gets cheaper, what gets more expensive?**  
> This project studies whether AI-assisted open-source contributions are linked to technical debt growth, review pressure, and security outcomes.

## About

This repository contains the full research workflow for an MSc thesis at the University of Amsterdam.

**Author:** Safouan Bolbaroud  
**Program:** MSc Business Information Technology Management  
**Supervisor:** Chintan Amrit

## Research Focus

| Dimension | Question |
|---|---|
| RQ1 Detection | How much AI-generated contribution can be detected, and how does it evolve over time? |
| RQ2 Technical debt | Do AI-flagged contributions show different debt/quality signatures than human-authored ones? |
| RQ3 Security | Can documented CVEs be traced to contribution/review pathways involving AI-flagged code? |
| RQ4 Developer perspective | How do maintainers describe AI impact on review burden, quality control, and security? |

## Why This Is Interesting

Most existing studies show velocity/quality trade-offs at scale.  
This study pushes deeper into **security traceability** and **maintainer discourse**, with a case-study design aimed at publishable empirical evidence.

## Study Design

Three connected phases:

1. **AI contribution detection**
   - [AIDev](https://huggingface.co/datasets/hao-li/AIDev)-aligned marker strategy + supplementary heuristics.
   - Confidence-tier labels + validation sample.
2. **Quantitative debt/security analysis**
   - Pre-AI vs post-AI trends.
   - AI-flagged vs human-authored comparisons.
   - CVE-to-commit/review tracing.
3. **Qualitative discourse mining**
   - PR, issue, and release-note evidence on review strain, governance, and risk handling.

Core external dataset and references:

1. [AIDev dataset](https://huggingface.co/datasets/hao-li/AIDev)
2. [AIDev paper](https://arxiv.org/abs/2507.15003)
3. [AIDev replication package](https://github.com/SAILResearch/AI_Teammates_in_SE3)

## Case Selection Integrity

Prescanning is used for **feasibility**, not result fishing.

1. Selection uses ex-ante criteria (detectability, security traceability, maturity, discourse volume).
2. Criteria are frozen before confirmatory analysis.
3. Rejected candidates and decisions are retained.

Full protocol: [docs/case_selection_protocol.md](./docs/case_selection_protocol.md)

## Project Status

| Workstream | Status |
|---|---|
| Literature base | In progress |
| Case selection protocol | Complete |
| Data pipeline scaffolding | In progress |
| Detection baseline scripts | Complete |
| Quant + CVE tracing scripts | In progress |
| Thesis chapter drafts | In progress |

## Repository Map

```text
.
├── data/
│   ├── raw/                 # Source data pulls
│   └── processed/           # Cleaned and labeled outputs
├── docs/
│   ├── 01_introduction.md
│   ├── 02_literature_review.md
│   ├── 03_methodology.md
│   ├── 04_findings.md
│   ├── 05_discussion.md
│   ├── 06_conclusion.md
│   └── case_selection_protocol.md
├── references/              # Extracted source papers/reports
├── results/
│   ├── figures/
│   └── tables/
└── scripts/
```

## Quick Start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Example data pull and baseline labeling:

```bash
python scripts/fetch_github_data.py --repo facebook/react --since 2018-01-01 --until 2026-03-01
python scripts/detect_ai_contributions.py --repo facebook/react
```

## Quality Bar

This repository is run as publication-oriented research:

1. Reproducible code paths for all tables/figures.
2. Explicit validity threats and robustness checks.
3. Clear exploratory (prescan) vs confirmatory (hypothesis test) separation.
4. Transparent protocol and decision trail.
