"""
Fetch commit and pull request data from the GitHub API for a target repository.

Writes JSON files to data/raw/.

Usage:
    python scripts/fetch_github_data.py --repo facebook/react --since 2018-01-01 --until 2026-03-01
"""

import argparse
import json
import os
from pathlib import Path

import requests

TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}
OUT = Path("data/raw")


def paginate(url, params=None):
    results = []
    while url:
        r = requests.get(url, headers=HEADERS, params=params)
        r.raise_for_status()
        results.extend(r.json())
        url = r.links.get("next", {}).get("url")
        params = None
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--since", default="2018-01-01")
    parser.add_argument("--until", default="2026-03-01")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    slug = args.repo.replace("/", "_")

    print(f"fetching commits for {args.repo} ...")
    commits = paginate(
        f"https://api.github.com/repos/{args.repo}/commits",
        {"since": args.since, "until": args.until, "per_page": 100},
    )
    (OUT / f"{slug}_commits.json").write_text(json.dumps(commits, indent=2))
    print(f"  {len(commits)} commits")

    print(f"fetching pull requests ...")
    prs = paginate(
        f"https://api.github.com/repos/{args.repo}/pulls",
        {"state": "all", "per_page": 100},
    )
    (OUT / f"{slug}_pulls.json").write_text(json.dumps(prs, indent=2))
    print(f"  {len(prs)} PRs")


if __name__ == "__main__":
    main()
