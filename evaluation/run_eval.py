"""
run_eval.py
------------------
PHASE 6 of the MCP server plan - THE EVALUATION.

Goal: send 50 real questions to a real AI (Claude Code CLI) connected
to our MCP server, record which tool it picked for each one, and
measure how accurate our tool descriptions actually are.

Why this matters (simple words):
Anyone can build tools. This step PROVES the tools work well by
measuring it with real numbers - not just "it seemed to work when I
tried it once."

How it works:
1. Load our 50 questions from questions.json
2. For each question, call the "claude" CLI in headless mode (-p),
   pointed ONLY at our MCP server (--strict-mcp-config), asking it
   to answer the question.
3. Claude will look at our 5 tools and decide (on its own) which one
   to use - exactly like a real user's AI assistant would.
4. We read back which tool it actually called (from the stream-json
   output) and compare it to what we EXPECTED.
5. We save every result to results.jsonl AS WE GO (not just at the
   end) - so if something crashes halfway, we don't lose progress.
6. At the end, we calculate accuracy and write a summary report.
"""

import json
import subprocess
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).parent
QUESTIONS_FILE = EVAL_DIR / "questions.json"
RESULTS_FILE = EVAL_DIR / "results.jsonl"
MCP_CONFIG_FILE = EVAL_DIR / "mcp_config.json"

# All 5 real tool names our server exposes, in the format Claude Code
# uses to refer to MCP tools: mcp__<server-name>__<tool-name>
OUR_TOOLS = [
    "mcp__github-mcp-server__list_open_issues",
    "mcp__github-mcp-server__get_repository_info",
    "mcp__github-mcp-server__search_repository_issues",
    "mcp__github-mcp-server__create_repository_label",
    "mcp__github-mcp-server__comment_on_issue",
]

ALLOWED_TOOLS_ARG = ",".join(OUR_TOOLS)


def strip_prefix(tool_name: str) -> str:
    """
    Claude reports tool calls as 'mcp__github-mcp-server__list_open_issues'.
    We just want the short name: 'list_open_issues'.
    """
    prefix = "mcp__github-mcp-server__"
    if tool_name.startswith(prefix):
        return tool_name[len(prefix):]
    return tool_name


def ask_claude(question: str) -> dict:
    """
    Sends one question to Claude Code CLI in headless mode, connected
    ONLY to our MCP server, and returns which of OUR tools it called
    (if any), plus its final text answer.
    """
    cmd = [
        "claude",
        "-p", question,
        "--mcp-config", str(MCP_CONFIG_FILE),
        "--strict-mcp-config",
        "--output-format", "stream-json",
        "--verbose",
        "--model", "haiku",  # cheaper model - fine for tool-picking accuracy testing
        "--allowedTools", ALLOWED_TOOLS_ARG,
    ]

    result = subprocess.run(
        cmd,
        cwd=str(EVAL_DIR),
        capture_output=True,
        text=True,
        timeout=180,
    )

    tools_called = []
    final_text = ""
    error = None

    if result.returncode != 0:
        error = f"CLI exited with code {result.returncode}: {result.stderr[:300]}"

    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    name = block.get("name", "")
                    # Only count REAL tool calls from our server,
                    # ignore internal helper calls like "ToolSearch"
                    if name in OUR_TOOLS:
                        tools_called.append(strip_prefix(name))

        if event.get("type") == "result":
            final_text = event.get("result", "")

    return {
        "tools_called": tools_called,
        "final_text": final_text,
        "error": error,
    }


def grade_result(expected_tool: str | None, tools_called: list[str]) -> str:
    """
    Decides pass/fail for one question.

    - If expected_tool is None: the AI should NOT have called any of
      our tools (it was a general knowledge question). PASS if it
      called zero of our tools.
    - If expected_tool is set: PASS if that tool is somewhere in the
      list of tools it called (it's fine if it also double-checked
      with another tool, as long as the right one was used).
    """
    if expected_tool is None:
        return "correct" if len(tools_called) == 0 else "wrong_tool_used"

    if expected_tool in tools_called:
        return "correct"
    if len(tools_called) == 0:
        return "no_tool_called"
    return "wrong_tool"


def main():
    questions = json.loads(QUESTIONS_FILE.read_text())

    # Resume support: if results.jsonl already has some entries,
    # skip questions we've already run (in case this got interrupted).
    already_done = set()
    if RESULTS_FILE.exists():
        for line in RESULTS_FILE.read_text().splitlines():
            if line.strip():
                already_done.add(json.loads(line)["id"])

    total = len(questions)
    for q in questions:
        if q["id"] in already_done:
            print(f"[{q['id']}/{total}] SKIP (already done)")
            continue

        print(f"[{q['id']}/{total}] Asking: {q['question'][:60]}...")

        try:
            response = ask_claude(q["question"])
        except subprocess.TimeoutExpired:
            response = {"tools_called": [], "final_text": "", "error": "TIMEOUT"}

        outcome = grade_result(q["expected_tool"], response["tools_called"])

        record = {
            "id": q["id"],
            "question": q["question"],
            "expected_tool": q["expected_tool"],
            "tools_called": response["tools_called"],
            "outcome": outcome,
            "error": response["error"],
        }

        # Append immediately - progress is saved even if we crash later
        with open(RESULTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        print(f"    -> expected={q['expected_tool']}  got={response['tools_called']}  outcome={outcome}")

    print("\nDone. Run summarize_results.py to generate the report.")


if __name__ == "__main__":
    main()
