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

Phase 2 computes a set of per-pull-request proxy metrics and then compares them across the AI-labeled and human-labeled groups established in Phase 1. The unit of observation remains the pull request. Metrics are derived from the raw data already collected by `fetch_github_data.py` — specifically the PR detail, files patch, review objects, review comments, issue comments, and commit list stored per PR in the JSONL bundles.

The following metrics are computed for each pull request by `compute_pr_metrics.py`:

- **added_lines** and **deleted_lines**: net line counts from the files endpoint, used as a basic size control.
- **changed_files**: number of distinct files modified in the PR.
- **commit_count**: number of commits in the PR, capturing granularity of the development process.
- **todo_fixme_count**: count of `TODO`, `FIXME`, `HACK`, `XXX`, `TEMP`, and `NOSONAR` annotations in added lines only (lines starting with `+` in the patch, excluding `+++` headers). To avoid artefacts from vendored bundles and dependency metadata, the patch-text debt proxies exclude lockfiles, compiled/generated paths, and extremely long minified lines. These are established deferred-debt markers in technical debt research (Bavota and Russo 2016; Guo et al. 2019). Counting only added lines avoids penalizing PRs that resolve pre-existing debt.
- **complexity_proxy**: decision-point keyword frequency per 100 analyzable added lines. Counted keywords are `if`, `else if`, `elif`, `for`, `while`, `case`, `catch`, `except`, `&&`, `||`, and a ternary operator pattern. The proxy is computed only on analyzable patch text rather than on vendored/compiled artifacts, because generated one-line bundles can massively inflate decision counts without reflecting contributor-authored source complexity. This is a lightweight cyclomatic complexity estimate that can be extracted from patch text without running a static analysis tool on the full codebase. It is explicitly a proxy; per-patch decision counts correlate moderately with McCabe complexity but do not substitute for it.
- **security_kw_in_review**: count of security-relevant terms in all review bodies and comments combined. The term list covers `vulnerability`, `CVE`, `injection`, `XSS`, `CSRF`, `SQLi`, `RCE`, `auth`, `sanitiz`, `escap`, `exploit`, `bypass`, `overflow`, `traversal`, `deseri`, `privilege`, and `malici`. This indicator is used as a review-thoroughness proxy rather than as a vulnerability detector — it captures whether reviewers raised security concerns, not whether the PR contains a vulnerability.
- **review_duration_hours**: elapsed hours from `created_at` to `merged_at` (or `updated_at` if unmerged). Review latency is used in code review research as a proxy for review investment; very short durations on large PRs are associated with rubber-stamping (Rigby and Bird 2013).
- **reviewer_count**: distinct human logins who submitted a review, excluding the PR author and accounts matching bot-name patterns (`[bot]`, `-bot`, `copilot`, `dependabot`).

For the pre/post-AI trend analysis required by the proposal (§4.4), the same metrics are computed over the pre-AI baseline sample (2018–2022) collected by `fetch_pre2022_data.py`. Each row carries a `period` column (`pre2022` or `post2022`) to allow project-level comparisons. The trend comparison does not require individual-level AI labels in the pre-2022 sample; the comparison is at the group level between the two time periods.

Statistical testing follows the non-parametric convention appropriate for PR metric distributions (typically right-skewed, non-normal). Mann–Whitney U tests are used for group comparisons with effect sizes reported as rank-biserial correlation. Bonferroni correction is applied over the set of primary metric comparisons to control family-wise error rate. All tests treat the sample of 250 post-2022 PRs per case as the analytical population rather than drawing inferences to a broader super-population; effect-size language is used in preference to significance language in the write-up.

### CVE commit tracing

Phase 2 also traces published security advisories to specific pull requests in order to ask whether the fix-implementing PRs bear AI or human labels and what their review characteristics look like (RQ3).

The tracing pipeline implemented in `trace_cve_commits.py` proceeds in three steps. First, the GitHub Security Advisory API response for each case repository is parsed to extract CVE IDs, CVSS scores, advisory descriptions, and the patched version string (for example `1.109.1` for VS Code). Second, patched version strings are resolved to Git release tags using the GitHub Releases API, and the commit SHAs associated with those tags are retrieved. Third, each identified fix commit SHA is looked up in the labelled PR dataset to determine whether the commit was part of an AI-labeled or human-labeled pull request; if a match is found the PR's full metadata and review record are retrieved.

