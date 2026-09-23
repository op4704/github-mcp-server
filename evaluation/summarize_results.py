"""
summarize_results.py
------------------
Reads evaluation/results.jsonl (produced by run_eval.py) and writes a
clean, human-readable report to evaluation/results.md.

This is the file you'd actually show in an interview or in your
portfolio README.
"""

import json
from collections import Counter
from pathlib import Path

EVAL_DIR = Path(__file__).parent
RESULTS_FILE = EVAL_DIR / "results.jsonl"
REPORT_FILE = EVAL_DIR / "results.md"


def main():
    if not RESULTS_FILE.exists():
        print("No results.jsonl found. Run run_eval.py first.")
        return

    records = [json.loads(line) for line in RESULTS_FILE.read_text().splitlines() if line.strip()]
    total = len(records)

    outcome_counts = Counter(r["outcome"] for r in records)
    correct = outcome_counts.get("correct", 0)
    accuracy = (correct / total * 100) if total else 0

    failures = [r for r in records if r["outcome"] != "correct"]

    lines = []
    lines.append("# MCP Server Evaluation Results\n")
    lines.append(f"**Total questions:** {total}")
    lines.append(f"**Correct tool selections:** {correct}")
    lines.append(f"**Accuracy:** {accuracy:.1f}%\n")

    lines.append("## Breakdown by outcome type\n")
    lines.append("| Outcome | Count | What it means |")
    lines.append("|---|---|---|")
    meaning = {
        "correct": "AI picked the right tool (or correctly called no tool)",
        "wrong_tool": "AI called a tool, but not the one we expected",
        "no_tool_called": "AI should have used a tool but didn't call any",
        "wrong_tool_used": "AI called a tool when it shouldn't have (trick question)",
    }
    for outcome, count in outcome_counts.most_common():
        lines.append(f"| {outcome} | {count} | {meaning.get(outcome, '')} |")

    lines.append("\n## Failures (for improving tool descriptions)\n")
    if not failures:
        lines.append("None! All questions were handled correctly.")
    else:
        lines.append("| # | Question | Expected | Got | Outcome |")
        lines.append("|---|---|---|---|---|")
        for r in failures:
            q_short = r["question"][:50] + ("..." if len(r["question"]) > 50 else "")
            got = ", ".join(r["tools_called"]) if r["tools_called"] else "(none)"
            lines.append(f"| {r['id']} | {q_short} | {r['expected_tool']} | {got} | {r['outcome']} |")

    lines.append("\n## Errors during the run\n")
    errored = [r for r in records if r.get("error")]
    if not errored:
        lines.append("None - every question ran without a CLI/process error.")
    else:
        for r in errored:
            lines.append(f"- Q{r['id']}: {r['error']}")

    report = "\n".join(lines) + "\n"
    REPORT_FILE.write_text(report, encoding="utf-8")

    print(report)
    print(f"\nReport saved to: {REPORT_FILE}")


if __name__ == "__main__":
    main()
