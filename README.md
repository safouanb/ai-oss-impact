# When Code Becomes Cheap

## Is AI Disrupting Open Source Through Technical Debt and Security Risk?

A mixed-methods MSc thesis project on AI-generated code, software quality, and vulnerability outcomes in mature open-source ecosystems.

**Author:** Safouan Bolbaroud
**Program:** MSc Business Information Technology Management, University of Amsterdam  
**Supervisor:** Chintan Amrit

## Thesis At A Glance

| Item | Value |
|---|---|
| Core question | Does growth in AI-assisted OSS contribution volume relate to measurable debt and security outcomes? |
| Study design | Two-case mixed-methods study (quantitative + qualitative) |
| Time window | 2018-2026 (pre-AI vs post-AI comparison) |
| Quantitative focus | AI-detection prevalence, debt/quality metrics, CVE commit tracing |
| Qualitative focus | PR/issue/release discourse on review burden, quality, and security |

## Why This Matters

Recent empirical work shows a repeating pattern: AI coding tools can increase short-term throughput, while complexity and warning burden can persist.  
This project tests whether that pattern translates into security-relevant outcomes in real, high-impact repositories.

## Research Questions

1. **RQ1 (Detection)**: To what extent are AI-generated contributions identifiable in selected projects, and what is their prevalence over time?
2. **RQ2 (Technical Debt)**: How do technical debt and code quality indicators evolve after widespread AI tool adoption, and how do AI-flagged contributions compare with human-authored ones?
3. **RQ3 (Security)**: Is there a traceable relationship between AI-flagged contributions and documented vulnerabilities (CVEs)?
4. **RQ4 (Developer Perspective)**: How do maintainers and contributors describe AI-related effects on quality, review load, and security?

## Method Overview

### Phase 1: AI contribution detection
- Use AIDev-aligned markers and supplementary heuristics.
- Build commit/PR labels with confidence tiers and validation samples.

### Phase 2: Quantitative debt and Security analysis
- Compare pre-AI and post-AI metric trends.
- Compare AI-flagged vs human-authored changes.
- Trace CVE timelines to commits and review trails.

### Phase 3: Qualitative evidence
- Mine project discourse from PRs/issues/release notes.
- Identify themes around review strain, governance, and security practice.

## Case selection policy

Prescanning is used only for **feasibility** and **inclusion criteria**, not for fishing desirable results.  

- Full protocol: [`docs/case_selection_protocol.md`](docs/case_selection_protocol.md)
- Guardrails:
  - No outcome-based cherry-picking.
  - Criteria are frozen before main hypothesis testing.
  - Full scan logs and rejected candidates are retained.

## Repository structure

```text
.
├── data/
│   ├── raw/
│   └── processed/
├── docs/
│   ├── 01_introduction.md
│   ├── 02_literature_review.md
│   ├── 03_methodology.md
│   ├── 04_findings.md
│   ├── 05_discussion.md
│   ├── 06_conclusion.md
│   └── case_selection_protocol.md
├── references/
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

Optional first run:

```bash
python scripts/fetch_github_data.py --repo facebook/react --since 2018-01-01 --until 2026-03-01
python scripts/detect_ai_contributions.py --repo facebook/react
```

## Quality bar

This project is built with publication readiness in mind:

1. Reproducible scripts for all tables/figures.
2. Explicit validity threats and robustness checks.
3. Clear separation between exploratory prescan and confirmatory analysis.
4. Open methodological traceability for case selection and labeling decisions.
