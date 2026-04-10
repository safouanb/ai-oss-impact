"""
Create a stratified manual-validation sample from PR label outputs.

Usage:
    python scripts/sample_validation_prs.py --repo-set locked --per-tier 20
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

PROCESSED_ROOT = Path("data/processed")
RESULTS_ROOT = Path("results/tables")
LOCKED_REPOS = ("microsoft/vscode", "vercel/next.js")
TARGET_TIERS = ("high", "medium", "none")


def repo_slug(repo: str) -> str:
    return repo.replace("/", "_")


def select_repos(explicit_repos: list[str], repo_set: str | None) -> list[str]:
    repos = list(explicit_repos)
    if repo_set == "locked":
        repos.extend(LOCKED_REPOS)
    if not repos:
        raise SystemExit("provide at least one --repo or use --repo-set locked")
    return list(dict.fromkeys(repos))


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"missing label file: {path}")
    with path.open() as handle:
        return list(csv.DictReader(handle))


def shorten_evidence(evidence_json: str, limit: int = 3) -> str:
    evidence = json.loads(evidence_json or "[]")
    compact = [f"{item['level']}:{item['source']}={item['evidence']}" for item in evidence[:limit]]
    return " | ".join(compact)


def sample_rows(rows: list[dict[str, str]], per_tier: int, seed: int) -> list[dict[str, str]]:
    rng = random.Random(seed)
    sampled: list[dict[str, str]] = []

    for tier in TARGET_TIERS:
        bucket = [row for row in rows if row["confidence_tier"] == tier]
        if not bucket:
            continue
        take = min(per_tier, len(bucket))
        sampled.extend(rng.sample(bucket, take))

    return sampled


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise SystemExit("no validation rows selected")
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", action="append", default=[])
    parser.add_argument("--repo-set", choices=("locked",), default=None)
    parser.add_argument("--per-tier", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--out",
        type=Path,
        default=RESULTS_ROOT / "rq1_validation_sample.csv",
        help="Output CSV for manual validation.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repos = select_repos(args.repo, args.repo_set)
    sampled_rows: list[dict[str, str]] = []

    for repo in repos:
        slug = repo_slug(repo)
        rows = load_rows(PROCESSED_ROOT / slug / "pr_labels.csv")
        repo_sample = sample_rows(rows, per_tier=args.per_tier, seed=args.seed)
        for row in repo_sample:
            sampled_rows.append(
                {
                    "repo": row["repo"],
                    "pr_number": row["pr_number"],
                    "created_at": row["created_at"],
                    "title": row["title"],
                    "author_login": row["author_login"],
                    "label": row["label"],
                    "confidence_tier": row["confidence_tier"],
                    "confidence_score": row["confidence_score"],
                    "signal_count": row["signal_count"],
                    "evidence_preview": shorten_evidence(row["evidence_json"]),
                    "manual_label": "",
                    "review_notes": "",
                }
            )

    write_csv(args.out, sampled_rows)
    print(f"wrote {len(sampled_rows)} validation rows -> {args.out}")


if __name__ == "__main__":
    main()
