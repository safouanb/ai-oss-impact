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

Phase 1 constructs the labelled contribution dataset used in the rest of the thesis. The unit of identification is the pull request, because this is the level at which AIDev records agent involvement and where review dynamics are most directly observable. Commit-level labels are then propagated only where a pull request-to-commit linkage can be established from repository history.

The primary detection source is the AIDev dataset, which provides externally curated pull requests attributed to major coding agents. For selected repositories that appear in AIDev, those pull requests are treated as high-confidence AI-positive observations rather than rediscovered from scratch. This reduces dependence on brittle keyword-only detection and gives the study a stronger starting point than a purely local heuristic approach.

Because AIDev does not capture all forms of AI assistance, the dataset is extended using a supplementary marker-based pass over repository metadata. This pass records explicit branch-name conventions such as `codex/`, `copilot/`, and `cursor/`; bot-authored activity where the bot identity is project-visible; and explicit co-author or commit-message signatures that directly indicate AI involvement. Marker-based rules are intentionally conservative. The study prioritizes precision over recall in the high-confidence bucket, because downstream RQ2 and RQ3 analyses are more vulnerable to false positives than to undercounting hidden AI use.

The resulting labels are assigned in confidence tiers rather than as a naive binary. Contributions are classified as `high-confidence AI`, `medium-confidence AI`, or `unresolved`. High-confidence AI labels are reserved for AIDev-linked pull requests and explicit repository-visible markers. Medium-confidence AI labels are assigned when multiple weaker indicators point in the same direction but no single indicator is definitive. Unresolved cases remain unlabelled for the main confirmatory analyses and can later be used in sensitivity checks if needed.

To reduce measurement error, Phase 1 includes a manual validation sample. A stratified subset of pull requests from each case repository is reviewed against raw metadata, patch context, and review history. The goal of this validation is not to perfectly detect all AI assistance, which is not possible with public metadata alone, but to estimate the precision of the high-confidence and medium-confidence tiers and to document the residual uncertainty in the label construction process.

The output of Phase 1 is a repository-specific labelled dataset containing pull request identifiers, linked commits where available, detection source, confidence tier, and timestamp. This dataset serves two roles in the study. First, it answers RQ1 by describing the detectable volume and temporal evolution of AI-related contributions. Second, it provides the treatment-like grouping required for the Phase 2 comparisons of technical debt indicators, review dynamics, and security traceability.

## Phase 2: quantitative code and security analysis (RQ2, RQ3)

### Code quality and technical debt metrics

### CVE commit tracing

## Phase 3: qualitative evidence (RQ4)

### Public discourse mining

### Developer interviews

## Validity and limitations
