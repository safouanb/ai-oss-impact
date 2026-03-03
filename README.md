# When Code Becomes Cheap: Is AI Disrupting Open Source?

A mixed-methods case study on AI-generated code, technical debt, and security in open-source software.

**Safouan** — MSc Business Information Technology Management, University of Amsterdam. Supervised by Chintan Amrit.

## What this is about

Something changed in open-source software development around late 2022. AI coding tools made it possible for anyone to produce code faster and in larger quantities than before. Recent work out of CMU (He et al., 2025; Agarwal et al., 2026) has shown that this comes with a trade-off: velocity goes up, but so does complexity and static analysis warnings — and that quality degradation persists even after the initial speed boost fades.

This thesis goes where those papers stopped. Rather than running another broad survey across thousands of repos, the goal here is a deep case study of one or two mature open-source projects with recent, critical security incidents. The question is not just whether AI-generated code is present, but whether it matters — for technical debt, for review quality, and ultimately for security.

## Research questions

1. **RQ1 (Detection):** To what extent are AI-generated contributions identifiable in the selected projects, and what is their prevalence over time?
2. **RQ2 (Technical Debt):** How have technical debt indicators changed since the widespread availability of AI coding tools, and do AI-flagged contributions show different debt profiles than human-authored code?
3. **RQ3 (Security):** Is there a traceable link between AI-generated contributions and documented security vulnerabilities (CVEs)?
4. **RQ4 (Developer perspective):** How do project maintainers perceive the impact of AI-assisted contributions on code quality, review burden, and security?

## Methodology

Three phases, each building on the previous:

- **Phase 1** — Detect and label AI-generated contributions using the AIDev dataset (Li et al., 2025) and supplementary heuristics
- **Phase 2** — Quantitative analysis of code quality metrics (pre-AI vs post-AI period) and CVE commit tracing
- **Phase 3** — Qualitative evidence from public project discourse and, where feasible, developer interviews

## Timeline

| Period | What happens |
|---|---|
| Feb 2026 | Literature deep-dive, AIDev dataset exploration, case selection |
| Mar–Apr 2026 | Phase 1: AI detection, labelled contribution dataset |
| Apr–May 2026 | Phase 2: quantitative analysis, CVE tracing |
| May–Jun 2026 | Phase 3: discourse mining, qualitative analysis |
| Jun–Jul 2026 | Synthesis and writing |

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
