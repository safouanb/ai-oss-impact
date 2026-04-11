"""
Summarize PR metric comparisons for RQ2.

Outputs:
  - results/tables/pr_metric_analysis.csv
  - results/tables/pr_metric_analysis.md

Comparisons:
  1. post2022 AI-labeled PRs vs post2022 non-AI PRs
  2. pre2022 baseline PRs vs all post2022 PRs
"""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from pathlib import Path

PROCESSED_ROOT = Path("data/processed")
RESULTS_ROOT = Path("results/tables")
LOCKED_REPOS = ("microsoft/vscode", "vercel/next.js")

METRICS = (
    "added_lines",
    "deleted_lines",
    "changed_files",
    "commit_count",
    "analyzable_added_lines",
    "todo_fixme_count",
    "complexity_proxy",
    "security_kw_in_review",
    "review_duration_hours",
    "reviewer_count",
)


def repo_slug(repo: str) -> str:
    return repo.replace("/", "_")


def load_metrics(repo: str, filename: str) -> list[dict[str, str]]:
    path = PROCESSED_ROOT / repo_slug(repo) / filename
    if not path.exists():
        return []
    with path.open() as handle:
        return list(csv.DictReader(handle))


def coerce_metric(row: dict[str, str], metric: str) -> float | None:
    value = row.get(metric, "")
    if value in ("", None):
        return None
    return float(value)


def median_iqr(values: list[float]) -> tuple[float, float, float]:
    ordered = sorted(values)
    median = statistics.median(ordered)
    if len(ordered) == 1:
        return median, ordered[0], ordered[0]
    quartiles = statistics.quantiles(ordered, n=4, method="inclusive")
    return median, quartiles[0], quartiles[2]


