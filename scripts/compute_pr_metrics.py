"""
Compute code quality and technical debt metrics for each PR (RQ2).

Metrics computed per PR (proposal §4.4):
  - added_lines, deleted_lines, changed_files
  - todo_fixme_count       : deferred debt markers in patch additions
  - complexity_proxy       : avg cyclomatic complexity estimate from patch
                             (counted as number of decision keywords: if/for/while/
                              case/catch/&&/||/? per 100 added lines)
  - security_keyword_count : security-relevant words in review comments
                             (vulnerability/cve/injection/xss/auth/exploit/sanitiz)
  - review_duration_hours  : hours from PR open to merge (or last update)
  - reviewer_count         : distinct human reviewers
  - review_comment_count   : already in pr_labels.csv
  - merge_rate             : 1 if merged else 0

Output:
  data/processed/<slug>/pr_metrics.csv
  data/processed/<slug>/pr_metrics_pre2022.csv  (if pre-2022 data exists)

Usage:
    python scripts/compute_pr_metrics.py --repo-set locked
    python scripts/compute_pr_metrics.py --repo microsoft/vscode --period both
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

RAW_ROOT = Path("data/raw")
PROCESSED_ROOT = Path("data/processed")
LOCKED_REPOS = ("microsoft/vscode", "vercel/next.js")

# Deferred debt markers in added lines
TODO_PATTERN = re.compile(r"\b(TODO|FIXME|HACK|XXX|TEMP|NOSONAR)\b", re.I)

# Decision-point keywords for cyclomatic complexity proxy
DECISION_PATTERN = re.compile(
    r"\b(if|else\s+if|elif|for|while|case|catch|except|&&|\|\||\?\s+\w)"
)

# Security-relevant words in review comments
SECURITY_PATTERN = re.compile(
    r"\b(vulnerabilit|cve|inject|xss|csrf|sqli|rce|auth|sanitiz|escap|exploit"
    r"|bypass|overflow|traversal|deseri|privilege|malici)\w*\b",
    re.I,
)


def repo_slug(repo: str) -> str:
    return repo.replace("/", "_")


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_pr_labels(repo: str) -> dict[int, dict]:
    path = PROCESSED_ROOT / repo_slug(repo) / "pr_labels.csv"
    if not path.exists():
        return {}
    with path.open() as f:
        return {int(r["pr_number"]): r for r in csv.DictReader(f)}


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def metrics_from_bundle(bundle: dict, label_row: dict | None) -> dict:
    detail = bundle.get("detail", {})
    files = bundle.get("files", [])
    reviews = bundle.get("reviews", [])
    review_comments = bundle.get("review_comments", [])
    issue_comments = bundle.get("issue_comments", [])
    commits = bundle.get("commits", [])

    pr_num = detail.get("number") or (bundle.get("summary") or {}).get("number", 0)
    author = (detail.get("user") or {}).get("login", "")
    created_at = detail.get("created_at", "")
    merged_at = detail.get("merged_at")
    updated_at = detail.get("updated_at", "")
    merged = bool(merged_at)

    # Lines
    added = sum(f.get("additions", 0) for f in files)
    deleted = sum(f.get("deletions", 0) for f in files)

    # TODO/FIXME in patch additions only (lines starting with +)
    todo_count = 0
    decision_count = 0
    for f in files:
        patch = f.get("patch") or ""
        for line in patch.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                todo_count += len(TODO_PATTERN.findall(line))
                decision_count += len(DECISION_PATTERN.findall(line))

    # Cyclomatic complexity proxy: decisions per 100 added lines.
    # Set to None for very small PRs (<10 added lines) to avoid denominator
    # instability (a single keyword in 1-2 lines produces extreme outliers).
    # Use median (not mean) in downstream analysis.
    if added >= 10:
        complexity_proxy = round((decision_count / added) * 100, 2)
    else:
        complexity_proxy = None

    # Security keywords in review text
    all_review_text = " ".join(
        [r.get("body") or "" for r in reviews]
        + [c.get("body") or "" for c in review_comments]
        + [c.get("body") or "" for c in issue_comments]
    )
    security_kw_count = len(SECURITY_PATTERN.findall(all_review_text))

    # Review duration
    end_dt = parse_dt(merged_at or updated_at)
    start_dt = parse_dt(created_at)
    review_duration_hours = None
    if start_dt and end_dt:
        review_duration_hours = round(
            (end_dt - start_dt).total_seconds() / 3600, 2
        )

    # Distinct human reviewers (exclude bots and the PR author)
    bot_suffixes = ("[bot]", "-bot", "copilot", "dependabot")
    reviewers = set()
    for r in reviews:
        login = (r.get("user") or {}).get("login", "").lower()
        if login and login != author.lower() and not any(
            login.endswith(s) for s in bot_suffixes
        ):
            reviewers.add(login)
    reviewer_count = len(reviewers)

    # AI label from pr_labels.csv
    label = "unresolved"
    confidence_tier = "none"
    confidence_score = 0.0
    aidev_sourced = False
    if label_row:
        label = label_row.get("label", "unresolved")
        confidence_tier = label_row.get("confidence_tier", "none")
        confidence_score = float(label_row.get("confidence_score", 0.0))
        evidence = json.loads(label_row.get("evidence_json") or "[]")
        aidev_sourced = any(s.get("source") == "aidev_dataset" for s in evidence)

    return {
        "pr_number": pr_num,
        "author_login": author,
        "created_at": created_at,
        "merged_at": merged_at or "",
        "merged": int(merged),
        "added_lines": added,
        "deleted_lines": deleted,
        "changed_files": len(files),
        "commit_count": len(commits),
        "todo_fixme_count": todo_count,
        "complexity_proxy": complexity_proxy,
        "security_kw_in_review": security_kw_count,
        "review_duration_hours": review_duration_hours,
        "reviewer_count": reviewer_count,
        "review_comment_count": len(review_comments),
        "issue_comment_count": len(issue_comments),
        "label": label,
        "confidence_tier": confidence_tier,
        "confidence_score": confidence_score,
        "aidev_sourced": int(aidev_sourced),
    }


def process_repo(repo: str, period: str) -> None:
    slug = repo_slug(repo)
    raw_dir = RAW_ROOT / slug
    processed_dir = PROCESSED_ROOT / slug
    processed_dir.mkdir(parents=True, exist_ok=True)

    label_map = load_pr_labels(repo)

    periods_to_run = []
    if period in ("post", "both"):
        post_path = raw_dir / "pull_requests.jsonl"
        if post_path.exists():
            periods_to_run.append(("post2022", post_path,
                                   processed_dir / "pr_metrics.csv"))
        else:
            print(f"  Warning: {post_path} not found — skipping post-2022")

    if period in ("pre", "both"):
        pre_path = raw_dir / "pull_requests_pre2022.jsonl"
        if pre_path.exists():
            periods_to_run.append(("pre2022", pre_path,
                                   processed_dir / "pr_metrics_pre2022.csv"))
        else:
            print(f"  Warning: {pre_path} not found — run fetch_pre2022_data.py first")

    for period_name, jsonl_path, out_path in periods_to_run:
        print(f"  Processing {period_name} data: {jsonl_path} ...", flush=True)
        bundles = load_jsonl(jsonl_path)
        rows = []
        for bundle in bundles:
            detail = bundle.get("detail", {})
            pr_num = detail.get("number") or (bundle.get("summary") or {}).get("number")
            label_row = label_map.get(int(pr_num)) if pr_num else None
            row = metrics_from_bundle(bundle, label_row)
            row["repo"] = repo
            row["period"] = period_name
            rows.append(row)

        if not rows:
            print(f"    No rows computed for {period_name}")
            continue

        with out_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        ai_prs = [r for r in rows if r["label"] == "ai"]
        human_prs = [r for r in rows if r["label"] != "ai"]

        def avg(lst, key):
            vals = [v[key] for v in lst if v[key] is not None]
            return round(sum(vals) / len(vals), 2) if vals else None

        print(f"    {period_name}: {len(rows)} PRs | "
              f"AI={len(ai_prs)} human={len(human_prs)}")
        if ai_prs and human_prs:
            print(f"    Complexity proxy — AI: {avg(ai_prs, 'complexity_proxy')} "
                  f"| Human: {avg(human_prs, 'complexity_proxy')}")
            print(f"    TODO/FIXME — AI: {avg(ai_prs, 'todo_fixme_count')} "
                  f"| Human: {avg(human_prs, 'todo_fixme_count')}")
            print(f"    Review duration (hrs) — AI: {avg(ai_prs, 'review_duration_hours')} "
                  f"| Human: {avg(human_prs, 'review_duration_hours')}")
            print(f"    Reviewer count — AI: {avg(ai_prs, 'reviewer_count')} "
                  f"| Human: {avg(human_prs, 'reviewer_count')}")
        print(f"    Written -> {out_path}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", action="append", default=[])
    parser.add_argument("--repo-set", choices=("locked",), default=None)
    parser.add_argument(
        "--period",
        choices=("post", "pre", "both"),
        default="post",
        help="Which period to compute: post (2023+), pre (2018-2022), or both",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repos = list(args.repo)
    if args.repo_set == "locked":
        repos.extend(LOCKED_REPOS)
    if not repos:
        raise SystemExit("provide --repo or --repo-set locked")
    repos = list(dict.fromkeys(repos))

    print(f"Computing PR metrics for: {repos} | period={args.period}\n")
    for repo in repos:
        print(f"\n[{repo}]")
        process_repo(repo, args.period)

    print("\nMetrics complete.")
    print("Next: open results in a notebook or run trace_cve_commits.py for RQ3.")


if __name__ == "__main__":
    main()
