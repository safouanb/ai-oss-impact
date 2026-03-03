# Case selection protocol

## Purpose

This protocol defines how repositories are selected for the thesis case study while avoiding outcome-based cherry-picking.

The goal of prescanning is **feasibility validation**, not hypothesis confirmation.

## Why prescan?

Case-study research requires checking whether candidate cases have enough observable data to answer the research questions.  
Without this check, the study risks selecting cases with no detectable AI signal, no traceable security incidents, or insufficient public discourse.

Prescanning is acceptable when:

1. Criteria are defined before main analysis.
2. Selection variables are independent from primary dependent outcomes.
3. The full candidate set and exclusions are documented.

## Selection inputs (feasibility variables only)

The prescan uses only metadata and traceability indicators:

1. **AI detectability**
   - Presence of explicit agent markers in PR/commit metadata (e.g., branch prefixes, bot accounts, co-author signatures).
2. **Security traceability**
   - Availability of documented security advisories and CVE-linked release information.
3. **Repository maturity**
   - Age, adoption footprint, sustained maintenance activity.
4. **Discourse richness**
   - Sufficient PR/issue/release discussion volume for qualitative mining.

The prescan does **not** use:

1. Technical debt effect sizes.
2. Security outcome directionality.
3. Any model results tied to RQ2/RQ3 hypotheses.

## Inclusion criteria

A repository is eligible if it satisfies all of the following:

1. Mature and widely used OSS project.
2. Publicly documented security history suitable for commit-level tracing.
3. Detectable AI-related contribution signals (explicit markers and/or AIDev alignment).
4. Adequate public discussion artifacts for qualitative coding.

## Prescan procedure

1. Build a broad candidate list of mature repositories.
2. Collect feasibility metadata for each candidate.
3. Score candidates using a fixed rubric.
4. Select one primary and one secondary case.
5. Freeze selected cases before confirmatory analysis.
6. Archive prescan outputs (including rejected candidates and reasons).

## Anti-Cherry-Picking Controls

1. **Design lock**: Main analysis starts only after case freeze.
2. **Audit trail**: Keep full prescan table and selection memo in version control.
3. **Transparent exclusions**: Report why each non-selected candidate was excluded.
4. **Exploratory/confirmatory separation**: Clearly label prescan as exploratory feasibility work.

## Reporting Template (Methodology Chapter)

Use wording similar to:

> Case selection followed a predefined feasibility protocol. Candidate repositories were evaluated using ex-ante criteria (AI signal traceability, security advisory traceability, project maturity, and discourse volume). These criteria were independent from the primary quantitative outcomes. Cases were frozen before confirmatory modeling, and all screened candidates with inclusion/exclusion reasons were retained in the research archive to reduce selection bias.

## Known Limitations

1. Public metadata under-detects AI usage when contributors do not leave explicit markers.
2. Advisory ecosystems differ by project and may not be fully normalized across repositories.
3. Feasibility-based case selection improves analyzability but does not guarantee representativeness of all OSS.

These limitations are reported explicitly in validity threats and addressed through sensitivity analyses where feasible.