def mann_whitney_u(sample_a: list[float], sample_b: list[float]) -> tuple[float, float, float]:
    n1 = len(sample_a)
    n2 = len(sample_b)
    if n1 == 0 or n2 == 0:
        return 0.0, 1.0, 0.0

    combined = [(value, 0) for value in sample_a] + [(value, 1) for value in sample_b]
    order = sorted(range(len(combined)), key=lambda idx: combined[idx][0])

    ranks = [0.0] * len(combined)
    tie_counts: list[int] = []
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and combined[order[j]][0] == combined[order[i]][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2
        for k in range(i, j):
            ranks[order[k]] = avg_rank
        tie_counts.append(j - i)
        i = j

    rank_sum_a = sum(ranks[:n1])
    u1 = rank_sum_a - (n1 * (n1 + 1) / 2)
    mean_u = n1 * n2 / 2

    n = n1 + n2
    tie_term = sum(count**3 - count for count in tie_counts)
    variance = (n1 * n2 / 12) * ((n + 1) - tie_term / (n * (n - 1))) if n > 1 else 0.0

    if variance <= 0:
        p_value = 1.0
    else:
        continuity = 0.5 if u1 > mean_u else (-0.5 if u1 < mean_u else 0.0)
        z = (u1 - mean_u - continuity) / math.sqrt(variance)
        p_value = math.erfc(abs(z) / math.sqrt(2))

    rank_biserial = (2 * u1) / (n1 * n2) - 1
    return u1, p_value, rank_biserial


def summarize_metric(
    repo: str,
    comparison: str,
    group_a_name: str,
    group_b_name: str,
    rows_a: list[dict[str, str]],
    rows_b: list[dict[str, str]],
) -> list[dict[str, str | float | int]]:
    summaries: list[dict[str, str | float | int]] = []

    for metric in METRICS:
        values_a = [value for row in rows_a if (value := coerce_metric(row, metric)) is not None]
        values_b = [value for row in rows_b if (value := coerce_metric(row, metric)) is not None]
        if not values_a or not values_b:
            continue

        median_a, q1_a, q3_a = median_iqr(values_a)
        median_b, q1_b, q3_b = median_iqr(values_b)
        u_stat, p_value, rank_biserial = mann_whitney_u(values_a, values_b)
        summaries.append(
            {
                "repo": repo,
                "comparison": comparison,
                "metric": metric,
                "group_a": group_a_name,
                "group_b": group_b_name,
                "n_a": len(values_a),
                "n_b": len(values_b),
                "median_a": round(median_a, 2),
                "q1_a": round(q1_a, 2),
                "q3_a": round(q3_a, 2),
                "median_b": round(median_b, 2),
                "q1_b": round(q1_b, 2),
                "q3_b": round(q3_b, 2),
                "median_diff_a_minus_b": round(median_a - median_b, 2),
                "u_stat": round(u_stat, 2),
                "p_value": round(p_value, 6),
                "rank_biserial": round(rank_biserial, 4),
            }
        )

    tests_in_family = len(summaries) or 1
    for row in summaries:
        adjusted = min(float(row["p_value"]) * tests_in_family, 1.0)
        row["bonferroni_p"] = round(adjusted, 6)

    return summaries


def write_csv(path: Path, rows: list[dict[str, str | float | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise SystemExit("no analysis rows to write")
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, str | float | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# PR Metric Analysis",
        "",
        "Generated by `scripts/analyze_pr_metrics.py`",
        "Tests use Mann-Whitney U with rank-biserial correlation and Bonferroni-adjusted p-values within each comparison family.",
        "",
    ]

    repos = list(dict.fromkeys(str(row["repo"]) for row in rows))
    comparisons = list(dict.fromkeys(str(row["comparison"]) for row in rows))

    for repo in repos:
        lines.append(f"## {repo}")
        lines.append("")
        for comparison in comparisons:
            subset = [
                row for row in rows
                if row["repo"] == repo and row["comparison"] == comparison
            ]
            if not subset:
                continue
            group_a = subset[0]["group_a"]
            group_b = subset[0]["group_b"]
            lines.append(f"### {comparison}: {group_a} vs {group_b}")
            lines.append("")
            lines.append("| Metric | n A | n B | Median A | Median B | Delta (A-B) | Rank-Biserial | Bonferroni p |")
            lines.append("|--------|-----|-----|----------|----------|-------------|---------------|--------------|")
            for row in subset:
                lines.append(
                    f"| {row['metric']} | {row['n_a']} | {row['n_b']} | "
                    f"{row['median_a']} | {row['median_b']} | {row['median_diff_a_minus_b']} | "
                    f"{row['rank_biserial']} | {row['bonferroni_p']} |"
                )
            lines.append("")

    path.write_text("\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", action="append", default=[])
    parser.add_argument("--repo-set", choices=("locked",), default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repos = list(args.repo)
    if args.repo_set == "locked":
        repos.extend(LOCKED_REPOS)
    if not repos:
        raise SystemExit("provide --repo or --repo-set locked")
    repos = list(dict.fromkeys(repos))

    all_rows: list[dict[str, str | float | int]] = []
    for repo in repos:
        post_rows = load_metrics(repo, "pr_metrics.csv")
        pre_rows = load_metrics(repo, "pr_metrics_pre2022.csv")
        if not post_rows:
            print(f"[warn] Missing post2022 metrics for {repo}")
            continue

        ai_rows = [row for row in post_rows if row.get("label") == "ai"]
        human_rows = [row for row in post_rows if row.get("label") != "ai"]
        if ai_rows and human_rows:
            all_rows.extend(
                summarize_metric(
                    repo,
                    "post2022_ai_vs_human",
                    "ai",
                    "non_ai",
                    ai_rows,
                    human_rows,
                )
            )

        if pre_rows:
            all_rows.extend(
                summarize_metric(
                    repo,
                    "pre2022_vs_post2022",
                    "post2022_all",
                    "pre2022_all",
                    post_rows,
                    pre_rows,
                )
            )

    csv_path = RESULTS_ROOT / "pr_metric_analysis.csv"
    md_path = RESULTS_ROOT / "pr_metric_analysis.md"
    write_csv(csv_path, all_rows)
    write_markdown(md_path, all_rows)

    print(f"Wrote {len(all_rows)} comparison rows")
    print(f"  CSV -> {csv_path}")
    print(f"  MD  -> {md_path}")


if __name__ == "__main__":
    main()
