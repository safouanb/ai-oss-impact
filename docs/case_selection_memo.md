# Case selection memo

- Date: 2026-03-19
- Input list: `docs/prescan_candidates.txt`
- Protocol: `docs/case_selection_protocol.md`
- Prescan outputs:
  - `results/tables/case_prescan.csv`
  - `results/tables/case_prescan.md`
  - `results/figures/case_prescan_scores.png`

## Purpose

This memo records the exploratory prescan decision context before confirmatory analysis starts.
The prescan is limited to feasibility variables: explicit AI-signal detectability, GitHub security
advisory traceability, maturity, and public discussion volume.

## Top-ranked candidates

| Rank | Repository | Prescan score | AI markers | Advisories | Eligible |
|---|---|---:|---:|---:|---|
| 1 | `microsoft/vscode` | 0.874 | 1647 | 23 | yes |
| 2 | `vercel/next.js` | 0.584 | 70 | 36 | yes |
| 3 | `pytorch/pytorch` | 0.575 | 144 | 5 | yes |
| 4 | `n8n-io/n8n` | 0.555 | 58 | 42 | yes |
| 5 | `home-assistant/core` | 0.537 | 41 | 13 | yes |

## Initial interpretation

1. `microsoft/vscode` is the clearest primary case.
   - It dominates on explicit AI markers.
   - It has strong maturity and discourse volume.
   - It has enough published GitHub advisories to support RQ3 traceability.

2. `vercel/next.js` is the strongest general-purpose secondary case.
   - It has solid explicit AI signal across multiple tools.
   - It has a stronger security advisory channel than most mature framework candidates.
   - It gives broader ecosystem contrast than another IDE or ML framework.

3. `pytorch/pytorch` is a serious alternative secondary case.
   - It has stronger AI-signal volume than `next.js`.
   - Its weaker point is the smaller advisory count, which may constrain RQ3 depth.

4. `n8n-io/n8n` is strong on advisories and still viable.
   - It is a good backup if the study wants denser security material.
   - It has lower prestige and external-validity signal than `next.js` or `pytorch`.

## Cautionary note

`tensorflow/tensorflow` is eligible, but its advisory volume is unusually large (`427`) and appears
to reflect a very broad GitHub advisory history. It is analytically viable, but it is not an ideal
case if the goal is a clean, balanced narrative around explicit AI-signal detectability.

## Proposed shortlist

1. Primary: `microsoft/vscode`
2. Secondary: `vercel/next.js`
3. Backup secondary: `pytorch/pytorch`
4. Backup secondary: `n8n-io/n8n`

## Decision rule for final lock

Lock the final two cases after supervisor review, using the following order:

1. Keep `microsoft/vscode` unless a downstream data-access problem appears.
2. Prefer `vercel/next.js` if the goal is broader external relevance and a stronger web/security narrative.
3. Prefer `pytorch/pytorch` if the goal is higher AI-marker density in a prestigious mature project.
4. Prefer `n8n-io/n8n` if the goal is maximum security-advisory depth.
