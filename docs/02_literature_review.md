# Literature review

This chapter is not yet written as thesis prose, but the source base is already strong enough to structure the review. The current SLR state is therefore best described as **source extraction complete enough to synthesize, but synthesis not yet drafted**.

The existing literature bank in `references/` already supports six review strands.

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

A working extraction sheet now exists at `docs/slr_literature_matrix.csv` so the review can move from isolated paper notes to a comparable evidence matrix.

Specifically:

1. Build a literature matrix with columns for `claim`, `method`, `unit of analysis`, `main finding`, `relevance to RQ1-RQ4`, and `limitations`.
2. Use that matrix to draft this chapter in narrative form rather than as paper-by-paper summaries.
3. Separate background literature from argument-serving literature:
   - background: code review, OSS governance, technical debt
   - argument-serving: AI contribution detection, AI quality/security evidence
4. End the chapter with the exact gap statement that justifies your two-case mixed-methods design.
