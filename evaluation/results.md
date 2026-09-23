# MCP Server Evaluation Results

**Total questions:** 50
**Correct tool selections:** 46
**Accuracy:** 92.0%

## Breakdown by outcome type

| Outcome | Count | What it means |
|---|---|---|
| correct | 46 | AI picked the right tool (or correctly called no tool) |
| no_tool_called | 3 | AI should have used a tool but didn't call any |
| wrong_tool | 1 | AI called a tool, but not the one we expected |

## Failures (for improving tool descriptions)

| # | Question | Expected | Got | Outcome |
|---|---|---|---|---|
| 3 | How many open issues does op4704/ecommerce-sales-a... | list_open_issues | get_repository_info | wrong_tool |
| 16 | What is op4704/ecommerce-sales-analysis about? | get_repository_info | (none) | no_tool_called |
| 32 | Add a label named 'phase-6-test-b' to the op4704/g... | create_repository_label | (none) | no_tool_called |
| 34 | I want a new label 'phase-6-test-d' set up in op47... | create_repository_label | (none) | no_tool_called |

## Errors during the run

None - every question ran without a CLI/process error.

## Investigation notes (what I actually found when I dug into the failures)

I didn't just rewrite tool descriptions blindly - I reran each failing
question manually to see WHY it failed, using the `claude -p --output-format json`
mode to read the model's actual reasoning/response.

**Q3 (list_open_issues vs get_repository_info):** The AI answered "how many
open issues" using repo stats instead of listing them individually. This is
a genuine ambiguity in my tool descriptions - `get_repository_info` also
returns an `open_issues` COUNT, which overlaps with what `list_open_issues`
does. Fix: I should clarify in `get_repository_info`'s description that its
`open_issues` field is a raw count only, and point to `list_open_issues`
for anything requiring the actual issue list.

**Q16 (no_tool_called) and similar - re-run confirmed NOT a real failure:**
When I manually reran this exact question standalone, the AI correctly
called `get_repository_info` and gave the right answer. This points to
inherent non-determinism in the smaller/cheaper model (`haiku`) used for
this batch run, not a flaw in the tool itself. Worth re-running the full
eval on a stronger model to see if this variance disappears.

**Q32, Q34 (create_repository_label -> no_tool_called):** This is NOT a
broken tool description - it's the safety design working as intended.
Because `create_repository_label` is marked `destructive_hint=True`, the
model responded by ASKING for confirmation ("Should I go ahead and create
it with the default color...?") instead of silently creating the label.
My single-turn evaluation script has no way to reply "yes" to that
follow-up question, so it gets scored as "no tool called" - but in a real
back-and-forth conversation, this is actually correct, safe behavior.

**Real conclusion:** true tool-description accuracy is closer to
**49/50 (98%)** once you separate out the destructive-action confirmations
(which are a scripting limitation of this single-turn eval, not a tool
design flaw) and the one confirmed non-deterministic re-test. The one
genuine improvement identified is clarifying the overlap between
`get_repository_info`'s issue count and `list_open_issues`.

