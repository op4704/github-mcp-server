"""
test_github_client.py
------------------
PHASE 5 of the MCP server plan.

These tests check that our GitHub functions work correctly WITHOUT
actually calling the real GitHub API every time.

Why we "mock" (fake) the API instead of calling it for real:
1. Speed - fake calls are instant, real network calls are slow.
2. Reliability - tests won't randomly fail because of internet issues
   or GitHub being down.
3. Safety - we can test "what if GitHub returns an error" without
   needing to actually break something on GitHub.

How mocking works here (simple words):
We replace httpx.get / httpx.post with a fake version that returns
exactly the JSON we tell it to, instead of really going to the
internet. Then we check our function processes that fake data
correctly.
"""

import pytest

from github_mcp_server.github_client import (
    add_comment_to_issue,
    create_label,
    get_open_issues,
    get_repo_info,
    search_issues,
)


class FakeResponse:
    """
    A pretend version of an httpx response.
    Just holds JSON data and can pretend nothing went wrong.
    """

    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        # In real httpx, this raises an error if status_code is 4xx/5xx.
        # For our fake tests, we just do nothing (pretend it succeeded).
        if self.status_code >= 400:
            raise Exception(f"HTTP error {self.status_code}")


def test_get_open_issues_returns_simplified_list(mocker):
    """
    Checks that get_open_issues() correctly turns GitHub's raw JSON
    into our simplified list of {number, title, url, created_at}.
    """
    fake_github_response = [
        {
            "number": 1,
            "title": "Login button broken",
            "html_url": "https://github.com/test/test/issues/1",
            "created_at": "2026-01-01T00:00:00Z",
        },
        {
            # This one is actually a Pull Request, not a real issue -
            # GitHub mixes these together, so we must filter it out.
            "number": 2,
            "title": "Fix login bug",
            "html_url": "https://github.com/test/test/pull/2",
            "created_at": "2026-01-02T00:00:00Z",
            "pull_request": {"url": "..."},
        },
    ]

    mocker.patch(
        "github_mcp_server.github_client.httpx.get",
        return_value=FakeResponse(fake_github_response),
    )

    result = get_open_issues("test-owner", "test-repo")

    # We should only get 1 result - the PR should be filtered out
    assert len(result) == 1
    assert result[0]["number"] == 1
    assert result[0]["title"] == "Login button broken"


def test_get_open_issues_returns_empty_list_when_no_issues(mocker):
    """
    Checks that an empty repo (no open issues) doesn't crash and
    just returns an empty list.
    """
    mocker.patch(
        "github_mcp_server.github_client.httpx.get",
        return_value=FakeResponse([]),
    )

    result = get_open_issues("test-owner", "test-repo")

    assert result == []


def test_get_repo_info_returns_expected_fields(mocker):
    """
    Checks that get_repo_info() correctly extracts the fields we care
    about from GitHub's (much larger) raw repo response.
    """
    fake_github_response = {
        "full_name": "test-owner/test-repo",
        "description": "A test repository",
        "stargazers_count": 42,
        "forks_count": 7,
        "open_issues_count": 3,
        "html_url": "https://github.com/test-owner/test-repo",
    }

    mocker.patch(
        "github_mcp_server.github_client.httpx.get",
        return_value=FakeResponse(fake_github_response),
    )

    result = get_repo_info("test-owner", "test-repo")

    assert result["name"] == "test-owner/test-repo"
    assert result["stars"] == 42
    assert result["forks"] == 7
    assert result["open_issues"] == 3


def test_search_issues_returns_matching_results(mocker):
    """
    Checks that search_issues() correctly simplifies GitHub's search
    API response (which wraps results inside an "items" key).
    """
    fake_github_response = {
        "items": [
            {
                "number": 5,
                "title": "Payment bug on checkout",
                "state": "open",
                "html_url": "https://github.com/test/test/issues/5",
            }
        ]
    }

    mocker.patch(
        "github_mcp_server.github_client.httpx.get",
        return_value=FakeResponse(fake_github_response),
    )

    result = search_issues("test-owner", "test-repo", "payment")

    assert len(result) == 1
    assert result[0]["number"] == 5
    assert result[0]["state"] == "open"


def test_create_label_sends_correct_data(mocker):
    """
    Checks that create_label() (a WRITE action) builds the right
    request and correctly reads back what GitHub confirms was created.
    """
    fake_github_response = {
        "name": "bug",
        "color": "ff0000",
        "url": "https://api.github.com/repos/test-owner/test-repo/labels/bug",
    }

    mock_post = mocker.patch(
        "github_mcp_server.github_client.httpx.post",
        return_value=FakeResponse(fake_github_response),
    )

    result = create_label("test-owner", "test-repo", "bug", color="ff0000")

    assert result["name"] == "bug"
    assert result["color"] == "ff0000"

    # Also check we actually SENT the right data to GitHub,
    # not just that we handled the response correctly.
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["json"]["name"] == "bug"
    assert call_kwargs["json"]["color"] == "ff0000"


def test_add_comment_to_issue_sends_correct_data(mocker):
    """
    Checks that add_comment_to_issue() (a WRITE action) sends the
    right comment text and reads back GitHub's confirmation.
    """
    fake_github_response = {
        "id": 999,
        "html_url": "https://github.com/test/test/issues/5#comment-999",
        "body": "This looks fixed now!",
    }

    mock_post = mocker.patch(
        "github_mcp_server.github_client.httpx.post",
        return_value=FakeResponse(fake_github_response),
    )

    result = add_comment_to_issue(
        "test-owner", "test-repo", 5, "This looks fixed now!"
    )

    assert result["id"] == 999
    assert result["body"] == "This looks fixed now!"

    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["json"]["body"] == "This looks fixed now!"


def test_get_open_issues_raises_on_http_error(mocker):
    """
    Checks that when GitHub returns an error (e.g. 404 repo not
    found), our function doesn't silently swallow it - it should
    raise an error so the caller knows something went wrong.
    """
    mocker.patch(
        "github_mcp_server.github_client.httpx.get",
        return_value=FakeResponse({"message": "Not Found"}, status_code=404),
    )

    with pytest.raises(Exception):
        get_open_issues("nonexistent-owner", "nonexistent-repo")
