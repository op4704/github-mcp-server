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

from github_mcp_server.github_client import get_open_issues, get_repo_info

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
@mcp.tool()
def list_open_issues(owner: str, repo: str) -> list[dict]:
    """
    List all currently OPEN issues in a GitHub repository.

    Use this when the user asks things like:
    - "what issues are open in my repo?"
    - "show me bugs in X repo"
    - "how many open issues does Y have?"

    Args:
        owner: the GitHub username or organization that owns the repo
               (e.g. "op4704")
        repo: the repository name (e.g. "rag-eval-harness")

    Returns:
        A list of issues, each with: number, title, url, created_at.
        Returns an empty list if there are no open issues.
    """
    return get_open_issues(owner, repo)


@mcp.tool()
def get_repository_info(owner: str, repo: str) -> dict:
    """
    Get basic stats and info about a GitHub repository.

    Use this when the user asks things like:
    - "tell me about this repo"
    - "how many stars does X have?"
    - "what's the description of Y repo?"

    Args:
        owner: the GitHub username or organization that owns the repo
        repo: the repository name

    Returns:
        A dict with: name, description, stars, forks, open_issues, url.
    """
    return get_repo_info(owner, repo)


def main() -> None:
    """
    Starts the MCP server so it can listen for requests.
    This is what runs when someone does: uv run github-mcp-server
    """
    mcp.run()


if __name__ == "__main__":
    main()
