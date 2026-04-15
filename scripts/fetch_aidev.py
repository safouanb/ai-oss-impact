"""
Download AIDev dataset from HuggingFace, filter for locked case repos,
and save a repository-specific PR index + merge labels into pr_labels.csv.

Source: Li et al. (2025) — AIDev dataset (arXiv:2507.15003)
        https://huggingface.co/datasets/hao-li/AIDev
        Config: 'pull_request', split: 'train'
        Schema: id, number, title, body, agent, user_id, user, state,
                created_at, closed_at, merged_at, repo_id, repo_url, html_url

The AIDev dataset is the PRIMARY detection source per the thesis proposal (§4.3).
Agent label values observed: OpenAI_Codex, Devin, Claude_Code, Cursor, Copilot

Usage:
    pip install datasets pyarrow
    python scripts/fetch_aidev.py
    python scripts/fetch_aidev.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

PROCESSED_ROOT = Path("data/processed")
LOCKED_REPOS = ("microsoft/vscode", "vercel/next.js")

AGENT_DISPLAY = {
    "OpenAI_Codex": "OpenAI Codex",
    "Devin": "Devin",
    "Claude_Code": "Claude Code",
    "Cursor": "Cursor",
    "Copilot": "GitHub Copilot",
}


def repo_slug(repo: str) -> str:
    return repo.replace("/", "_")


def load_aidev_for_repos(repos: list[str]) -> dict[str, list[dict]]:
    """
    Stream the AIDev pull_request config and collect all PRs for target repos.
    Returns dict mapping repo -> list of {pr_number, agent, html_url, created_at, ...}
    """
    try:
        from datasets import load_dataset
    except ImportError:
        raise SystemExit("Run: pip install datasets pyarrow")

    print("Loading AIDev dataset from HuggingFace (streaming — no full download)...")
    print("Source: Li et al. (2025) — arXiv:2507.15003")
    print("Config: pull_request / train\n")

    ds = load_dataset("hao-li/AIDev", "pull_request", streaming=True, split="train")

    found: dict[str, list[dict]] = {r: [] for r in repos}
    checked = 0

    for row in ds:
        repo_url = row.get("repo_url", "") or ""
        # repo_url looks like https://api.github.com/repos/microsoft/vscode
        if "/repos/" not in repo_url:
            continue
        repo_name = repo_url.split("/repos/", 1)[1].rstrip("/")
        if repo_name in found:
            found[repo_name].append({
                "pr_number": row["number"],
                "agent": row.get("agent", "unknown"),
                "agent_display": AGENT_DISPLAY.get(row.get("agent", ""), row.get("agent", "")),
                "html_url": row.get("html_url", ""),
                "created_at": row.get("created_at", ""),
                "merged_at": row.get("merged_at", ""),
                "state": row.get("state", ""),
                "title": row.get("title", ""),
            })
        checked += 1
        if checked % 20000 == 0:
            totals = {r: len(v) for r, v in found.items()}
            print(f"  Scanned {checked:,} rows ... {totals}", flush=True)

    return found


def save_aidev_index(found: dict[str, list[dict]]) -> None:
    out = {}
    for repo, rows in found.items():
        out[repo] = {
            "count": len(rows),
            "pr_numbers": sorted(set(r["pr_number"] for r in rows)),
            "agents": sorted(set(r["agent"] for r in rows)),
        }
    path = PROCESSED_ROOT / "aidev_pr_index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2))
    print(f"\nAIDev PR index -> {path}")


def merge_into_pr_labels(repo: str, rows: list[dict], dry_run: bool) -> int:
    """
    Upsert AIDev rows into data/processed/<slug>/pr_labels.csv.
    Existing rows for a PR number are updated only if the current source is
    not already 'aidev_dataset' (so we don't overwrite existing AIDev entries).
    New PR numbers not already in the file are appended.
    Returns number of rows written/updated.
    """
    slug = repo_slug(repo)
    labels_path = PROCESSED_ROOT / slug / "pr_labels.csv"

    if not labels_path.exists():
        print(f"  WARNING: {labels_path} not found — skipping label merge for {repo}")
        return 0

    with labels_path.open() as f:
        existing = list(csv.DictReader(f))

    existing_by_pr: dict[int, dict] = {int(r["pr_number"]): r for r in existing}
    fieldnames = list(existing[0].keys()) if existing else [
        "repo", "pr_number", "label", "confidence_tier", "confidence_score",
        "source", "signal_count", "evidence",
    ]

    updated = 0
    for row in rows:
        pr_num = int(row["pr_number"])
        entry = existing_by_pr.get(pr_num)
        agent_tag = f"aidev:{row['agent']}"
        # Handle both schema variants:
        # narrow: evidence, source  |  wide: evidence_json (no source column)
        uses_wide = "evidence_json" in fieldnames

        def already_aidev(e: dict) -> bool:
            if uses_wide:
                return "aidev:" in (e.get("evidence_json") or "")
            return e.get("source") == "aidev_dataset"

        def set_aidev(e: dict) -> None:
            e["label"] = "ai"
            e["confidence_tier"] = "high"
            e["confidence_score"] = "1.0"
            e["signal_count"] = "1"
            if uses_wide:
                import json as _json
                e["evidence_json"] = _json.dumps([agent_tag])
            else:
                e["source"] = "aidev_dataset"
                e["evidence"] = agent_tag

        if entry is not None:
            if not already_aidev(entry):
                set_aidev(entry)
                updated += 1
        else:
            new_row = {k: "" for k in fieldnames}
            new_row["repo"] = repo
            new_row["pr_number"] = str(pr_num)
            set_aidev(new_row)
            existing_by_pr[pr_num] = new_row
            updated += 1

    if not dry_run:
        all_rows = sorted(existing_by_pr.values(), key=lambda r: int(r["pr_number"]))
        with labels_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)

    return updated


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repos = list(args.repo) or list(LOCKED_REPOS)

    found = load_aidev_for_repos(repos)

    print("\n=== AIDev coverage for your cases ===")
    for repo, rows in found.items():
        agents = {}
        for r in rows:
            agents[r["agent"]] = agents.get(r["agent"], 0) + 1
        print(f"  {repo}: {len(rows)} PRs — {agents}")

    if args.dry_run:
        print("\n[dry-run] No files written.")
        return

    save_aidev_index(found)

    print("\n=== Merging AIDev labels into pr_labels.csv ===")
    total = 0
    for repo, rows in found.items():
        if not rows:
            print(f"  {repo}: 0 AIDev PRs — nothing to merge")
            continue
        n = merge_into_pr_labels(repo, rows, dry_run=False)
        print(f"  {repo}: {n} rows written/updated")
        total += n

    print(f"\nTotal: {total} label rows updated across {len(repos)} repos")
    print("Done. Re-run detect_ai_contributions.py to regenerate summaries.")


if __name__ == "__main__":
    main()
