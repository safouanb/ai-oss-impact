# SLR Priority Sources

As of April 12, 2026, the current reference bank is strong enough to draft the literature review, but not strong enough to claim disciplined coverage of the thesis space. This note separates the highest-value additions from papers that are merely adjacent.

## Must add

These sources should be added before treating the literature review as stable.

### Directly relevant to the thesis argument

1. `hao2024`
   - Title: *An empirical study on developers' shared conversations with ChatGPT in GitHub pull requests and issues*
   - Why it matters: direct evidence for visible LLM use in GitHub PRs/issues, which is central to your discourse and observability claims for RQ1 and RQ4.
   - Link: https://link.springer.com/article/10.1007/s10664-024-10540-x

2. `xiao2024`
   - Title: *DevGPT: Studying Developer-ChatGPT Conversations*
   - Why it matters: foundational dataset/method paper for mining shared ChatGPT traces in GitHub artifacts; it anchors any discussion of observable AI use in collaborative development.
   - Link: https://arxiv.org/abs/2309.03914

3. `watanabe2025`
   - Title: *On the Use of Agentic Coding: An Empirical Study of Pull Requests on GitHub*
   - Why it matters: one of the closest external comparators to your thesis because it studies agent-generated PR acceptance, merge outcomes, and human revision.
   - Link: https://arxiv.org/abs/2509.14745

4. `minh2026`
   - Title: *Early-Stage Prediction of Review Effort in AI-Generated Pull Requests*
   - Why it matters: directly supports your review-burden and governance framing by operationalizing high-effort AI PRs and maintainer attention costs.
   - Link: https://arxiv.org/abs/2601.00753

5. `ogenrwot2026`
   - Title: *How AI Coding Agents Modify Code: A Large-Scale Study of GitHub Pull Requests*
   - Why it matters: large-scale evidence on how AI PRs differ structurally from human PRs; directly useful for interpreting your RQ2 metric differences.
   - Link: https://arxiv.org/abs/2601.17581

6. `pearce2021`
   - Title: *Asleep at the Keyboard? Assessing the Security of GitHub Copilot's Code Contributions*
   - Why it matters: still a core empirical security baseline for AI-generated code; your security section is weak without it.
   - Link: https://arxiv.org/abs/2108.09293

7. `pearce2023`
   - Title: *Examining Zero-Shot Vulnerability Repair with Large Language Models*
   - Why it matters: strengthens the security discussion by covering LLM-assisted repair, not only code generation.
   - Link: https://ieeexplore.ieee.org/abstract/document/10179324

8. `moreschini2026`
   - Title: *The Evolution of Technical Debt from DevOps to Generative AI: A multivocal literature review*
   - Why it matters: this is the strongest current bridge between technical debt and the GenAI era, which your debt framing currently lacks.
   - Link: https://www.sciencedirect.com/science/article/pii/S0164121225002687

### Methodology canon you should cite explicitly

9. `kitchenham2007`
   - Title: *Guidelines for performing Systematic Literature Reviews in Software Engineering*
   - Why it matters: if you call anything in this thesis an SLR, you need this or an equivalent software-engineering review protocol anchor.
   - Link: https://www.researchgate.net/publication/302924724_Guidelines_for_performing_Systematic_Literature_Reviews_in_Software_Engineering

10. `wohlin2014`
    - Title: *Guidelines for Snowballing in Systematic Literature Studies and a Replication in Software Engineering*
    - Why it matters: this is the right citation if your search process uses backward/forward snowballing instead of database-only screening.
    - Link: https://www.wohlin.eu/ease14.pdf

11. `runeson2009`
    - Title: *Guidelines for conducting and reporting case study research in software engineering*
    - Why it matters: your thesis is a two-case OSS study; this should be one of the methodological anchors.
    - Link: https://link.springer.com/article/10.1007/s10664-008-9102-8

12. `creswell2017`
    - Title: *Designing and Conducting Mixed Methods Research* (3rd ed.)
    - Why it matters: your design is explicitly mixed-methods; you should cite a mixed-methods methodology authority instead of only asserting that label.
    - Link: https://collegepublishing.sagepub.com/products/designing-and-conducting-mixed-methods-research-3-241842

## Nice to add

These are useful, but not as urgent as the list above.

1. `zeng2025`
   - Title: *Benchmarking and Studying the LLM-based Code Review*
   - Why it matters: useful if you want a stronger “automated review / LLM review capability” paragraph, but it is less central than papers on real AI-authored PRs.
   - Link: https://arxiv.org/abs/2509.01494

2. More peer-reviewed follow-up work around AIDev / agent-authored PRs after April 2026
   - Why it matters: the agentic PR literature is moving fast, and one or two more accepted papers may appear before submission.
   - Rule: only add them if they materially sharpen RQ1-RQ4, not just because they mention agents.

## Deprioritize

These are not the best use of time right now.

1. Generic GenAI surveys outside software engineering
   - They create breadth without helping your actual argument.

2. News articles, vendor blogs, and product announcements about AI code review or coding agents
   - Useful for context or motivation, not for the literature review core.

3. Benchmark-only code-generation papers with no OSS, PR, review, or governance angle
   - They are too far from your unit of analysis.

4. Extra supply-chain reports beyond one or two anchors
   - You already have enough industry risk background; the gap is empirical traceability, not more market reports.

## Practical rule

Do not try to collect everything. The literature review becomes thesis-grade once it has:

1. one solid observability/discourse strand,
2. one solid agentic-PR strand,
3. one solid technical-debt/maintainability strand,
4. one solid security strand,
5. one explicit methodology strand.

That is the threshold you should optimize for, not “maximum number of PDFs.”
