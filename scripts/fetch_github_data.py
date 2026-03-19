"""
Fetch PR-first GitHub data for the thesis case studies.

For each repository, this script writes:
  - data/raw/<slug>/repo.json
  - data/raw/<slug>/pull_requests.jsonl
  - data/raw/<slug>/security_advisories.json
  - data/raw/<slug>/manifest.json

Usage:
    python scripts/fetch_github_data.py --repo microsoft/vscode --since 2023-01-01 --max-prs 50
    python scripts/fetch_github_data.py --repo-set locked --since 2023-01-01 --max-prs 25
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException

load_dotenv()

API_ROOT = "https://api.github.com"
RAW_ROOT = Path("data/raw")
LOCKED_REPOS = ("microsoft/vscode", "vercel/next.js")


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def repo_slug(repo: str) -> str:
    return repo.replace("/", "_")


class GitHubClient:
    def __init__(self, token: str | None) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "Connection": "close",
                "User-Agent": "ai-oss-impact-rq1-fetcher",
            }
        )
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def get(self, url: str, params: dict[str, Any] | None = None) -> requests.Response:
        retries = 4
        for attempt in range(1, retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=(20, 120))
                if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
                    reset = int(response.headers.get("X-RateLimit-Reset", "0"))
                    wait_seconds = max(reset - int(time.time()) + 2, 2)
                    print(f"[rate-limit] waiting {wait_seconds}s for {url}", flush=True)
                    time.sleep(wait_seconds)
                    continue
                response.raise_for_status()
                resource = response.headers.get("X-RateLimit-Resource", "")
                if resource == "search":
                    time.sleep(0.25)
                return response
            except RequestException as exc:
                if attempt == retries:
                    raise
                wait_seconds = attempt * 5
                print(f"[retry {attempt}/{retries}] {url}: {exc}; waiting {wait_seconds}s", flush=True)
                time.sleep(wait_seconds)

        raise RuntimeError(f"failed to fetch {url}")

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> Any:
        return self.get(url, params=params).json()

    def paginate(self, url: str, params: dict[str, Any] | None = None) -> list[Any]:
        items: list[Any] = []
        next_url = url
        next_params = params

        while next_url:
            response = self.get(next_url, params=next_params)
            payload = response.json()
            if isinstance(payload, list):
                items.extend(payload)
            else:
                raise RuntimeError(f"expected list payload from {next_url}")

            next_url = response.links.get("next", {}).get("url")
            next_params = None

        return items


def select_repos(explicit_repos: list[str], repo_set: str | None) -> list[str]:
    repos: list[str] = list(explicit_repos)
    if repo_set == "locked":
        repos.extend(LOCKED_REPOS)
    if not repos:
        raise SystemExit("provide at least one --repo or use --repo-set locked")
    return list(dict.fromkeys(repos))


def fetch_pull_summaries(
    client: GitHubClient,
    repo: str,
    state: str,
    since: datetime | None,
    until: datetime | None,
    max_prs: int,
) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    url = f"{API_ROOT}/repos/{repo}/pulls"
    params: dict[str, Any] | None = {
        "state": state,
        "sort": "created",
        "direction": "desc",
        "per_page": 100,
    }

    while url:
        response = client.get(url, params=params)
        pulls = response.json()
        if not isinstance(pulls, list):
            raise RuntimeError(f"expected list payload from {url}")

        stop = False
        for pr in pulls:
            created_at = parse_date(pr.get("created_at"))
            if until and created_at and created_at > until:
                continue
            if since and created_at and created_at < since:
                stop = True
                break

            collected.append(pr)
            if max_prs and len(collected) >= max_prs:
                stop = True
                break

        if stop:
            break

        url = response.links.get("next", {}).get("url")
        params = None

    return collected


def fetch_pr_bundle(client: GitHubClient, repo: str, summary: dict[str, Any]) -> dict[str, Any]:
    number = summary["number"]
    detail_url = f"{API_ROOT}/repos/{repo}/pulls/{number}"
    reviews_url = f"{API_ROOT}/repos/{repo}/pulls/{number}/reviews"
    review_comments_url = f"{API_ROOT}/repos/{repo}/pulls/{number}/comments"
    issue_comments_url = f"{API_ROOT}/repos/{repo}/issues/{number}/comments"
    commits_url = f"{API_ROOT}/repos/{repo}/pulls/{number}/commits"
    files_url = f"{API_ROOT}/repos/{repo}/pulls/{number}/files"

    return {
        "summary": summary,
        "detail": client.get_json(detail_url),
        "reviews": client.paginate(reviews_url, params={"per_page": 100}),
        "review_comments": client.paginate(review_comments_url, params={"per_page": 100}),
        "issue_comments": client.paginate(issue_comments_url, params={"per_page": 100}),
        "commits": client.paginate(commits_url, params={"per_page": 100}),
        "files": client.paginate(files_url, params={"per_page": 100}),
    }


def fetch_security_advisories(client: GitHubClient, repo: str) -> list[dict[str, Any]]:
    return client.paginate(
        f"{API_ROOT}/repos/{repo}/security-advisories",
        params={"state": "published", "per_page": 100},
    )


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row))
            handle.write("\n")


def fetch_repo(
    client: GitHubClient,
    repo: str,
    since: datetime | None,
    until: datetime | None,
    state: str,
    max_prs: int,
) -> dict[str, Any]:
    slug = repo_slug(repo)
    repo_dir = RAW_ROOT / slug
    repo_dir.mkdir(parents=True, exist_ok=True)

    print(f"fetching repository metadata for {repo} ...", flush=True)
    metadata = client.get_json(f"{API_ROOT}/repos/{repo}")
    write_json(repo_dir / "repo.json", metadata)

    print(f"fetching pull request summaries for {repo} ...", flush=True)
    pull_summaries = fetch_pull_summaries(client, repo, state=state, since=since, until=until, max_prs=max_prs)
    print(f"  {len(pull_summaries)} pull requests selected", flush=True)

    bundles: list[dict[str, Any]] = []
    total = len(pull_summaries)
    for idx, summary in enumerate(pull_summaries, start=1):
        number = summary["number"]
        print(f"  [{idx}/{total}] PR #{number}", flush=True)
        bundles.append(fetch_pr_bundle(client, repo, summary))

    print(f"fetching security advisories for {repo} ...", flush=True)
    advisories = fetch_security_advisories(client, repo)
    print(f"  {len(advisories)} advisories", flush=True)

    write_jsonl(repo_dir / "pull_requests.jsonl", bundles)
    write_json(repo_dir / "security_advisories.json", advisories)

    manifest = {
        "repo": repo,
        "slug": slug,
        "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "since": since.isoformat() if since else None,
        "until": until.isoformat() if until else None,
        "state": state,
        "max_prs": max_prs,
        "pull_request_count": len(bundles),
        "security_advisory_count": len(advisories),
        "paths": {
            "repo": str(repo_dir / "repo.json"),
            "pull_requests": str(repo_dir / "pull_requests.jsonl"),
            "security_advisories": str(repo_dir / "security_advisories.json"),
        },
    }
    write_json(repo_dir / "manifest.json", manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", action="append", default=[], help="Repository in owner/name format.")
    parser.add_argument(
        "--repo-set",
        choices=("locked",),
        default=None,
        help="Convenience set of repositories from the working case lock.",
    )
    parser.add_argument("--since", default="2023-01-01", help="Filter PRs created on or after this date.")
    parser.add_argument("--until", default=None, help="Filter PRs created on or before this date.")
    parser.add_argument("--state", default="all", choices=("open", "closed", "all"))
    parser.add_argument(
        "--max-prs",
        type=int,
        default=250,
        help="Maximum number of PRs to fetch per repository. Use 0 for no limit.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repos = select_repos(args.repo, args.repo_set)
    since = parse_date(args.since)
    until = parse_date(args.until)
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required. Put it in .env or export it before running the script.")

    client = GitHubClient(token=token)
    manifests = []
    for repo in repos:
        manifests.append(
            fetch_repo(
                client,
                repo=repo,
                since=since,
                until=until,
                state=args.state,
                max_prs=args.max_prs,
            )
        )

    print("\nfinished fetch run", flush=True)
    for manifest in manifests:
        print(
            f"- {manifest['repo']}: {manifest['pull_request_count']} PRs, "
            f"{manifest['security_advisory_count']} advisories",
            flush=True,
        )


if __name__ == "__main__":
    main()
