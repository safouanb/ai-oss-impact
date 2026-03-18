"""
Repository prescan pipeline for case selection.

This script is intentionally limited to feasibility variables. It does not inspect
technical debt outcomes or vulnerability effects. The goal is to rank candidate
repositories on observability and analyzability before confirmatory analysis starts.

Usage:
    python scripts/prescan_cases.py --repos docs/prescan_candidates.txt
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib
import requests

matplotlib.use("Agg")

import matplotlib.pyplot as plt

API_ROOT = "https://api.github.com"
DEFAULT_REPOS = Path("docs/prescan_candidates.txt")
DEFAULT_CSV = Path("results/tables/case_prescan.csv")
DEFAULT_MD = Path("results/tables/case_prescan.md")
DEFAULT_FIG = Path("results/figures/case_prescan_scores.png")

# Fixed feasibility thresholds to avoid outcome-driven tuning.
MIN_STARS = 10_000
MIN_PUBLIC_DISCUSSION = 1_000
RECENT_ADVISORY_CUTOFF = "2024-01-01"

AI_MARKERS = (
    ("codex_branch", "head:codex/"),
    ("copilot_branch", "head:copilot/"),
    ("cursor_branch", "head:cursor/"),
    ("devin_bot", "author:devin-ai-integration[bot]"),
    ("claude_coauthor", '"Co-Authored-By: Claude"'),
)


@dataclass
class RepoPrescan:
    repo: str
    stars: int
    forks: int
    subscribers: int
    open_issues: int
    age_years: float
    default_branch: str
    advisories_total: int
    advisories_high_or_critical: int
    advisories_recent: int
    advisories_critical: int
    pr_count: int
    issue_count: int
    marker_counts: dict[str, int] = field(default_factory=dict)
    ai_markers_total: int = 0
    ai_detectability_norm: float = 0.0
    security_traceability_norm: float = 0.0
    discourse_richness_norm: float = 0.0
    maturity_norm: float = 0.0
    prescan_score: float = 0.0
    eligible: bool = False
    exclusion_reasons: list[str] = field(default_factory=list)

    def to_csv_row(self) -> dict[str, Any]:
        row = {
            "repo": self.repo,
            "stars": self.stars,
            "forks": self.forks,
            "subscribers": self.subscribers,
            "open_issues": self.open_issues,
            "age_years": round(self.age_years, 2),
            "default_branch": self.default_branch,
            "advisories_total": self.advisories_total,
            "advisories_high_or_critical": self.advisories_high_or_critical,
            "advisories_recent": self.advisories_recent,
            "advisories_critical": self.advisories_critical,
            "pr_count": self.pr_count,
            "issue_count": self.issue_count,
            "ai_markers_total": self.ai_markers_total,
            "ai_detectability_norm": round(self.ai_detectability_norm, 4),
            "security_traceability_norm": round(self.security_traceability_norm, 4),
            "discourse_richness_norm": round(self.discourse_richness_norm, 4),
            "maturity_norm": round(self.maturity_norm, 4),
            "prescan_score": round(self.prescan_score, 4),
            "eligible": self.eligible,
            "exclusion_reasons": ";".join(self.exclusion_reasons),
        }
        for name, _ in AI_MARKERS:
            row[name] = self.marker_counts.get(name, 0)
        return row


class GitHubClient:
    def __init__(self, token: str | None, sleep_seconds: float | None = None) -> None:
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/vnd.github+json"})
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.sleep_seconds = sleep_seconds if sleep_seconds is not None else (0.25 if token else 7.0)

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> Any:
        while True:
            response = self.session.get(url, params=params, timeout=60)
            if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
                reset = int(response.headers.get("X-RateLimit-Reset", "0"))
                wait_seconds = max(reset - int(time.time()) + 2, 2)
                print(f"[rate-limit] waiting {wait_seconds}s for {url}")
                time.sleep(wait_seconds)
                continue
            response.raise_for_status()
            resource = response.headers.get("X-RateLimit-Resource", "")
            if resource == "search":
                time.sleep(self.sleep_seconds)
            return response.json()

    def repo_metadata(self, repo: str) -> dict[str, Any]:
        return self.get_json(f"{API_ROOT}/repos/{repo}")

    def search_count(self, query: str) -> int:
        payload = self.get_json(f"{API_ROOT}/search/issues", params={"q": query, "per_page": 1})
        return int(payload.get("total_count", 0))

    def security_advisories(self, repo: str) -> list[dict[str, Any]]:
        advisories: list[dict[str, Any]] = []
        page = 1
        while True:
            payload = self.get_json(
                f"{API_ROOT}/repos/{repo}/security-advisories",
                params={"state": "published", "per_page": 100, "page": page},
            )
            if not payload:
                break
            advisories.extend(payload)
            if len(payload) < 100:
                break
            page += 1
        return advisories


def load_repos(path: Path) -> list[str]:
    repos: list[str] = []
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        repos.append(line)
    return repos


def years_since(timestamp: str) -> float:
    created = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    delta = now - created
    return delta.days / 365.25


def collect_repo(client: GitHubClient, repo: str) -> RepoPrescan:
    meta = client.repo_metadata(repo)
    advisories = client.security_advisories(repo)

    marker_counts: dict[str, int] = {}
    ai_total = 0
    for name, fragment in AI_MARKERS:
        count = client.search_count(f"repo:{repo} is:pr {fragment}")
        marker_counts[name] = count
        ai_total += count

    pr_count = client.search_count(f"repo:{repo} is:pr")
    issue_count = client.search_count(f"repo:{repo} is:issue")

    high_or_critical = sum(1 for advisory in advisories if advisory.get("severity") in {"high", "critical"})
    recent = sum(
        1 for advisory in advisories if (advisory.get("published_at") or "") >= RECENT_ADVISORY_CUTOFF
    )
    critical = sum(1 for advisory in advisories if advisory.get("severity") == "critical")

    return RepoPrescan(
        repo=repo,
        stars=int(meta.get("stargazers_count", 0)),
        forks=int(meta.get("forks_count", 0)),
        subscribers=int(meta.get("subscribers_count", 0)),
        open_issues=int(meta.get("open_issues_count", 0)),
        age_years=years_since(meta["created_at"]),
        default_branch=meta.get("default_branch", ""),
        advisories_total=len(advisories),
        advisories_high_or_critical=high_or_critical,
        advisories_recent=recent,
        advisories_critical=critical,
        pr_count=pr_count,
        issue_count=issue_count,
        marker_counts=marker_counts,
        ai_markers_total=ai_total,
    )


def normalize_series(values: list[float]) -> list[float]:
    low = min(values)
    high = max(values)
    if math.isclose(low, high):
        return [0.0 for _ in values]
    return [(value - low) / (high - low) for value in values]


def apply_scoring(rows: list[RepoPrescan]) -> None:
    ai_norm = normalize_series([math.log1p(row.ai_markers_total) for row in rows])
    advisory_norm = normalize_series([math.log1p(row.advisories_total) for row in rows])
    advisory_hc_norm = normalize_series([math.log1p(row.advisories_high_or_critical) for row in rows])
    advisory_recent_norm = normalize_series([math.log1p(row.advisories_recent) for row in rows])
    discourse_norm = normalize_series([math.log1p(row.pr_count + row.issue_count) for row in rows])
    stars_norm = normalize_series([math.log1p(row.stars) for row in rows])
    age_norm = normalize_series([row.age_years for row in rows])

    for idx, row in enumerate(rows):
        row.ai_detectability_norm = ai_norm[idx]
        row.security_traceability_norm = (
            0.25 * advisory_norm[idx] + 0.45 * advisory_hc_norm[idx] + 0.30 * advisory_recent_norm[idx]
        )
        row.discourse_richness_norm = discourse_norm[idx]
        row.maturity_norm = 0.60 * stars_norm[idx] + 0.40 * age_norm[idx]
        row.prescan_score = (
            0.40 * row.ai_detectability_norm
            + 0.30 * row.security_traceability_norm
            + 0.20 * row.discourse_richness_norm
            + 0.10 * row.maturity_norm
        )
        row.eligible, row.exclusion_reasons = evaluate_eligibility(row)

    rows.sort(key=lambda item: item.prescan_score, reverse=True)


def evaluate_eligibility(row: RepoPrescan) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if row.stars < MIN_STARS:
        reasons.append("low_stars")
    if row.ai_markers_total == 0:
        reasons.append("no_explicit_ai_markers")
    if row.advisories_total == 0:
        reasons.append("no_github_security_advisories")
    if (row.pr_count + row.issue_count) < MIN_PUBLIC_DISCUSSION:
        reasons.append("low_public_discussion")
    return not reasons, reasons


def write_csv(rows: list[RepoPrescan], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].to_csv_row().keys())
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_csv_row())


def write_markdown(rows: list[RepoPrescan], path: Path, repos_path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    eligible_rows = [row for row in rows if row.eligible]
    top_rows = rows[: min(10, len(rows))]

    lines = [
        "# Case prescan summary",
        "",
        f"- Generated: {generated_at}",
        f"- Candidate list: `{repos_path}`",
        f"- Eligible cases: {len(eligible_rows)}/{len(rows)}",
        "",
        "## Fixed criteria",
        "",
        f"- Minimum stars: `{MIN_STARS}`",
        f"- Minimum PR + issue volume: `{MIN_PUBLIC_DISCUSSION}`",
        f"- Recent advisory cutoff: `{RECENT_ADVISORY_CUTOFF}`",
        "- Eligibility requires AI detectability, GitHub security advisory traceability, maturity, and public discourse.",
        "",
        "## Ranked candidates",
        "",
        "| Rank | Repo | Score | AI markers | Advisories | PRs | Issues | Eligible |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]

    for idx, row in enumerate(top_rows, start=1):
        lines.append(
            f"| {idx} | `{row.repo}` | {row.prescan_score:.3f} | {row.ai_markers_total} | "
            f"{row.advisories_total} | {row.pr_count} | {row.issue_count} | "
            f"{'yes' if row.eligible else 'no'} |"
        )

    lines.extend(
        [
            "",
            "## Exclusions",
            "",
        ]
    )

    for row in rows:
        if row.eligible:
            continue
        reason_text = ", ".join(row.exclusion_reasons) if row.exclusion_reasons else "not excluded"
        lines.append(f"- `{row.repo}`: {reason_text}")

    path.write_text("\n".join(lines) + "\n")


def write_figure(rows: list[RepoPrescan], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    ranked = list(reversed(rows))
    labels = [row.repo for row in ranked]
    scores = [row.prescan_score for row in ranked]
    colors = ["#0a7d34" if row.eligible else "#9aa4b2" for row in ranked]

    fig, ax = plt.subplots(figsize=(12, max(5, len(rows) * 0.45)))
    bars = ax.barh(labels, scores, color=colors)

    ax.set_title("Repository prescan ranking")
    ax.set_xlabel("Prescan score")
    ax.set_xlim(0, 1.0)
    ax.grid(axis="x", linestyle="--", alpha=0.25)
    ax.set_axisbelow(True)

    for bar, score in zip(bars, scores):
        ax.text(
            score + 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{score:.2f}",
            va="center",
            ha="left",
            fontsize=9,
        )

    legend_handles = [
        plt.Rectangle((0, 0), 1, 1, color="#0a7d34", label="eligible"),
        plt.Rectangle((0, 0), 1, 1, color="#9aa4b2", label="excluded"),
    ]
    ax.legend(handles=legend_handles, loc="lower right")

    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repos", type=Path, default=DEFAULT_REPOS)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_MD)
    parser.add_argument("--out-fig", type=Path, default=DEFAULT_FIG)
    parser.add_argument("--sleep-seconds", type=float, default=None)
    parser.add_argument(
        "--allow-no-token",
        action="store_true",
        help="Allow unauthenticated GitHub API access. This is slow and likely to hit rate limits.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        if not args.allow_no_token:
            raise SystemExit(
                "GITHUB_TOKEN is required for a full prescan. "
                "Set it in the environment or rerun with --allow-no-token for a slow, rate-limited run."
            )
        print("warning: GITHUB_TOKEN not set; GitHub Search API will be slow and heavily rate-limited.")

    repos = load_repos(args.repos)
    if not repos:
        raise SystemExit(f"no repositories found in {args.repos}")

    client = GitHubClient(token=token, sleep_seconds=args.sleep_seconds)
    rows: list[RepoPrescan] = []
    total = len(repos)
    for idx, repo in enumerate(repos, start=1):
        print(f"[{idx}/{total}] collecting {repo} ...", flush=True)
        row = collect_repo(client, repo)
        rows.append(row)
        print(
            f"[{idx}/{total}] {repo}: ai_markers={row.ai_markers_total}, "
            f"advisories={row.advisories_total}, prs={row.pr_count}, issues={row.issue_count}",
            flush=True,
        )

    apply_scoring(rows)
    write_csv(rows, args.out_csv)
    write_markdown(rows, args.out_md, args.repos)
    write_figure(rows, args.out_fig)

    print(f"wrote {len(rows)} rows -> {args.out_csv}")
    print(f"wrote markdown summary -> {args.out_md}")
    print(f"wrote figure -> {args.out_fig}")


if __name__ == "__main__":
    main()
