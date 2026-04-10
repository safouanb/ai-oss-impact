"""
Collect pre-AI-era (2018-2022) PR data for project-level trend analysis (RQ2).

This extends fetch_github_data.py to collect a historical baseline.
The proposal (§4.4) requires tracking metrics across:
  - pre-AI period:  2018-01-01 to 2022-12-31
  - post-AI period: 2023-01-01 to present  (already collected)

Output:
  data/raw/<slug>/pull_requests_pre2022.jsonl
  data/raw/<slug>/manifest_pre2022.json

Usage:
    python scripts/fetch_pre2022_data.py --repo-set locked
    python scripts/fetch_pre2022_data.py --repo microsoft/vscode --max-prs 500
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

RAW_ROOT = Path("data/raw")
LOCKED_REPOS = ("microsoft/vscode", "vercel/next.js")

PRE_AI_SINCE = "2018-01-01T00:00:00Z"
PRE_AI_UNTIL = "2022-12-31T23:59:59Z"
DEFAULT_MAX_PRS = 500


def repo_slug(repo: str) -> str:
    return repo.replace("/", "_")


def get_token() -> str | None:
    import os
    from dotenv import load_dotenv
    load_dotenv()
    return os.environ.get("GITHUB_TOKEN")


def github_get(url: str, token: str | None, params: dict | None = None) -> dict | list:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(7):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=60)
        except requests.exceptions.Timeout:
            wait = 2 ** attempt
            print(f"  Timeout — retrying in {wait}s ...", flush=True)
            time.sleep(wait)
            continue
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            wait = int(resp.headers.get("Retry-After", 60))
            print(f"  Rate limited — waiting {wait}s ...", flush=True)
            time.sleep(wait)
            continue
        if resp.status_code in (500, 502, 503, 504):
            wait = 2 ** attempt
            print(f"  HTTP {resp.status_code} — retrying in {wait}s ...", flush=True)
            time.sleep(wait)
            continue
        resp.raise_for_status()
    raise RuntimeError(f"Failed after retries: {url}")


def paginate(url: str, token: str | None, params: dict | None = None) -> list:
    results = []
    page = 1
    while True:
        p = dict(params or {})
        p["per_page"] = 100
        p["page"] = page
        data = github_get(url, token, p)
        if not data:
            break
        results.extend(data)
        if len(data) < 100:
            break
        page += 1
    return results


def fetch_pr_bundle(pr: dict, repo: str, token: str | None) -> dict:
    """Fetch full PR detail including reviews, commits, files."""
    base = f"https://api.github.com/repos/{repo}"
    num = pr["number"]

    detail = github_get(f"{base}/pulls/{num}", token)
    reviews = paginate(f"{base}/pulls/{num}/reviews", token)
    review_comments = paginate(f"{base}/pulls/{num}/comments", token)
    issue_comments = paginate(f"{base}/issues/{num}/comments", token)
    commits = paginate(f"{base}/pulls/{num}/commits", token)
    files = paginate(f"{base}/pulls/{num}/files", token)

    return {
        "summary": pr,
        "detail": detail,
        "reviews": reviews,
        "review_comments": review_comments,
        "issue_comments": issue_comments,
        "commits": commits,
        "files": files,
    }


def fetch_pre2022_prs(repo: str, token: str | None, max_prs: int) -> None:
    slug = repo_slug(repo)
    raw_dir = RAW_ROOT / slug
    out_path = raw_dir / "pull_requests_pre2022.jsonl"
    manifest_path = raw_dir / "manifest_pre2022.json"

    if out_path.exists():
        print(f"  {repo}: pre-2022 data already exists at {out_path}, skipping.")
        print(f"  Delete {out_path} to re-collect.")
        return

    print(f"  Fetching pre-2022 PRs for {repo} (since={PRE_AI_SINCE}, until={PRE_AI_UNTIL}) ...", flush=True)

    # Use Search API with date range — avoids paginating hundreds of thousands
    # of PRs on large repos (the /pulls endpoint with 'since' does not filter
    # by created date and causes 504s on large repos).
    since_date = PRE_AI_SINCE[:10]   # 2018-01-01
    until_date = PRE_AI_UNTIL[:10]   # 2022-12-31
    query = f"repo:{repo} is:pr created:{since_date}..{until_date}"

    filtered = []
    page = 1
    while len(filtered) < max_prs:
        data = github_get(
            "https://api.github.com/search/issues",
            token,
            {"q": query, "sort": "created", "order": "asc",
             "per_page": 100, "page": page},
        )
        items = data.get("items", []) if isinstance(data, dict) else []
        if not items:
            break
        filtered.extend(items)
        if len(items) < 100:
            break
        page += 1
        time.sleep(0.5)   # Search API secondary rate limit

    filtered = filtered[:max_prs]
    print(f"  Found {len(filtered)} PRs in pre-2022 window (capped at {max_prs})", flush=True)

    raw_dir.mkdir(parents=True, exist_ok=True)

    with out_path.open("w") as f:
        for i, pr in enumerate(filtered):
            if i % 50 == 0:
                print(f"    Fetching bundle {i+1}/{len(filtered)} ...", flush=True)
            try:
                bundle = fetch_pr_bundle(pr, repo, token)
                f.write(json.dumps(bundle) + "\n")
                time.sleep(0.1)
            except Exception as exc:
                print(f"    Warning: skipping PR #{pr['number']}: {exc}")

    manifest = {
        "repo": repo,
        "slug": slug,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "since": PRE_AI_SINCE,
        "until": PRE_AI_UNTIL,
        "period": "pre_ai",
        "state": "all",
        "max_prs": max_prs,
        "pull_request_count": len(filtered),
        "paths": {
            "pull_requests": str(out_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"  Done: {len(filtered)} pre-2022 PR bundles -> {out_path}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", action="append", default=[])
    parser.add_argument("--repo-set", choices=("locked",), default=None)
    parser.add_argument("--max-prs", type=int, default=DEFAULT_MAX_PRS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repos = list(args.repo)
    if args.repo_set == "locked":
        repos.extend(LOCKED_REPOS)
    if not repos:
        raise SystemExit("provide --repo or --repo-set locked")
    repos = list(dict.fromkeys(repos))

    token = get_token()
    if not token:
        print("Warning: no GITHUB_TOKEN found — API rate limits will be severe.")

    print(f"Collecting pre-AI-era data (2018–2022) for: {repos}")
    print(f"Max PRs per repo: {args.max_prs}\n")

    for repo in repos:
        print(f"\n[{repo}]")
        fetch_pre2022_prs(repo, token, args.max_prs)

    print("\nPre-2022 data collection complete.")
    print("Next: run compute_pr_metrics.py with --period both to compare pre/post-AI metrics.")


if __name__ == "__main__":
    main()
