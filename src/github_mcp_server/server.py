"""
server.py
------------------
PHASE 2 of the MCP server plan.

This is the MAIN file. It turns our plain Python functions
(from github_client.py) into MCP "tools" that an AI can call.

Simple words: this file is the "waiter" - it takes the functions we
already proved work in Phase 1, and puts a menu in front of the AI so
it knows what it's allowed to ask for.
"""

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from github_mcp_server.github_client import (
    add_comment_to_issue,
    create_label,
    get_open_issues,
    get_repo_info,
    search_issues,
)

# Step 1: create the server itself. The "name" is what shows up when
# an AI (or MCP Inspector) connects to it.
mcp = MCPServer(
    name="github-mcp-server",
    instructions=(
        "Tools for reading information from GitHub repositories. "
        "Use these when the user asks about issues, repo stats, "
        "or anything about a specific GitHub repository."
    ),
)


# Step 2: register our FIRST tool.
# The @mcp.tool() decorator is what turns a normal Python function
# into something the AI can discover and call.
#
# IMPORTANT: the docstring below is NOT just for humans - the AI
# reads this exact text to decide whether this is the right tool to
# use. Clear, specific descriptions = the AI picks correctly.
@mcp.tool(
    annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False)
)
def list_open_issues(owner: str, repo: str) -> list[dict]:
    """
    List all currently OPEN issues in a GitHub repository.

    Use this when the user asks things like:
    - "what issues are open in my repo?"
    - "show me bugs in X repo"
    - "how many open issues does Y have?"

    NOTE: this returns the actual LIST of issues. If the user just
    wants a quick COUNT, get_repository_info also has an open_issues
    number and is cheaper to call for that specific question.

    Args:
        owner: the GitHub username or organization that owns the repo
               (e.g. "op4704")
        repo: the repository name (e.g. "rag-eval-harness")

    Returns:
        A list of issues, each with: number, title, url, created_at.
        Returns an empty list if there are no open issues.
    """
    return get_open_issues(owner, repo)


@mcp.tool(
    annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False)
)
def get_repository_info(owner: str, repo: str) -> dict:
    """
    Get basic stats and info about a GitHub repository.

    Use this when the user asks things like:
    - "tell me about this repo"
    - "how many stars does X have?"
    - "what's the description of Y repo?"

    NOTE: this returns an `open_issues` COUNT only (a single number).
    If the user wants to see the actual list of open issues (titles,
    numbers, links), use list_open_issues instead - not this tool.

    Args:
        owner: the GitHub username or organization that owns the repo
        repo: the repository name

    Returns:
        A dict with: name, description, stars, forks, open_issues, url.
    """
    return get_repo_info(owner, repo)


@mcp.tool(
    annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False)
)
def search_repository_issues(owner: str, repo: str, keyword: str) -> list[dict]:
    """
    Search for issues (open AND closed) in a repo that mention a
    keyword in their title or body.

    Use this when the user asks things like:
    - "find issues about login"
    - "search for bugs mentioning payment"
    - "is there an issue about X?"

    Args:
        owner: the GitHub username or organization that owns the repo
        repo: the repository name
        keyword: the word or phrase to search for

    Returns:
        A list of matching issues with: number, title, state, url.
    """
    return search_issues(owner, repo, keyword)


# ------------------------------------------------------------------
# WRITE TOOLS BELOW - these change real data on GitHub.
# destructive_hint=True tells the AI client (and the user) that this
# tool should NOT run silently - it should ask "are you sure?" first.
# read_only_hint=False marks it as not a read-only/safe action.
# ------------------------------------------------------------------

@mcp.tool(
    annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True)
)
def create_repository_label(
    owner: str, repo: str, name: str, color: str = "ededed",
    description: str = ""
) -> dict:
    """
    Create a NEW label in a GitHub repository.

    ** THIS CHANGES REAL DATA ON GITHUB. Always confirm with the user
    before calling this tool. **

    Use this when the user explicitly asks to add/create a label,
    e.g. "create a 'bug' label" or "add a label called 'urgent'".

    Args:
        owner: the GitHub username or organization that owns the repo
        repo: the repository name
        name: the label's name, e.g. "bug", "needs-review"
        color: 6-character hex code WITHOUT the '#', e.g. "ff0000"
        description: optional short description shown on the label

    Returns:
        The created label's name, color, and url.
    """
    return create_label(owner, repo, name, color, description)


@mcp.tool(
    annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True)
)
def comment_on_issue(
    owner: str, repo: str, issue_number: int, comment_body: str
) -> dict:
    """
    Post a NEW comment on an existing GitHub issue.

    ** THIS CHANGES REAL DATA ON GITHUB. Always confirm with the user
    before calling this tool. **

    Use this when the user explicitly asks to comment/reply on an
    issue, e.g. "comment on issue #5 saying it's fixed".

    Args:
        owner: the GitHub username or organization that owns the repo
        repo: the repository name
        issue_number: the issue number to comment on
        comment_body: the text of the comment to post

    Returns:
        The created comment's id, url, and body text.
    """
    return add_comment_to_issue(owner, repo, issue_number, comment_body)


def main() -> None:
    """
    Starts the MCP server so it can listen for requests.
    This is what runs when someone does: uv run github-mcp-server
    """
    mcp.run()


if __name__ == "__main__":
    main()
