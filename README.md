# github-mcp-server

An MCP (Model Context Protocol) server that lets an AI assistant securely
read (and, with confirmation, write to) GitHub repositories - listing
issues, checking repo stats, searching issues, creating labels, and
posting comments.

Built as a portfolio project to demonstrate AI tool infrastructure design,
not just prompt engineering: designing safe tools, writing descriptions an
AI can reliably act on, and *measuring* that reliability with real data
instead of just demoing it once and hoping.

## What it does

Give an AI assistant (Claude, or any MCP-compatible client) these 5 tools:

| Tool | Type | What it does |
|---|---|---|
| `list_open_issues` | Read-only | Lists all open issues in a repo |
| `get_repository_info` | Read-only | Repo stats: stars, forks, description, issue count |
| `search_repository_issues` | Read-only | Searches issues (open + closed) by keyword |
| `create_repository_label` | Write (confirm first) | Creates a new label |
| `comment_on_issue` | Write (confirm first) | Posts a comment on an issue |

Write tools are explicitly annotated (`destructive_hint=True`) so any AI
client knows to ask the user before running them - they don't fire
silently.

## Why this project (not just "another GitHub wrapper")

Most portfolio MCP demos stop at "look, it works." This one goes one step
further: a **50-question evaluation harness** (see `evaluation/`) that
sends real questions to a real AI (Claude Code CLI) connected to this
server, and measures - with actual numbers - how often it picks the
correct tool.

**Result: 92% raw accuracy on the first run.** After investigating every
failure individually (not just rewriting descriptions blindly), the real
picture was:
- 1 genuine tool-description ambiguity (fixed - see `evaluation/results.md`)
- 2 cases where the AI correctly asked for confirmation before a
  destructive action, which the single-turn eval script scored as a
  "failure" but is actually the safety design working as intended
- 1 case of model non-determinism on a cheap/small model, confirmed by
  re-running the exact same question standalone

Full investigation notes: [`evaluation/results.md`](evaluation/results.md)

## Tech stack

Python 3.11+ - `mcp` SDK v2 - `httpx` (raw HTTP calls to GitHub's REST API,
not a wrapper library, so the request/response shape is fully visible) -
`uv` for dependency management - `pytest` + `pytest-mock` for tests -
Claude Code CLI for the evaluation harness.

See [`requirment.txt`](requirment.txt) for the full breakdown.

## How it works

```
AI assistant (Claude/etc)
        |
        | "what issues are open in X repo?"
        v
  MCP Server (this project)
        |
        | httpx GET request + auth token
        v
   GitHub REST API
        |
        v
  Real data flows back through the same chain
```

Full data-flow and folder structure: [`structur.txt`](structur.txt)
Plain-English explanation with a real-world example: [`explain.txt`](explain.txt)

## Running it

```bash
# Install dependencies
uv sync

# Add your GitHub token
cp .env.example .env
# edit .env and paste your token (from github.com/settings/tokens)

# Run the tests
uv run pytest -v

# Try it manually in MCP Inspector (browser UI)
npx @modelcontextprotocol/inspector uv run github-mcp-server

# Or register it with an MCP-compatible AI client, e.g. Hermes:
hermes mcp add github-mcp-server --command uv --args run --directory "<path-to-this-folder>" github-mcp-server
```

## Running the evaluation yourself

```bash
cd evaluation
uv run python run_eval.py          # asks all 50 questions, saves results.jsonl
uv run python summarize_results.py # generates results.md report
```

The eval script is resumable - if it's interrupted partway, re-running it
skips questions already answered.

## Project structure

```
src/github_mcp_server/
  github_client.py   - plain Python functions that call GitHub's REST API
  server.py           - wraps those functions as MCP tools
tests/
  test_github_client.py - 7 pytest tests, mocked HTTP (no real network calls)
evaluation/
  questions.json       - 50 test questions (40 real + 10 trick questions)
  run_eval.py           - sends each question to Claude, records tool choice
  summarize_results.py  - generates the accuracy report
  results.md             - the actual report, with full failure analysis
```

## What I'd build next

- Re-run the evaluation on a stronger model to separate genuine tool-design
  issues from small-model non-determinism
- Add a multi-turn eval mode so destructive-action confirmations can be
  properly answered "yes" and tested end-to-end
- A 6th "smart" tool that requires real judgment (e.g. summarize all open
  issues by priority) rather than a direct API wrapper
