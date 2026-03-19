# Case selection memo

- Date: 2026-03-19
- Input list: `docs/prescan_candidates.txt`
- Protocol: `docs/case_selection_protocol.md`
- Prescan outputs:
  - `results/tables/case_prescan.csv`
  - `results/tables/case_prescan.md`
  - `results/figures/case_prescan_scores.png`

## Purpose

This memo records the prescan interpretation before confirmatory analysis starts.
The point of the prescan is simple: select cases on feasibility, not on observed results.

The prescan uses only four ex-ante variables:

1. Explicit AI-signal detectability.
2. GitHub security advisory traceability.
3. Repository maturity.
4. Public discussion volume.

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
It is not just first; it is first by a lot. It leads the field on explicit AI markers (`1647`), has very high public discussion volume, and still has enough published advisories (`23`) to support RQ3 tracing.

2. `vercel/next.js` is the cleanest secondary case.
Its AI signal is lower than `pytorch/pytorch`, but still strong enough (`70`), and its security advisory channel is much richer (`36`). It also gives better ecosystem contrast against `vscode` than another IDE or ML framework would.

3. `pytorch/pytorch` is the strongest backup if the study prioritizes AI-signal density.
It has a much larger explicit AI marker count than `next.js` (`144`), but only `5` GitHub advisories. That makes it somewhat weaker for a security-heavy thesis narrative.

4. `n8n-io/n8n` is the strongest backup if the study prioritizes security depth.
It has a viable AI signal (`58`) and a very strong advisory channel (`42`). The tradeoff is external-validity and prestige signal; it is less established than `vscode`, `next.js`, or `pytorch`.

## Cautionary note

`tensorflow/tensorflow` is technically eligible, but its advisory volume is unusually large (`427`) relative to its explicit AI signal (`4`). That makes it analytically usable, but not attractive as a balanced case if the goal is to study both AI detectability and security traceability in the same design.

## Proposed lock order

1. Primary: `microsoft/vscode`
2. Secondary: `vercel/next.js`
3. Backup secondary: `pytorch/pytorch`
4. Backup secondary: `n8n-io/n8n`

## Decision rule

The final two cases should be locked after supervisor review and before confirmatory modeling.

1. Keep `microsoft/vscode` unless a downstream data-access problem appears.
2. Prefer `vercel/next.js` if the goal is broader external relevance and a stronger web/security narrative.
3. Prefer `pytorch/pytorch` if the goal is higher AI-marker density in a prestigious mature project.
4. Prefer `n8n-io/n8n` if the goal is maximum security-advisory depth.
