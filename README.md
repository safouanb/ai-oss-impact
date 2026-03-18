# When Code Gets Cheap, Who Pays the Debt?
*From Prompt to Patch to Breach in Open Source Security*

[![Research](https://img.shields.io/badge/Research-MSc%20Thesis-black)](./thesis_proposal.md)
[![Status](https://img.shields.io/badge/Status-Active%20Development-0a7d34)](#project-status)
[![Method](https://img.shields.io/badge/Method-Mixed%20Methods-1f6feb)](#study-design)
[![Reproducibility](https://img.shields.io/badge/Reproducibility-Protocol%20Driven-6f42c1)](./docs/case_selection_protocol.md)

> This project studies whether AI-assisted open-source contributions are linked to technical debt growth, review burden, and security outcomes.

## About

This repository contains the full research workflow for an MSc thesis at the University of Amsterdam.

**Author:** Safouan Bolbaroud  
**Program:** MSc Business Information Technology Management  
**Supervisor:** Chintan Amrit

## Research focus

| Dimension | Question |
|---|---|
| RQ1 Detection | How much AI-generated contribution can be detected, and how does it evolve over time? |
| RQ2 Technical Debt | Do AI-flagged contributions show different debt/quality signatures than human-authored ones? |
| RQ3 Security | Can documented CVEs be traced to contribution/review pathways involving AI-flagged code? |
| RQ4 Developer Perspective | How do maintainers describe AI impact on review burden, quality control, and security? |

## Why this is interesting

Most existing studies show velocity/quality trade-offs at scale.  
This study pushes deeper into **security traceability** and **maintainer discourse**, with a case-study design aimed at publishable empirical evidence.

## Study design

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

## Case selection integrity

Prescanning is used for **feasibility**, not result fishing.

1. Selection uses ex-ante criteria (detectability, security traceability, maturity, discourse volume).
2. Criteria are frozen before confirmatory analysis.
3. Rejected candidates and decisions are retained.

Full protocol: [docs/case_selection_protocol.md](./docs/case_selection_protocol.md)

Prescan workflow: [docs/prescan_pipeline.md](./docs/prescan_pipeline.md)

## Project status

| Workstream | Status |
|---|---|
| Literature base | In progress |
| Case selection protocol | Complete |
| Data pipeline scaffolding | In progress |
| Detection baseline scripts | Complete |
| Quant + CVE tracing scripts | In progress |
| Thesis chapter drafts | In progress |

## Repository map

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

## Quick start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the repository prescan:

```bash
export GITHUB_TOKEN=your_token_here
python scripts/prescan_cases.py \
  --repos docs/prescan_candidates.txt \
  --out-csv results/tables/case_prescan.csv \
  --out-md results/tables/case_prescan.md \
  --out-fig results/figures/case_prescan_scores.png
```

Example data pull and baseline labeling:

```bash
python scripts/fetch_github_data.py --repo facebook/react --since 2018-01-01 --until 2026-03-01
python scripts/detect_ai_contributions.py --repo facebook/react
```

## Quality bar

This repository is run as publication-oriented research:

1. Reproducible code paths for all tables/figures.
2. Explicit validity threats and robustness checks.
3. Clear exploratory (prescan) vs confirmatory (hypothesis test) separation.
4. Transparent protocol and decision trail.

## GitHub sidebar setup

Set this manually in the repository "About" panel:

- **Description:** `Mixed-methods research on AI-assisted OSS contributions, technical debt, and CVE-linked security traceability.`
- **Website:** use your thesis/project link when available.
- **Topics:** `software-engineering`, `open-source`, `ai-code`, `technical-debt`, `software-security`, `cve`, `empirical-research`, `mining-software-repositories`
