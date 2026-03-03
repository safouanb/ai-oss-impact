"""
Label commits as AI-generated or human-authored.

Uses heuristics from the AIDev dataset (Li et al., 2025):
  - known bot usernames (devin, copilot agent, etc.)
  - commit message patterns that indicate AI authorship
  - .cursor/ directory traces in diffs

Reads from data/raw/<slug>_commits.json, writes to data/processed/<slug>_labelled.csv.

Usage:
    python scripts/detect_ai_contributions.py --repo facebook/react
"""

import argparse
import json
import re
from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/processed")

BOT_LOGINS = {
    "devin-ai-integration",
    "copilot-swe-agent",
    "dependabot[bot]",
}

AI_PATTERNS = [
    re.compile(r"generated (by|with|using) (copilot|cursor|devin|claude|chatgpt)", re.I),
    re.compile(r"co-authored-by:.*copilot", re.I),
    re.compile(r"\[cursor\]", re.I),
]


def label(commit):
    login = (commit.get("author") or {}).get("login", "").lower()
    msg = commit.get("commit", {}).get("message", "")

    if login in BOT_LOGINS:
        return "ai", "bot_username", 0.95

    for p in AI_PATTERNS:
        if p.search(msg):
            return "ai", "commit_message", 0.80

    return "unknown", "-", 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()

    slug = args.repo.replace("/", "_")
    src = RAW / f"{slug}_commits.json"
    if not src.exists():
        print(f"run fetch_github_data.py first — no data at {src}")
        return

    commits = json.loads(src.read_text())
    rows = []
    for c in commits:
        l, method, conf = label(c)
        rows.append({
            "sha": c["sha"],
            "author": (c.get("author") or {}).get("login"),
            "date": c["commit"]["author"]["date"],
            "label": l,
            "method": method,
            "confidence": conf,
        })

    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    out = OUT / f"{slug}_labelled.csv"
    df.to_csv(out, index=False)

    ai_count = (df["label"] == "ai").sum()
    print(f"{len(df)} commits labelled, {ai_count} flagged as AI → {out}")


if __name__ == "__main__":
    main()
