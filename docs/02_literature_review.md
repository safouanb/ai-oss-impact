# Literature review

This chapter is not yet written as thesis prose, but the literature base is now substantially more formalized than before. The current SLR state is best described as **screened and scoped, with matrix extraction complete for the included core corpus, but narrative synthesis still not drafted**.

The existing literature bank in `references/` together with the audit-trail files in `docs/slr_*.csv` supports six review strands.

## The velocity–quality trade-off

Core sources for this section:

- `references/li2025.md`: AIDev paper on autonomous coding-agent pull requests at ecosystem scale
- `references/he2025.md`: recent empirical evidence on AI-assisted development quality/acceptance dynamics
- `references/fu2023.md`: code-generation quality and risk evidence

This section should establish the central tension in the thesis: AI tools increase contribution throughput, but the consequences for review burden, code quality, and downstream risk remain mixed.

## Code review as the defence that gets overwhelmed

Core sources for this section:

- `references/bacchelli2013.md`: why modern code review matters and how it works in practice
- `references/mcintosh2016.md`: review quality, inspection coverage, and defect implications
- `references/mockus2002.md`: OSS process and coordination foundations

This section should frame review as the main governance mechanism that stands between increased contribution volume and degraded code integration quality.

## AI-generated code and known security weaknesses

Core sources for this section:

- `references/sonatype2024.md`: software supply-chain risk and open-source security pressure
- `references/blackduck2025.md`: vulnerability and governance trends in OSS consumption
- `references/intruder2025.md`: AI code security weaknesses / exploitability discussion

This section should distinguish between generic supply-chain risk and the narrower question your thesis asks: whether AI-signaled contributions can be traced to security-relevant review and vulnerability pathways.

## Technical debt: the slow accumulation of unmaintainable code

Core sources for this section:

- `references/avgeriou2023.md`: technical debt foundations and taxonomy
- `references/zazworka2011.md`: debt and software quality impact
- `references/shivashankar2024.md`: more recent debt / maintainability framing

This section should justify the debt proxies in your design: deferred-work markers, complexity proxies, maintainability-oriented patch signals, and the broader argument that local shortcuts create downstream maintenance costs.

## Detecting AI-generated code

Core sources for this section:

- `references/li2025.md`: AIDev as the primary external dataset
- `references/moonlight2025.md`: summary material around agent contribution detection
- `references/react2025.md`: repository-visible policy / contribution artefacts relevant to AI-assisted development

This section should make the measurement problem explicit: public metadata can identify only **detectable AI assistance**, not all AI usage. That is why your thesis should keep using terms such as `AI-assisted`, `AI-signaled`, or `detectable AI-related contributions` rather than claiming universal detection.

## The gap this thesis addresses

The literature base currently supports a clear gap statement:

1. AI-in-SE studies increasingly measure speed, acceptance, or benchmark performance.
2. Technical-debt research explains why maintainability costs matter, but usually without AI-attribution.
3. Security and supply-chain reports document rising risk, but usually at ecosystem or package-management level rather than at pull-request traceability level.
4. Code-review research explains reviewer effort and governance capacity, but not specifically under AI-driven contribution growth.

The thesis gap is therefore not “AI code might be risky.” That claim is too generic. The actual gap is:

> existing work does not combine detectable AI-attributed OSS contributions, technical-debt proxies, review dynamics, and CVE-linked traceability in a single mixed-methods case design.

## What the SLR needs next

The next SLR step is not collecting many more papers. It is synthesis.

A working extraction sheet now exists at `docs/slr_literature_matrix.csv`, and the current included corpus has been screened into a core set plus contextual grey-literature anchors.

The highest-priority additions are tracked explicitly in `docs/slr_priority_sources.md`, and the included or excluded status of candidate papers is now recorded in `docs/slr_screening_decisions.csv`.

The SLR workflow itself is now documented in `docs/slr_protocol.md`, with executed search passes logged in `docs/slr_search_log.csv`, screening outcomes in `docs/slr_screening_decisions.csv`, and source-file availability in `docs/slr_source_inventory.csv`.

What remains is:

1. convert the extracted matrix into narrative prose rather than paper-by-paper summaries,
2. keep background literature clearly separate from argument-serving literature,
3. decide whether any final post-April-2026 follow-up paper materially changes the corpus,
4. end the chapter with the exact gap statement that justifies the two-case mixed-methods design.
