# Introduction

## Background and motivation

AI tools have changed how code is produced in open-source software. Since late 2022, tools such as ChatGPT, Copilot, Cursor, Codex, and related coding agents have made it possible to write and submit code faster, in larger volume, and with less effort than before. This has made AI-assisted development an increasingly visible part of real repository activity rather than only a laboratory topic.

At the same time, open-source projects do not only need code to be written. They also need that code to be reviewed, maintained, and kept secure over time. In mature repositories, those tasks are already difficult because maintainers work under limited time and attention. If AI tools make it easier to submit more code, an important question follows: do observable indicators of maintainability, review activity, and security traceability also change?

This thesis approaches that question through two mature open-source cases, `microsoft/vscode` and `vercel/next.js`. Rather than treating AI as a general trend, the study focuses on pull requests with detectable AI-related signals and compares them with other pull requests in the same repositories.

## Problem statement

Current research offers only partial answers. Some studies show that AI tools can increase development speed. Others show that AI-generated code can contain quality or security weaknesses. Separate lines of research explain why code review quality and technical debt matter in software projects. However, these topics are usually studied separately. There is still limited empirical evidence on whether detectable AI-assisted contributions in real open-source repositories are associated with different patterns in technical debt proxies, review indicators, and security-traceability outcomes than non-AI-signaled contributions.

There is also a second gap in interpretation. Repository metrics can show whether patterns differ, but they cannot by themselves explain how maintainers understand or frame those changes. Public GitHub discussions provide useful evidence here because they show how contributors and maintainers talk about AI use, review burden, quality control, and security concerns in practice.

## Research objective

The objective of this thesis is to examine whether detectable AI-assisted contributions in `microsoft/vscode` and `vercel/next.js` are associated with different technical debt proxies, review indicators, and security-traceability patterns than other pull requests. To do this, the study combines pull-request-level AI-signal detection, quantitative comparison of maintainability and review metrics, CVE-linked traceability analysis, and qualitative analysis of public repository discourse.

The contribution of the thesis is to bring together four strands that are often studied separately: AI-contribution detection, maintainability and technical debt, code review dynamics, and security traceability. The thesis does not attempt to prove that AI causes poor outcomes. Instead, it asks a more defensible question: whether observable AI-related contributions are linked to different patterns in real projects, and how those patterns are described in public project discourse.

## Research questions

**Main question**

In mature open-source projects with documented security incidents, are detectable AI-assisted contributions associated with different technical debt proxies, review dynamics, and security-traceability patterns than non-AI-signaled contributions?

**Sub-questions**

1. `RQ1 Detection:` To what extent are detectable AI-assisted contributions identifiable in the selected projects, and what is their observable prevalence over time?
2. `RQ2 Technical debt and review:` How do AI-signaled and non-AI-signaled contributions differ in technical debt proxies and review indicators, and how do those indicators differ between the pre-2022 and post-2022 periods?
3. `RQ3 Security traceability:` Can documented vulnerabilities be traced to contribution and review pathways involving AI-signaled code, and what observable review characteristics accompany those pathways?
4. `RQ4 Public discourse:` How do maintainers and contributors describe and frame the effects of AI-assisted contributions on review burden, quality control, and security in public repository discussion?

## Thesis structure

Chapter 2 reviews the literature on AI-assisted software development, technical debt, code review, security, and the methodological foundations of the study. Chapter 3 presents the research questions in their final form. Chapter 4 explains the mixed-methods design, case selection process, AI-detection approach, quantitative metrics, CVE tracing, and qualitative discourse analysis. Chapter 5 presents the findings from the quantitative and qualitative analyses. Chapter 6 discusses what those findings mean, their limitations, and the broader implications for open-source governance. Chapter 7 concludes the thesis and outlines directions for future work.
