"""
Download AIDev dataset from HuggingFace, filter for locked case repos,
and save a repository-specific PR index for downstream label generation.

Source: Li et al. (2025) — AIDev dataset (arXiv:2507.15003)
        https://huggingface.co/datasets/hao-li/AIDev

The AIDev dataset is the PRIMARY detection source per the thesis proposal (§4.3).
This script stores the AIDev PR index under `data/processed/aidev_pr_index.json`.
`detect_ai_contributions.py` then uses that index during label generation so
the AIDev signal is part of the main labeling path rather than a detached
post-hoc override.

Usage:
    pip install datasets pandas pyarrow
    python scripts/fetch_aidev.py
    python scripts/fetch_aidev.py --repo microsoft/vscode
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PROCESSED_ROOT = Path("data/processed")
LOCKED_REPOS = ("microsoft/vscode", "vercel/next.js")

def repo_slug(repo: str) -> str:
    return repo.replace("/", "_")


def load_aidev_for_repos(repos: list[str]) -> dict[str, set[int]]:
    """
    Download the canonical AIDev PR parquet from HuggingFace and return a dict
    mapping repo -> set of PR numbers confirmed AI-authored by AIDev.
    """
    try:
        from huggingface_hub import hf_hub_download
        import pyarrow.parquet as pq
    except ImportError:
        raise SystemExit(
            "Required packages not installed. Run: pip install datasets pyarrow"
        )

    print("Downloading AIDev PR parquet from HuggingFace (this may take a few minutes)...")
    print("Dataset: hao-li/AIDev / all_pull_request.parquet")
    print("Source: Li et al. (2025) — arXiv:2507.15003")

    aidev_prs: dict[str, set[int]] = {repo: set() for repo in repos}

    try:
        parquet_path = hf_hub_download(
            repo_id="hao-li/AIDev",
            repo_type="dataset",
            filename="all_pull_request.parquet",
        )
        table = pq.read_table(parquet_path, columns=["repo_url", "number"])
        repo_urls = table.column("repo_url").to_pylist()
        pr_numbers = table.column("number").to_pylist()

        for repo_url, pr_num in zip(repo_urls, pr_numbers):
            if not repo_url or "/repos/" not in repo_url or pr_num is None:
                continue
            repo_name = str(repo_url).split("/repos/", 1)[1].strip("/")
            if repo_name in repos and pr_num is not None:
                aidev_prs[repo_name].add(int(pr_num))
    except Exception as exc:
        raise SystemExit(f"Could not load AIDev pull-request parquet: {exc}")

    return aidev_prs


def save_aidev_index(repos: list[str], aidev_prs: dict[str, set[int]]) -> None:
    """Save a lookup index of AIDev PR numbers per repo for audit trail."""
    out = {}
    for repo in repos:
        out[repo] = sorted(aidev_prs[repo])
    path = Path("data/processed/aidev_pr_index.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2))
    print(f"\nAIDev PR index saved -> {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without writing files")
    args = parser.parse_args()

    repos = list(args.repo) or list(LOCKED_REPOS)

    aidev_prs = load_aidev_for_repos(repos)

    print("\n=== AIDev coverage for your cases ===")
    for repo in repos:
        count = len(aidev_prs[repo])
        print(f"  {repo}: {count} PRs found in AIDev")

    if args.dry_run:
        print("\n[dry-run] No files written.")
        return

    save_aidev_index(repos, aidev_prs)

    print("\n=== AIDev index written ===")
    for repo in repos:
        print(f"  {repo}: {len(aidev_prs[repo])} AIDev PRs indexed")

    print(
        "\nDone. Re-run detect_ai_contributions.py so AIDev becomes part of "
        "the main PR and commit labeling flow."
    )


if __name__ == "__main__":
    main()
