"""
Label pull requests and linked commits for likely AI involvement.

This script reads the PR bundles written by scripts/fetch_github_data.py and produces:
  - data/processed/<slug>/pr_labels.csv
  - data/processed/<slug>/commit_labels.csv
  - data/processed/<slug>/summary.json

Usage:
    python scripts/detect_ai_contributions.py --repo microsoft/vscode
    python scripts/detect_ai_contributions.py --repo-set locked
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

RAW_ROOT = Path("data/raw")
PROCESSED_ROOT = Path("data/processed")
LOCKED_REPOS = ("microsoft/vscode", "vercel/next.js")

HIGH_BRANCH_PREFIXES = (
    ("codex_branch", "codex/"),
    ("copilot_branch", "copilot/"),
    ("cursor_branch", "cursor/"),
)

HIGH_BOT_LOGINS = {
    "copilot-swe-agent",
    "devin-ai-integration[bot]",
    "devin-ai-integration",
}

HIGH_TEXT_PATTERNS = (
    ("explicit_ai_generation", re.compile(r"(generated|written|created)\s+(by|with|using)\s+.*(copilot|cursor|devin|claude|chatgpt|codex)", re.I)),
    ("ai_coauthor", re.compile(r"co-authored-by:.*(copilot|cursor|claude|chatgpt|codex)", re.I)),
)

MEDIUM_TEXT_PATTERNS = (
    ("agent_reference", re.compile(r"\b(copilot|cursor|devin|claude|chatgpt|codex)\b", re.I)),
)

MEDIUM_FILE_PATTERNS = (
    ("cursor_artifact", re.compile(r"(^|/)\.cursor(/|$)")),
    ("cursor_rule_file", re.compile(r"(^|/)\.cursorrules$")),
)


def repo_slug(repo: str) -> str:
    return repo.replace("/", "_")


def select_repos(explicit_repos: list[str], repo_set: str | None) -> list[str]:
    repos: list[str] = list(explicit_repos)
    if repo_set == "locked":
        repos.extend(LOCKED_REPOS)
    if not repos:
        raise SystemExit("provide at least one --repo or use --repo-set locked")
    return list(dict.fromkeys(repos))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def add_signal(signals: list[dict[str, str]], level: str, source: str, evidence: str) -> None:
    signals.append({"level": level, "source": source, "evidence": evidence})


def scan_text(signals: list[dict[str, str]], text: str, source_prefix: str) -> None:
    if not text:
        return

    for source, pattern in HIGH_TEXT_PATTERNS:
        if pattern.search(text):
            snippet = pattern.search(text).group(0)
            add_signal(signals, "high", f"{source_prefix}:{source}", snippet[:160])

    for source, pattern in MEDIUM_TEXT_PATTERNS:
        if pattern.search(text):
            snippet = pattern.search(text).group(0)
            add_signal(signals, "medium", f"{source_prefix}:{source}", snippet[:160])


def scan_login(signals: list[dict[str, str]], login: str | None, source_prefix: str) -> None:
    normalized = (login or "").lower()
    if normalized in HIGH_BOT_LOGINS:
        add_signal(signals, "high", f"{source_prefix}:bot_login", normalized)


def scan_branch(signals: list[dict[str, str]], head_ref: str | None) -> None:
    normalized = (head_ref or "").lower()
    for source, prefix in HIGH_BRANCH_PREFIXES:
        if normalized.startswith(prefix):
            add_signal(signals, "high", f"pr:{source}", normalized)


def scan_files(signals: list[dict[str, str]], files: list[dict[str, Any]]) -> None:
    for file_info in files:
        filename = file_info.get("filename", "")
        normalized = filename.lower()
        for source, pattern in MEDIUM_FILE_PATTERNS:
            if pattern.search(normalized):
                add_signal(signals, "medium", f"file:{source}", filename)


def score_signals(signals: list[dict[str, str]]) -> tuple[str, str, float]:
    high_count = sum(1 for signal in signals if signal["level"] == "high")
    medium_count = sum(1 for signal in signals if signal["level"] == "medium")

    if high_count >= 1:
        return "ai", "high", 0.95
    if medium_count >= 2:
        return "ai", "medium", 0.75
    return "unresolved", "none", 0.0


def pr_record(repo: str, bundle: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    detail = bundle["detail"]
    summary = bundle["summary"]
    reviews = bundle["reviews"]
    review_comments = bundle["review_comments"]
    issue_comments = bundle["issue_comments"]
    commits = bundle["commits"]
    files = bundle["files"]

    signals: list[dict[str, str]] = []

    head_ref = ((detail.get("head") or {}).get("ref")) or ""
    author_login = ((detail.get("user") or {}).get("login")) or ""

    scan_branch(signals, head_ref)
    scan_login(signals, author_login, "pr_author")
    scan_text(signals, detail.get("title") or "", "pr_title")
    scan_text(signals, detail.get("body") or "", "pr_body")
    scan_files(signals, files)

    commit_records: list[dict[str, Any]] = []
    commit_signal_union: list[dict[str, str]] = []

    for commit in commits:
        commit_signals: list[dict[str, str]] = []
        scan_login(commit_signals, ((commit.get("author") or {}).get("login")), "commit_author")
        scan_text(commit_signals, ((commit.get("commit") or {}).get("message")) or "", "commit_message")

        label, confidence_tier, confidence_score = score_signals(commit_signals)
        commit_record = {
            "repo": repo,
            "pr_number": detail["number"],
            "commit_sha": commit["sha"],
            "commit_author_login": ((commit.get("author") or {}).get("login")) or "",
            "commit_author_name": (((commit.get("commit") or {}).get("author")) or {}).get("name", ""),
            "commit_date": (((commit.get("commit") or {}).get("author")) or {}).get("date", ""),
            "label": label,
            "confidence_tier": confidence_tier,
            "confidence_score": confidence_score,
            "label_origin": "commit_signal" if label == "ai" else "",
            "signal_count": len(commit_signals),
            "evidence_json": json.dumps(commit_signals),
        }
        commit_records.append(commit_record)
        commit_signal_union.extend(commit_signals)

    signals.extend(commit_signal_union)
    pr_label, pr_confidence_tier, pr_confidence_score = score_signals(signals)

    propagated_records: list[dict[str, Any]] = []
    for commit_record in commit_records:
        if commit_record["label"] == "unresolved" and pr_label == "ai":
            commit_record["label"] = "ai"
            commit_record["confidence_tier"] = pr_confidence_tier
            commit_record["confidence_score"] = pr_confidence_score
            commit_record["label_origin"] = "propagated_pr"
        propagated_records.append(commit_record)

    pr_row = {
        "repo": repo,
        "pr_number": detail["number"],
        "state": detail.get("state", summary.get("state", "")),
        "draft": bool(detail.get("draft", False)),
        "title": detail.get("title", ""),
        "author_login": author_login,
        "head_ref": head_ref,
        "base_ref": ((detail.get("base") or {}).get("ref")) or "",
        "created_at": detail.get("created_at", ""),
        "updated_at": detail.get("updated_at", ""),
        "merged_at": detail.get("merged_at", ""),
        "merged": bool(detail.get("merged_at")),
        "review_count": len(reviews),
        "review_comment_count": len(review_comments),
        "issue_comment_count": len(issue_comments),
        "commit_count": len(commits),
        "file_count": len(files),
        "label": pr_label,
        "confidence_tier": pr_confidence_tier,
        "confidence_score": pr_confidence_score,
        "signal_count": len(signals),
        "evidence_json": json.dumps(signals),
    }
    return pr_row, propagated_records


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise SystemExit(f"no rows to write for {path}")
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def label_repo(repo: str) -> dict[str, Any]:
    slug = repo_slug(repo)
    raw_dir = RAW_ROOT / slug
    processed_dir = PROCESSED_ROOT / slug
    source = raw_dir / "pull_requests.jsonl"
    if not source.exists():
        raise SystemExit(f"missing raw PR bundle file: {source}")

    bundles = load_jsonl(source)
    pr_rows: list[dict[str, Any]] = []
    commit_rows: list[dict[str, Any]] = []

    for bundle in bundles:
        pr_row, commit_records = pr_record(repo, bundle)
        pr_rows.append(pr_row)
        commit_rows.extend(commit_records)

    write_csv(processed_dir / "pr_labels.csv", pr_rows)
    write_csv(processed_dir / "commit_labels.csv", commit_rows)

    summary = {
        "repo": repo,
        "pull_request_count": len(pr_rows),
        "commit_count": len(commit_rows),
        "pr_label_counts": {
            "ai_high": sum(1 for row in pr_rows if row["label"] == "ai" and row["confidence_tier"] == "high"),
            "ai_medium": sum(1 for row in pr_rows if row["label"] == "ai" and row["confidence_tier"] == "medium"),
            "unresolved": sum(1 for row in pr_rows if row["label"] == "unresolved"),
        },
        "commit_label_counts": {
            "ai_high": sum(1 for row in commit_rows if row["label"] == "ai" and row["confidence_tier"] == "high"),
            "ai_medium": sum(1 for row in commit_rows if row["label"] == "ai" and row["confidence_tier"] == "medium"),
            "unresolved": sum(1 for row in commit_rows if row["label"] == "unresolved"),
        },
        "paths": {
            "pr_labels": str(processed_dir / "pr_labels.csv"),
            "commit_labels": str(processed_dir / "commit_labels.csv"),
        },
    }
    write_json(processed_dir / "summary.json", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", action="append", default=[], help="Repository in owner/name format.")
    parser.add_argument(
        "--repo-set",
        choices=("locked",),
        default=None,
        help="Convenience set of repositories from the working case lock.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repos = select_repos(args.repo, args.repo_set)
    summaries = []
    for repo in repos:
        print(f"labelling {repo} ...", flush=True)
        summary = label_repo(repo)
        summaries.append(summary)
        print(
            f"  PRs={summary['pull_request_count']} "
            f"(high={summary['pr_label_counts']['ai_high']}, medium={summary['pr_label_counts']['ai_medium']}, "
            f"unresolved={summary['pr_label_counts']['unresolved']})",
            flush=True,
        )

    print("\nfinished labelling run", flush=True)
    for summary in summaries:
        print(f"- {summary['repo']}: {summary['paths']['pr_labels']}", flush=True)


if __name__ == "__main__":
    main()