For the thesis, the CVE set is anchored on four pre-resolved fix commits that were identified using GitHub MCP tooling during the research setup phase:

- VS Code CVE-2026-21523 → commit `6534f6ba`
- VS Code CVE-2026-21518 → commit `cd11faec` (commit message explicitly references Opus and Sonnet 4.5, making this a methodologically significant case)
- Next.js CVE-2025-55182 (CVSS 10.0, critical) → commit `7492122a`
- Next.js CVE-2025-29927 (critical, widely exploited middleware bypass) → commit `535e26d3`

For each traced CVE, the output records the CVE identifier, CVSS score, advisory summary, fix commit SHA, PR number, AI label and confidence tier, reviewer count, review duration, and presence of security keywords in the review text. The trace results are written to `results/tables/cve_trace.csv` and `results/tables/cve_trace.md` for direct inclusion in the thesis.

The CVE tracing analysis is explicitly bounded by what is publicly recoverable from commit and PR metadata. It does not claim to determine whether AI involvement caused a vulnerability; it documents whether fix-implementing contributions carry AI markers and what the observable review characteristics were at the time the fix was merged. Interpretive claims about causal pathways are deferred to Chapter 5.

## Phase 3: qualitative evidence (RQ4)

### Public discourse mining

Phase 3 collects and analyses publicly available discourse about AI contributions, review quality, and security governance in the two case repositories. The primary source is GitHub Issues and Pull Request comment threads — specifically threads that reference AI tooling, code review practices, or security policy. Secondary sources include repository wikis, contributing guidelines, and governance documents such as `SECURITY.md` files.

Discourse collection is restricted to public data accessible through the GitHub Issues and Search APIs. No private communications, direct messages, or non-public materials are included. Collection targets threads that meet at least one of the following relevance criteria: the thread title or body mentions an AI coding agent by name; the thread discusses contribution guidelines or review requirements in the context of automated code generation; or the thread is linked to a security advisory or vulnerability report in the repository's advisory database.

Collected threads are analysed using thematic analysis (Braun and Clarke 2006). An initial codebook is developed deductively from the theoretical framework — specifically from the axes of review burden, governance response, and security concern articulation — and refined inductively from a first-pass reading of the collected threads. Codes are applied at the paragraph or comment level. Themes are synthesised across cases to identify patterns that are common to both repositories, patterns that diverge, and cases that challenge the quantitative findings from Phase 2.

The discourse analysis serves two functions. It provides the mechanism-level explanation that statistical comparisons alone cannot supply: why review durations are shorter or longer, why certain AI-labeled PRs passed without security scrutiny, and what maintainer rationales are offered for governance decisions. It also provides an important triangulation check — if the qualitative evidence contradicts the quantitative patterns from Phase 2, that tension is reported and investigated rather than resolved in favor of either data source.

### Developer interviews

To supplement the public discourse evidence, a small number of semi-structured interviews are conducted with maintainers or active contributors from the case repositories. Interviews target individuals who (a) have made or reviewed AI-assisted contributions, or (b) have been involved in security policy discussions in the repository. Recruitment proceeds through public GitHub profiles and repository contributor data; no private contact information is used.

The interview protocol covers three topic areas: the contributor's direct experience with AI coding tools in the context of the repository; their perceptions of review quality and governance burden under increased AI contribution volume; and their views on the relationship between AI-assisted code and security risk. Interviews are conducted remotely, recorded with consent, and transcribed. Transcripts are coded using the same codebook developed for the discourse analysis, with memos documenting new codes that emerge from the interview data.

Given the size of the study (two cases, limited interview access), interview findings are treated as illustrative and contextualising rather than as statistically representative. They are used to test whether the mechanisms inferred from public discourse and quantitative patterns are recognised and confirmed by practitioners, and to surface perspectives that are not visible in commit and PR metadata alone.

## Validity and limitations
