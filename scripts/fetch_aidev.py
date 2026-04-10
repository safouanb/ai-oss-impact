"""
Download AIDev dataset from HuggingFace, filter for locked case repos,
and merge AI labels into existing pr_labels.csv files.

Source: Li et al. (2025) — AIDev dataset (arXiv:2507.15003)
        https://huggingface.co/datasets/hao-li/AIDev

The AIDev dataset is the PRIMARY detection source per the thesis proposal (§4.3).
Labels from AIDev override or supplement local heuristic labels in detect_ai_contributions.py.

Usage:
    pip install datasets pandas pyarrow
    python scripts/fetch_aidev.py
    python scripts/fetch_aidev.py --repo microsoft/vscode
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

PROCESSED_ROOT = Path("data/processed")
LOCKED_REPOS = ("microsoft/vscode", "vercel/next.js")

# AIDev agent names as they appear in the dataset
AIDEV_AGENTS = ("OpenAI Codex", "Devin", "GitHub Copilot", "Cursor", "Claude Code")


def repo_slug(repo: str) -> str:
    return repo.replace("/", "_")


def load_aidev_for_repos(repos: list[str]) -> dict[str, set[int]]:
    """
    Download AIDev from HuggingFace and return a dict mapping
    repo_slug -> set of PR numbers confirmed AI-authored by AIDev.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        raise SystemExit(
            "datasets package not installed. Run: pip install datasets pyarrow"
        )

    print("Loading AIDev dataset from HuggingFace (this may take a few minutes)...")
    print("Dataset: hao-li/AIDev  (Li et al., 2025 — arXiv:2507.15003)")

    # AIDev is split by agent. Load all splits.
    aidev_prs: dict[str, set[int]] = {repo: set() for repo in repos}

    for agent in AIDEV_AGENTS:
        split_name = agent.lower().replace(" ", "_").replace(".", "")
        print(f"  Loading agent split: {agent} ...", flush=True)
        try:
            ds = load_dataset("hao-li/AIDev", split=split_name, streaming=True)
            for row in ds:
                repo_name = row.get("repo_name") or row.get("full_name") or ""
                pr_num = row.get("pr_number") or row.get("number")
                if repo_name in repos and pr_num is not None:
                    aidev_prs[repo_name].add(int(pr_num))
        except Exception as exc:
            print(f"    Warning: could not load split '{split_name}': {exc}")

    return aidev_prs


def load_pr_labels(repo: str) -> list[dict]:
    path = PROCESSED_ROOT / repo_slug(repo) / "pr_labels.csv"
    if not path.exists():
        raise SystemExit(f"Missing pr_labels.csv for {repo}: {path}")
    with path.open() as f:
        return list(csv.DictReader(f))


def write_pr_labels(repo: str, rows: list[dict]) -> None:
    path = PROCESSED_ROOT / repo_slug(repo) / "pr_labels.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def merge_aidev_labels(
    rows: list[dict], aidev_pr_numbers: set[int]
) -> tuple[list[dict], int]:
    """
    For each PR in rows, if the PR number is in aidev_pr_numbers:
      - set label = 'ai'
      - set confidence_tier = 'high'
      - set confidence_score = 1.0  (externally validated)
      - prepend 'aidev_dataset' to evidence_json

    Returns updated rows and count of newly promoted labels.
    """
    promoted = 0
    for row in rows:
        pr_num = int(row["pr_number"])
        if pr_num in aidev_pr_numbers:
            was_unresolved = row["label"] != "ai"
            row["label"] = "ai"
            row["confidence_tier"] = "high"
            row["confidence_score"] = "1.0"

            # Prepend AIDev signal to evidence
            existing = json.loads(row.get("evidence_json") or "[]")
            aidev_signal = {
                "level": "high",
                "source": "aidev_dataset",
                "evidence": "PR appears in Li et al. (2025) AIDev dataset — externally validated agent-authored PR",
            }
            row["evidence_json"] = json.dumps([aidev_signal] + existing)

            if was_unresolved:
                promoted += 1

    return rows, promoted


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

    save_aidev_index(repos, aidev_prs)

    if args.dry_run:
        print("\n[dry-run] No files written.")
        return

    print("\n=== Merging AIDev labels into pr_labels.csv ===")
    for repo in repos:
        if not aidev_prs[repo]:
            print(f"  {repo}: no AIDev PRs found — local heuristic labels unchanged")
            continue

        rows = load_pr_labels(repo)
        rows, promoted = merge_aidev_labels(rows, aidev_prs[repo])
        write_pr_labels(repo, rows)

        total_ai = sum(1 for r in rows if r["label"] == "ai")
        total_aidev = sum(
            1 for r in rows
            if "aidev_dataset" in r.get("evidence_json", "")
        )
        print(
            f"  {repo}: {len(aidev_prs[repo])} AIDev PRs → "
            f"{promoted} newly promoted from unresolved | "
            f"{total_ai} total AI-labeled | {total_aidev} AIDev-sourced"
        )

    print("\nDone. AIDev labels merged. Re-run detect_ai_contributions.py "
          "to regenerate commit-level labels from updated PR labels.")


if __name__ == "__main__":
    main()
