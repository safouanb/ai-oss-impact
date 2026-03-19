# Research methodology

## Research design

This thesis uses a mixed-methods multiple-case design. The quantitative component examines AI-signaled contributions, code-quality proxies, review activity, and security-advisory traceability across selected repositories. The qualitative component analyzes public discourse around those same repositories to understand how maintainers and contributors describe review burden, governance pressure, and security concerns.

The design is sequential and connected. Phase 1 establishes AI-related contribution signals. Phase 2 tests whether those signals align with measurable technical debt and security-relevant patterns. Phase 3 uses discourse evidence to interpret the mechanisms behind the quantitative patterns rather than treating the statistical outputs as self-explanatory.

## Case selection

Case selection follows a predefined feasibility protocol rather than an outcome-driven search for large effects. On 19 March 2026, a scripted prescan was run over 16 mature open-source repositories using [scripts/prescan_cases.py](../scripts/prescan_cases.py) and the candidate list in [docs/prescan_candidates.txt](./prescan_candidates.txt). The prescan evaluated only ex-ante feasibility variables: explicit AI-signal detectability, GitHub security-advisory traceability, repository maturity, and public discussion volume. It did not use technical debt estimates, vulnerability effect sizes, or any confirmatory model outputs.

Eligibility thresholds were fixed before interpretation. A repository had to meet four conditions: at least 10,000 stars, at least one explicit AI marker, at least one published GitHub security advisory, and at least 1,000 combined pull requests and issues. These thresholds were intentionally conservative. The aim was not to identify the most dramatic cases, but to rule out repositories that would be analytically thin for one or more research questions.

The prescan produced 10 eligible repositories out of 16 screened candidates. The strongest candidates were `microsoft/vscode` (prescan score `0.874`), `vercel/next.js` (`0.584`), `pytorch/pytorch` (`0.575`), `n8n-io/n8n` (`0.556`), and `home-assistant/core` (`0.537`). At this stage, `microsoft/vscode` is the clearest primary case because it combines very strong explicit AI signal with substantial maturity, discourse volume, and a usable advisory history. `vercel/next.js` is currently the strongest secondary candidate because it offers a more balanced mix of AI detectability and security traceability than most other mature framework repositories. `pytorch/pytorch` and `n8n-io/n8n` are retained as backup secondary cases.

This prescan is treated as exploratory feasibility work, not as part of the confirmatory analysis. The full candidate list, exclusion reasons, scored outputs, and selection memo are retained in the research archive to reduce selection bias and to preserve an audit trail. The final case lock is recorded before confirmatory modeling begins.

## Phase 1: AI contribution detection (RQ1)

## Phase 2: quantitative code and security analysis (RQ2, RQ3)

### Code quality and technical debt metrics

### CVE commit tracing

## Phase 3: qualitative evidence (RQ4)

### Public discourse mining

### Developer interviews

## Validity and limitations
