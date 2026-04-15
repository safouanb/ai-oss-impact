"""
Collect pre-AI-era (2018-2022) PR data for project-level trend analysis (RQ2).

This extends fetch_github_data.py to collect a historical baseline.
The proposal (§4.4) requires tracking metrics across:
  - pre-AI period:  2018-01-01 to 2022-12-31
  - post-AI period: 2023-01-01 to present  (already collected)

Sampling strategy: yearly stratified — ~PRS_PER_YEAR PRs per calendar year
(default 100), sampled from the middle of each year to avoid edge effects.
This prevents the asc-ordering problem where a flat query returns only the
earliest months of 2018.

Output:
  data/raw/<slug>/pull_requests_pre2022.jsonl
  data/raw/<slug>/manifest_pre2022.json

Usage:
    python scripts/fetch_pre2022_data.py --repo-set locked
    python scripts/fetch_pre2022_data.py --repo microsoft/vscode --prs-per-year 100
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

PRE_AI_YEARS = list(range(2018, 2023))   # 2018, 2019, 2020, 2021, 2022
DEFAULT_PRS_PER_YEAR = 100               # 100 × 5 years = 500 total per repo


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


def fetch_year_prs(repo: str, year: int, token: str | None, target: int) -> list[dict]:
    """
    Fetch up to `target` PRs from the middle of `year` using the Search API.
    Queries Jul 1 → Dec 31 first (second half), then Jan 1 → Jun 30 (first half)
    so the sample is spread across the year rather than front-loaded.
    """
    windows = [
        (f"{year}-07-01", f"{year}-12-31"),
        (f"{year}-01-01", f"{year}-06-30"),
    ]
    collected: list[dict] = []
    for since_date, until_date in windows:
        if len(collected) >= target:
            break
        remaining = target - len(collected)
        query = f"repo:{repo} is:pr created:{since_date}..{until_date}"
        page = 1
        while len(collected) < target:
            data = github_get(
                "https://api.github.com/search/issues",
                token,
                {"q": query, "sort": "created", "order": "desc",
                 "per_page": min(100, remaining), "page": page},
            )
            items = data.get("items", []) if isinstance(data, dict) else []
            if not items:
                break
            collected.extend(items)
            if len(items) < 100:
                break
            page += 1
            time.sleep(0.5)   # Search API secondary rate limit
    return collected[:target]


def fetch_pre2022_prs(repo: str, token: str | None, prs_per_year: int) -> None:
    slug = repo_slug(repo)
    raw_dir = RAW_ROOT / slug
    out_path = raw_dir / "pull_requests_pre2022.jsonl"
    manifest_path = raw_dir / "manifest_pre2022.json"

    if out_path.exists():
        print(f"  {repo}: pre-2022 data already exists at {out_path}, skipping.")
        print(f"  Delete {out_path} to re-collect.")
        return

    print(
        f"  Fetching pre-AI PRs for {repo} "
        f"(years={PRE_AI_YEARS[0]}-{PRE_AI_YEARS[-1]}, {prs_per_year}/year) ...",
        flush=True,
    )

    all_prs: list[dict] = []
    year_counts: dict[int, int] = {}

    for year in PRE_AI_YEARS:
        year_prs = fetch_year_prs(repo, year, token, prs_per_year)
        year_counts[year] = len(year_prs)
        all_prs.extend(year_prs)
        print(f"    {year}: {len(year_prs)} PRs collected", flush=True)

    total = len(all_prs)
    print(f"  Total: {total} PRs across {len(PRE_AI_YEARS)} years", flush=True)

    raw_dir.mkdir(parents=True, exist_ok=True)

    with out_path.open("w") as f:
        for i, pr in enumerate(all_prs):
            if i % 50 == 0:
                print(f"    Fetching bundle {i+1}/{total} ...", flush=True)
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
        "since": f"{PRE_AI_YEARS[0]}-01-01T00:00:00Z",
        "until": f"{PRE_AI_YEARS[-1]}-12-31T23:59:59Z",
        "period": "pre_ai",
        "sampling": "yearly_stratified",
        "prs_per_year": prs_per_year,
        "year_counts": year_counts,
        "pull_request_count": total,
        "paths": {
            "pull_requests": str(out_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"  Done: {total} pre-2022 PR bundles -> {out_path}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", action="append", default=[])
    parser.add_argument("--repo-set", choices=("locked",), default=None)
    parser.add_argument(
        "--prs-per-year",
        type=int,
        default=DEFAULT_PRS_PER_YEAR,
        help=f"PRs to collect per calendar year (default {DEFAULT_PRS_PER_YEAR}). "
             f"Total per repo = prs-per-year × {len(PRE_AI_YEARS)} years.",
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

    token = get_token()
    if not token:
        print("Warning: no GITHUB_TOKEN found — API rate limits will be severe.")

    total_target = args.prs_per_year * len(PRE_AI_YEARS)
    print(f"Collecting pre-AI-era data (2018–2022) for: {repos}")
    print(f"Sampling: {args.prs_per_year} PRs/year × {len(PRE_AI_YEARS)} years = {total_target} per repo\n")

    for repo in repos:
        print(f"\n[{repo}]")
        fetch_pre2022_prs(repo, token, args.prs_per_year)

    print("\nPre-2022 data collection complete.")
    print("Next: run compute_pr_metrics.py with --period both to compare pre/post-AI metrics.")


if __name__ == "__main__":
    main()
