"""
github_client.py
------------------
PHASE 1 of the MCP server plan.

Goal: prove we can talk to GitHub's real API using plain Python,
BEFORE we add any MCP/AI complexity on top.

How it works (simple words):
1. We load our secret GitHub token from the .env file.
2. We use httpx to send a request to GitHub's API.
3. GitHub checks our token and sends back real data (JSON).
4. We turn that JSON into something readable.
"""

import os
import httpx
from dotenv import load_dotenv

# Step 1: load the .env file so we can read GITHUB_TOKEN
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_BASE = "https://api.github.com"


def _headers() -> dict:
    """
    Every request to GitHub needs these headers:
    - Authorization: proves who we are (uses our token)
    - Accept: tells GitHub we want the standard JSON format
    """
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_open_issues(owner: str, repo: str) -> list[dict]:
    """
    Fetches the list of OPEN issues for a given repo.

    Example: get_open_issues("op4704", "rag-eval-harness")

    Returns a list of simplified issue dicts:
    [{ "number": 1, "title": "...", "url": "..." }, ...]
    """
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues"
    params = {"state": "open"}

    response = httpx.get(url, headers=_headers(), params=params)
    response.raise_for_status()  # crash loudly if something's wrong

    raw_issues = response.json()

    # GitHub's "issues" endpoint also returns pull requests mixed in.
    # We filter those out so we only get REAL issues.
    real_issues = [issue for issue in raw_issues if "pull_request" not in issue]

    # Simplify the data - we only keep what's actually useful
    simplified = [
        {
            "number": issue["number"],
            "title": issue["title"],
            "url": issue["html_url"],
            "created_at": issue["created_at"],
        }
        for issue in real_issues
    ]

    return simplified


def get_repo_info(owner: str, repo: str) -> dict:
    """
    Fetches basic info about a repo: stars, forks, description.

    Example: get_repo_info("op4704", "rag-eval-harness")
    """
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"

    response = httpx.get(url, headers=_headers())
    response.raise_for_status()

    data = response.json()

    return {
        "name": data["full_name"],
        "description": data["description"],
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "open_issues": data["open_issues_count"],
        "url": data["html_url"],
    }


if __name__ == "__main__":
    # Quick manual test - run this file directly to check it works:
    #   uv run python src/github_mcp_server/github_client.py

    if not GITHUB_TOKEN:
        print("ERROR: GITHUB_TOKEN not found. Check your .env file.")
    else:
        print("Token loaded. Testing against a real repo...\n")

        owner, repo = "op4704", "rag-eval-harness"

        print(f"--- Repo Info: {owner}/{repo} ---")
        info = get_repo_info(owner, repo)
        for key, value in info.items():
            print(f"{key}: {value}")

        print(f"\n--- Open Issues: {owner}/{repo} ---")
        issues = get_open_issues(owner, repo)
        if not issues:
            print("No open issues found (that's fine - just means repo is clean).")
        else:
            for issue in issues:
                print(f"#{issue['number']}: {issue['title']}")
