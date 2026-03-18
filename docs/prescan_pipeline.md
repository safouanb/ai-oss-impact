# Prescan pipeline

## What this is

This is the repository-level equivalent of study screening in a literature review.

In a systematic review, papers are not selected because they produce attractive results. They are screened on predefined inclusion criteria: relevance, data availability, methodological fit, and traceability.  
This prescan does the same for open-source repositories.

It asks a narrower question:

> Which repositories are actually analyzable for this thesis design?

That is different from:

> Which repositories produce the strongest debt or security findings?

The first is legitimate feasibility screening. The second would be cherry-picking.

## Why the pipeline exists

The thesis design requires all of the following before confirmatory analysis can even start:

1. Observable AI-related contribution signals.
2. Publicly documented security advisories suitable for traceability work.
3. Enough PR/issue discourse for qualitative mining.
4. Sufficient maturity and project scale to justify a case-study claim.

Without a prescan, case selection becomes arbitrary.

## Fixed feasibility criteria

The script uses only ex-ante feasibility variables:

1. **AI detectability**
   - Explicit PR markers aligned with AIDev-style signals:
   - `head:codex/`
   - `head:copilot/`
   - `head:cursor/`
   - `author:devin-ai-integration[bot]`
   - `"Co-Authored-By: Claude"`
2. **Security traceability**
   - GitHub security advisory availability.
   - High/critical advisory count.
   - Recent advisory presence.
3. **Discourse richness**
   - Public PR and issue volume.
4. **Maturity**
   - Stars and repository age.

It does **not** use:

1. Technical debt effect sizes.
2. CVE impact estimates derived from thesis models.
3. Any RQ2 or RQ3 hypothesis outcomes.

## How scoring works

The script computes normalized component scores for:

1. `ai_detectability_norm`
2. `security_traceability_norm`
3. `discourse_richness_norm`
4. `maturity_norm`

The fixed prescan score is:

```text
0.40 * AI detectability
+ 0.30 * security traceability
+ 0.20 * discourse richness
+ 0.10 * maturity
```

These weights are intentionally fixed before confirmatory analysis.

## Eligibility thresholds

The current fixed thresholds are:

1. Minimum stars: `10,000`
2. Minimum PR + issue volume: `1,000`
3. At least one explicit AI marker
4. At least one published GitHub security advisory

If a repository fails any of these, it is not eligible under the current protocol.

## Inputs

Primary input file:

- [`docs/prescan_candidates.txt`](/Users/safouan/Documents/DEV/thesis/docs/prescan_candidates.txt)

Each line contains one repository slug such as `microsoft/vscode`.

## Outputs

Running the script produces:

1. `results/tables/case_prescan.csv`
2. `results/tables/case_prescan.md`
3. `results/figures/case_prescan_scores.png`

These are intended to be retained as an audit trail.

## Run it

Set a GitHub token first. Without one, the Search API will be painfully slow.

```bash
export GITHUB_TOKEN=your_token_here
python scripts/prescan_cases.py --repos docs/prescan_candidates.txt
```

Optional:

```bash
python scripts/prescan_cases.py \
  --repos docs/prescan_candidates.txt \
  --out-csv results/tables/case_prescan.csv \
  --out-md results/tables/case_prescan.md \
  --out-fig results/figures/case_prescan_scores.png \
  --sleep-seconds 0.25
```

## How to use the outputs

1. Use the CSV as the complete feasibility log.
2. Use the markdown summary in supervisor meetings and methodology drafting.
3. Freeze the final case pair before any confirmatory modeling.
4. Keep excluded repositories visible in the archive.

## Academic positioning

Recommended wording for the methodology chapter:

> Repository case selection followed a predefined feasibility-screening pipeline analogous to inclusion screening in systematic literature reviews. Candidate repositories were evaluated on ex-ante observability and traceability criteria, not on substantive outcome effects. This preserved a separation between exploratory screening and confirmatory analysis while ensuring that selected cases contained sufficient AI, security, and discourse evidence to answer the research questions.
