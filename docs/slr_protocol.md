# SLR Protocol

## Status

This protocol is the starting point for the literature-review process. As written, it is strong enough to execute a disciplined review workflow for the thesis. The review is **not complete** until the search log, screening sheet, and literature matrix are filled.

## Objective

Build a defensible software-engineering literature base for a master thesis on detectable AI-assisted contributions in open-source software, with emphasis on:

1. observability and detection of AI-related contributions,
2. code quality / technical debt / maintainability effects,
3. review dynamics and governance burden,
4. security-relevant outcomes and vulnerability/repair pathways,
5. methodological grounding for SLR, case study, and mixed-methods design.

## Review questions

The SLR component should answer these literature questions:

1. How do existing studies detect or observe AI-assisted contributions in public software-engineering artifacts?
2. What evidence exists on code quality, maintainability, technical debt, or structural differences in AI-assisted code changes?
3. What evidence exists on review effort, acceptance, governance, or human oversight of AI-authored pull requests?
4. What evidence exists on security weaknesses, vulnerability repair, or security-relevant consequences of AI-generated code?
5. Which methods, datasets, and units of analysis dominate the field, and what gaps remain that justify this thesis?

## Source types

Prioritize these source types:

1. Peer-reviewed empirical software-engineering papers.
2. High-quality arXiv preprints that are directly relevant to agentic pull requests or GitHub-based collaboration.
3. Methodology canon for SLR, snowballing, case study, and mixed methods.
4. A limited number of industry reports only when they anchor ecosystem/security context.

Deprioritize generic GenAI surveys, vendor blogs, and benchmark-only coding papers with no PR/review/governance angle.

## Search venues

Use the following search venues in order:

1. Google Scholar
2. ACM Digital Library
3. IEEE Xplore
4. SpringerLink
5. ScienceDirect
6. arXiv
7. Backward/forward snowballing from seed papers

## Search strings

Use focused search strings, not long natural-language prompts.

### Core AI contribution / GitHub strand

- `"AI-assisted" OR "AI-generated" OR "LLM" OR "coding agent" OR "agentic" AND "pull request" AND GitHub`
- `"ChatGPT" AND GitHub AND ("pull request" OR issue) AND developer`
- `"DevGPT" AND GitHub`

### Technical debt / maintainability strand

- `("AI-assisted" OR "agentic" OR LLM) AND ("technical debt" OR maintainability OR complexity) AND software`
- `("coding agent" OR "AI-generated code") AND maintainability`

### Review / governance strand

- `("AI-generated pull request" OR "agentic pull request") AND ("review effort" OR review OR governance)`
- `("LLM-based code review" OR "AI code review") AND software engineering`

### Security strand

- `("AI-generated code" OR Copilot OR LLM) AND security AND software`
- `("vulnerability repair" AND LLM) OR ("secure code generation" AND GitHub Copilot)`

### Methodology strand

- `"systematic literature review" AND "software engineering" AND guidelines`
- `"case study research" AND "software engineering" AND guidelines`
- `"mixed methods" AND research design`

## Inclusion criteria

Include a source if it meets all applicable conditions:

1. It is clearly relevant to at least one review question above.
2. It is empirical, methodological, or a high-signal review source.
3. For AI-specific evidence, it is preferably from 2021 to April 15, 2026.
4. For foundational theory or methods, older canonical sources are allowed.
5. The source has enough accessible detail to extract claims, methods, and limitations.

## Exclusion criteria

Exclude a source if:

1. It is a vendor blog, product announcement, or news article.
2. It focuses on generic LLM performance benchmarks without collaboration, GitHub, PR, review, or governance relevance.
3. It is outside software engineering unless it contributes directly to research-method justification.
4. It duplicates another source without adding substantive value.

## Screening procedure

1. Run keyword searches and record them in `docs/slr_search_log.csv`.
2. Add every candidate source to `docs/slr_screening_decisions.csv`.
3. Screen title/abstract first.
4. Mark each source as `include`, `exclude`, or `maybe`.
5. For included papers, create or update the corresponding `references/*.md` note.
6. Extract core information into `docs/slr_literature_matrix.csv`.
7. Use snowballing from the strongest seed papers and log those additions as well.

## Extraction fields

For each included source, fill:

1. `claim`
2. `method`
3. `unit_of_analysis`
4. `main_finding`
5. `relevance_to_rqs`
6. `limitations`
7. `notes`

## Completion definition

The SLR part is only considered done when all of the following are true:

1. `docs/slr_search_log.csv` records the actual search passes you ran.
2. `docs/slr_screening_decisions.csv` records include/exclude decisions and reasons.
3. `docs/slr_literature_matrix.csv` is filled for all included sources, not just seeded.
4. The must-add sources in `docs/slr_priority_sources.md` are extracted.
5. The literature chapter is written from themes, not paper-by-paper summaries.

## Immediate execution order

1. Finish the must-add `references/*.md` notes.
2. Run the first keyword search pass and log it.
3. Screen results into include/maybe/exclude.
4. Fill the matrix for included papers.
5. Draft the literature review narrative from the matrix.
