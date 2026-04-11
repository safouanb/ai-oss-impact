"""
CVE commit tracing — Phase 2, RQ3.

For each published security advisory, this script:
  1. Resolves the patched release tag -> fix commit SHA (via GitHub API)
  2. Looks up whether the fix commit appears in your labeled PR dataset
  3. Examines the review trail of that PR (duration, reviewers, security flags)
  4. Attempts to identify the vulnerability-introducing commit by inspecting
     the diff of the fix commit and searching commit history for the file

Output:
  results/tables/cve_trace.csv   — one row per advisory
  results/tables/cve_trace.md    — markdown summary for thesis

Proposal reference: §4.4 (Security dimension, CVE commit tracing)
  "The study traces vulnerability-introducing commits by cross-referencing
   CVE database entries with the project's commit history."

Known fix commits (resolved 2026-04-01 via GitHub API):
  vscode  1.109.1  -> 6534f6ba  (CVE-2026-21523, terminal auto-replies)
  vscode  1.109.1  -> cd11faec  (CVE-2026-21518, MCP workspace trust)
                      NOTE: commit message says "Implemented with Opus,
                      reviewed with Sonnet4.5" — AI-authored fix commit.
  next.js v16.0.7  -> 7492122a  (CVE-2025-55182, React2Shell CVSS 10.0)
  next.js v15.2.3  -> 535e26d3  (CVE-2025-29927, middleware bypass)

Usage:
    python scripts/trace_cve_commits.py --repo-set locked
    python scripts/trace_cve_commits.py --repo vercel/next.js
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from pathlib import Path

import requests

RAW_ROOT = Path("data/raw")
PROCESSED_ROOT = Path("data/processed")
RESULTS_ROOT = Path("results/tables")
LOCKED_REPOS = ("microsoft/vscode", "vercel/next.js")

SECURITY_PATTERN = re.compile(
    r"\b(vulnerabilit|cve|inject|xss|csrf|sqli|rce|auth|sanitiz|escap|exploit"
    r"|bypass|overflow|traversal|deseri|privilege|malici)\w*\b",
    re.I,
)

# Known fix commits resolved via GitHub API (2026-04-01)
# tag -> list of (commit_sha, cve_ids_fixed)
KNOWN_FIX_COMMITS: dict[str, list[tuple[str, list[str]]]] = {
    "microsoft/vscode": [
        ("6534f6ba7604bf324f94cc9a590727f39a4af040",
         ["CVE-2026-21523"],
         "Terminal: Update Auto Replies Configuration"),
        ("cd11faec7b031b928bc5ec37f350d623ffb28713",
         ["CVE-2026-21518"],
         "CVE-2026-21518 fix — Implemented with Opus, reviewed with Sonnet4.5 (AI-authored)"),
    ],
    "vercel/next.js": [
        ("7492122a3bbc6655b64ccba04076c73ab418cdcc",
         ["CVE-2025-55182"],
         "v16.0.7 — React2Shell CVSS 10.0 fix"),
        ("535e26d3c69de49df8bd17618a424cbe65ec897b",
         ["CVE-2025-29927"],
         "v15.2.3 — middleware bypass fix"),
    ],
}


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
    for attempt in range(5):
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 404:
            return {}
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            wait = int(resp.headers.get("Retry-After", 60))
            print(f"  Rate limited — waiting {wait}s ...", flush=True)
            time.sleep(wait)
            continue
        if resp.status_code in (500, 502, 503):
            time.sleep(2 ** attempt)
            continue
        resp.raise_for_status()
    return {}


def load_advisories(repo: str) -> list[dict]:
    path = RAW_ROOT / repo_slug(repo) / "security_advisories.json"
    if not path.exists():
        return []
    return json.loads(path.read_text())


def advisory_package_fields(advisory: dict) -> tuple[list[str], list[str]]:
    ecosystems: list[str] = []
    names: list[str] = []
    for vuln in advisory.get("vulnerabilities", []):
        package = vuln.get("package") or {}
        ecosystem = (package.get("ecosystem") or "").strip()
        name = (package.get("name") or "").strip()
        if ecosystem:
            ecosystems.append(ecosystem)
        if name:
            names.append(name)
    return ecosystems, names


def advisory_preference(repo: str, advisory: dict) -> tuple[int, int, str]:
    ecosystems, names = advisory_package_fields(advisory)
    repo_token = re.sub(r"[^a-z0-9]+", "", repo.split("/")[-1].lower())
    normalized_names = [re.sub(r"[^a-z0-9]+", "", name.lower()) for name in names]

    # Prefer repository-level advisories when the same CVE appears multiple
    # times, then advisories that clearly match the repository package name.
    score = 0
    if not names:
        score += 4
    if any(repo_token and repo_token in name for name in normalized_names):
        score += 3
    if any(ecosystem.lower() in {"npm", "vs code", "vs code ", ""} for ecosystem in ecosystems):
        score += 1

    return (score, len(advisory.get("vulnerabilities", [])), advisory.get("published_at", ""))


def collapse_duplicate_advisories(repo: str, advisories: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for idx, advisory in enumerate(advisories):
        cve_id = advisory.get("cve_id") or ""
        ghsa_id = advisory.get("ghsa_id") or f"unknown-ghsa-{idx}"
        key = cve_id if cve_id else ghsa_id
        grouped.setdefault(key, []).append(advisory)

    collapsed: list[dict] = []
    for _, group in grouped.items():
        ordered = sorted(group, key=lambda a: advisory_preference(repo, a), reverse=True)
        chosen = dict(ordered[0])
        chosen["duplicate_advisory_count"] = len(group)
        chosen["related_ghsa_ids"] = [a.get("ghsa_id", "") for a in group if a.get("ghsa_id")]
        chosen["related_summaries"] = [a.get("summary", "") for a in group if a.get("summary")]
        collapsed.append(chosen)

    return sorted(collapsed, key=lambda a: a.get("published_at", ""), reverse=True)


def load_pr_labels(repo: str) -> dict[int, dict]:
    path = PROCESSED_ROOT / repo_slug(repo) / "pr_labels.csv"
    if not path.exists():
        return {}
    with path.open() as f:
        return {int(r["pr_number"]): r for r in csv.DictReader(f)}


def load_pr_bundles(repo: str) -> dict[str, dict]:
    """Return dict of commit_sha -> PR bundle for quick lookup."""
    path = RAW_ROOT / repo_slug(repo) / "pull_requests.jsonl"
    if not path.exists():
        return {}
    sha_to_bundle: dict[str, dict] = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            bundle = json.loads(line)
            for commit in bundle.get("commits", []):
                sha = commit.get("sha", "")
                if sha:
                    sha_to_bundle[sha] = bundle
    return sha_to_bundle


def resolve_fix_commit_via_api(
    repo: str, tag: str, token: str | None
) -> str | None:
    """Look up a release tag and return its commit SHA."""
    url = f"https://api.github.com/repos/{repo}/git/refs/tags/{tag}"
    data = github_get(url, token)
    if not data:
        return None
    # API may return a list when multiple refs match the prefix
    if isinstance(data, list):
        # Pick the exact match or the first entry
        exact = [r for r in data if r.get("ref") == f"refs/tags/{tag}"]
        data = exact[0] if exact else data[0]
    obj = data.get("object", {})
    sha = obj.get("sha")
    obj_type = obj.get("type")
    if obj_type == "tag":
        # Annotated tag — need to dereference
        tag_data = github_get(obj.get("url", ""), token)
        if isinstance(tag_data, dict):
            sha = (tag_data.get("object") or {}).get("sha")
    return sha


def get_commit_detail(repo: str, sha: str, token: str | None) -> dict:
    url = f"https://api.github.com/repos/{repo}/commits/{sha}"
    return github_get(url, token) or {}


def find_pr_for_commit(
    sha: str, repo: str, token: str | None
) -> dict | None:
    """Search GitHub for PRs that contain this commit."""
    url = f"https://api.github.com/repos/{repo}/commits/{sha}/pulls"
    headers = {
        "Accept": "application/vnd.github.groot-preview+json",
        "Authorization": f"Bearer {token}" if token else "",
    }
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 200 and resp.json():
        return resp.json()[0]
    return None


def security_flag_in_review(bundle: dict) -> bool:
    all_text = " ".join(
        [(r.get("body") or "") for r in bundle.get("reviews", [])]
        + [(c.get("body") or "") for c in bundle.get("review_comments", [])]
        + [(c.get("body") or "") for c in bundle.get("issue_comments", [])]
    )
    return bool(SECURITY_PATTERN.search(all_text))


def trace_repo(repo: str, token: str | None) -> list[dict]:
    print(f"\n[{repo}] Tracing CVE fix commits ...", flush=True)

    advisories = collapse_duplicate_advisories(repo, load_advisories(repo))
    label_map = load_pr_labels(repo)
    sha_to_bundle = load_pr_bundles(repo)
    known_fixes = KNOWN_FIX_COMMITS.get(repo, [])

    results = []

    for advisory in advisories:
        cve_id = advisory.get("cve_id") or "no-cve"
        ghsa_id = advisory.get("ghsa_id", "")
        severity = advisory.get("severity", "")
        published_at = (advisory.get("published_at") or "")[:10]
        summary = advisory.get("summary", "")
        vulns = advisory.get("vulnerabilities", [])
        patched = [v.get("patched_versions", "") for v in vulns]
        cwe_ids = advisory.get("cwe_ids", [])
        package_ecosystems, package_names = advisory_package_fields(advisory)
        duplicate_advisory_count = int(advisory.get("duplicate_advisory_count", 1) or 1)
        related_ghsa_ids = advisory.get("related_ghsa_ids") or ([ghsa_id] if ghsa_id else [])

        print(f"  {cve_id} ({severity}) patched={patched}", flush=True)

        # Try known fix commits first (pre-resolved)
        fix_sha = None
        fix_note = ""
        for sha, cves, note in known_fixes:
            if cve_id in cves:
                fix_sha = sha
                fix_note = note
                break

        # If not pre-resolved, try to look up via API using first patched version
        if not fix_sha and patched and patched[0]:
            tag = patched[0].strip().lstrip("=<>^~")
            # Normalise: vscode uses plain "1.109.1", next.js uses "v15.2.3"
            if not tag.startswith("v") and repo == "vercel/next.js":
                tag = "v" + tag
            fix_sha = resolve_fix_commit_via_api(repo, tag, token)
            fix_note = f"resolved from tag {tag}"
            time.sleep(0.3)

        # Look up PR for fix commit
        fix_pr_num = None
        fix_pr_label = "unresolved"
        fix_pr_confidence = "none"
        fix_pr_aidev = False
        fix_review_duration_hrs = None
        fix_reviewer_count = None
        fix_security_flagged = False
        fix_review_count = None
        fix_commit_msg = ""
        fix_commit_author = ""
        ai_in_fix_commit_msg = False

        if fix_sha:
            # Check local bundle first (fast)
            bundle = sha_to_bundle.get(fix_sha)

            # If not in local data, query API
            if not bundle:
                pr_data = find_pr_for_commit(fix_sha, repo, token)
                if pr_data:
                    fix_pr_num = pr_data.get("number")
                time.sleep(0.2)
            else:
                detail = bundle.get("detail", {})
                fix_pr_num = detail.get("number")

            # Get label from pr_labels.csv
            if fix_pr_num and fix_pr_num in label_map:
                row = label_map[fix_pr_num]
                fix_pr_label = row.get("label", "unresolved")
                fix_pr_confidence = row.get("confidence_tier", "none")
                evidence = json.loads(row.get("evidence_json") or "[]")
                fix_pr_aidev = any(
                    s.get("source") == "aidev_dataset" for s in evidence
                )
                fix_review_count = int(row.get("review_count", 0) or 0)

            # Review trail from bundle
            if bundle:
                reviews = bundle.get("reviews", [])
                detail = bundle.get("detail", {})
                created_at = detail.get("created_at")
                merged_at = detail.get("merged_at") or detail.get("updated_at")
                if created_at and merged_at:
                    from datetime import datetime
                    s = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    e = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
                    fix_review_duration_hrs = round(
                        (e - s).total_seconds() / 3600, 2
                    )
                bot_suffixes = ("[bot]", "-bot", "copilot", "dependabot")
                author_login = (detail.get("user") or {}).get("login", "").lower()
                reviewers = {
                    (r.get("user") or {}).get("login", "").lower()
                    for r in reviews
                    if (r.get("user") or {}).get("login", "").lower() not in ("", author_login)
                    and not any(
                        (r.get("user") or {}).get("login", "").lower().endswith(s)
                        for s in bot_suffixes
                    )
                }
                fix_reviewer_count = len(reviewers)
                fix_security_flagged = security_flag_in_review(bundle)

            # Get fix commit message to check for AI authorship
            commit_detail = get_commit_detail(repo, fix_sha, token)
            fix_commit_msg = (commit_detail.get("commit") or {}).get("message", "")[:300]
            fix_commit_author = (
                (commit_detail.get("author") or {}).get("login", "")
                or (commit_detail.get("commit") or {}).get("author", {}).get("name", "")
            )
            ai_keywords = re.compile(
                r"\b(copilot|cursor|claude|chatgpt|codex|devin|gpt|gemini|sonnet|opus)\b",
                re.I,
            )
            ai_in_fix_commit_msg = bool(ai_keywords.search(fix_commit_msg))
            time.sleep(0.2)

        row = {
            "repo": repo,
            "cve_id": cve_id,
            "ghsa_id": ghsa_id,
            "related_ghsa_ids": "; ".join(related_ghsa_ids),
            "duplicate_advisory_count": duplicate_advisory_count,
            "severity": severity,
            "published_at": published_at,
            "summary": summary[:120],
            "package_ecosystems": "; ".join(sorted(set(package_ecosystems))),
            "package_names": "; ".join(sorted(set(package_names))),
            "patched_versions": "; ".join(patched),
            "cwe_ids": "; ".join(cwe_ids),
            "fix_commit_sha": fix_sha or "",
            "fix_commit_note": fix_note,
            "fix_commit_msg": fix_commit_msg.replace("\n", " ")[:200],
            "fix_commit_author": fix_commit_author,
            "ai_in_fix_commit_msg": int(ai_in_fix_commit_msg),
            "fix_pr_number": fix_pr_num or "",
            "fix_pr_label": fix_pr_label,
            "fix_pr_confidence": fix_pr_confidence,
            "fix_pr_aidev_sourced": int(fix_pr_aidev),
            "fix_review_count": fix_review_count or "",
            "fix_reviewer_count": fix_reviewer_count or "",
            "fix_review_duration_hrs": fix_review_duration_hrs or "",
            "fix_security_flagged_in_review": int(fix_security_flagged),
        }
        results.append(row)
        print(
            f"    -> fix_sha={fix_sha[:8] if fix_sha else 'unknown'} "
            f"pr={fix_pr_num} label={fix_pr_label} "
            f"ai_in_msg={ai_in_fix_commit_msg}",
            flush=True,
        )

    return results


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CVE Commit Trace Results",
        "",
        "Generated by `scripts/trace_cve_commits.py`",
        "Methodology: §4.4 of thesis proposal — security dimension",
        "Duplicate GHSA advisories sharing the same CVE within one repository are collapsed to one row per repo/CVE.",
        "",
        "| Repo | CVE | Severity | Published | Fix SHA | Fix PR | AI Label | AI in Commit Msg | Reviewer Count | Review Duration (hrs) |",
        "|------|-----|----------|-----------|---------|--------|----------|-----------------|---------------|----------------------|",
    ]
    for r in rows:
        sha_short = r["fix_commit_sha"][:8] if r["fix_commit_sha"] else "—"
        lines.append(
            f"| {r['repo']} | {r['cve_id']} | {r['severity']} | {r['published_at']} "
            f"| `{sha_short}` | {r['fix_pr_number'] or '—'} | {r['fix_pr_label']} "
            f"| {'yes' if r['ai_in_fix_commit_msg'] else 'no'} "
            f"| {r['fix_reviewer_count'] or '—'} | {r['fix_review_duration_hrs'] or '—'} |"
        )
    lines += [
        "",
        "## Key findings (auto-generated)",
        "",
    ]

    ai_fix_commits = [r for r in rows if r["ai_in_fix_commit_msg"]]
    if ai_fix_commits:
        lines.append(f"- **{len(ai_fix_commits)} fix commit(s) contain AI tool references** in commit message:")
        for r in ai_fix_commits:
            lines.append(f"  - {r['cve_id']} ({r['repo']}): `{r['fix_commit_msg'][:100]}`")
        lines.append("")

    unresolved = [r for r in rows if not r["fix_commit_sha"]]
    if unresolved:
        lines.append(f"- **{len(unresolved)} CVEs could not be traced** to a fix commit (version range too broad or tag not found)")
        lines.append("")

    path.write_text("\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", action="append", default=[])
    parser.add_argument("--repo-set", choices=("locked",), default=None)
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
        print("Warning: no GITHUB_TOKEN — API calls will be rate-limited")

    all_rows: list[dict] = []
    for repo in repos:
        all_rows.extend(trace_repo(repo, token))

    csv_path = RESULTS_ROOT / "cve_trace.csv"
    md_path = RESULTS_ROOT / "cve_trace.md"

    write_csv(csv_path, all_rows)
    write_markdown(md_path, all_rows)

    print(f"\nTracing complete.")
    print(f"  CSV  -> {csv_path}")
    print(f"  MD   -> {md_path}")

    traced = sum(1 for r in all_rows if r["fix_commit_sha"])
    ai_fix = sum(1 for r in all_rows if r["ai_in_fix_commit_msg"])
    print(f"\nSummary: {len(all_rows)} advisories | {traced} fix commits traced | {ai_fix} with AI in commit message")


if __name__ == "__main__":
    main()
