# Ex9 — Reflection

## Q1 — Planner handoff decision

### Your answer

In my Exercise 7 trace, the deterministic loop planner (via `FakeLLMClient`)
assigned the venue search subgoal with the field `assigned_half: "loop"`.
Rather than the planner directly handing off to Rasa, the executor inside the
loop half triggered the `handoff_to_structured` tool after successfully finding
a venue. The reasoning provided by the executor for this tool call was: "loop
half identified a candidate venue; passing to structured half for confirmation
under policy rules". The signal that caused this decision was the successful
completion of the unstructured research phase—specifically, identifying a
candidate venue (`Haymarket Tap`) that met the initial criteria, which then
required Rasa to validate the booking against strict business policies (e.g.,
party size caps).

### Citation

Trace from session `sess_a6f62ecbf5e0`:
```json
{
    "event_type": "executor.tool_called",
    "payload": {
        "tool": "handoff_to_structured",
        "arguments": {
            "reason": "loop half identified a candidate venue; passing to structured half for confirmation under policy rules",
            "context": "party of 12 near Haymarket on 2026-04-25 19:30; chosen venue haymarket_tap",
            ...
        }
    }
}
```
And from `run.py` plan:
`"id": "sg_1", "description": "find venue near haymarket for 12", "assigned_half": "loop"`


---

## Q2 — Dataflow integrity catch

### Your answer

A plausible scenario where the Ex5 dataflow integrity check (`ex5_integrity`)
would catch a failure that a human reviewer would miss is an LLM hallucination
of specific data values. Suppose Qwen3-32B successfully searches for a venue
and the tool returns "The Royal Oak" with a capacity of 16. However, the
original user request was for a party of 12. During the `generate_flyer` tool
call, the LLM hallucinates and passes `"capacity": 12` instead of the actual
`"capacity": 16` returned by the API. Alternatively, it might hallucinate a
temperature of `20°C` instead of the actual `15°C` returned by the
`get_weather` tool. 

A human reviewer inspecting the resulting `flyer.html` would see "15°C" and
"Capacity: 12" and assume the flyer is perfectly plausible, completely missing
that the data was fabricated by the LLM. The dataflow integrity check catches
this immediately because it tracks the actual outputs from `_TOOL_CALL_LOG` and
verifies that the exact values returned by the tools are the ones present in
the final flyer payload.

In fact, the dataflow integrity check actually caught errors from the
deterministic fake model immediately after small bugs in the integrity check
itself were fixed (commit `a79d221`). Previously, the check erroneously
included the `generate_flyer` tool's own arguments when searching for valid
facts, meaning any hallucinated fact passed to `generate_flyer` would vacuously
validate itself. Once the check was fixed to only scan the *outputs* of *other*
tools, it immediately caught that the fake model's scripted responses were
inconsistent (the script called `calculate_cost` for 5 people yielding £497,
but called `generate_flyer` for 6 people and £540).

I must note that while catching hallucinations the way suggested in the code is
better than nothing, everything we can deterministically check we could also
deterministically fill not relying on the model. In a sense relying on the
model for passing details between deterministic tool calls seems redundant.

### Citation

Plausible test case:

1. `get_weather` tool returns `{"temperature_c": 15}`.
2. LLM calls `generate_flyer` with `{"event_details": {"temperature_c": 20}}`.
3. `ex5_integrity` check fails at: `assert value in [call.output for call in
   _TOOL_CALL_LOG]`, raising `SA_INTEGRITY_VIOLATION` because `20` was never
   returned by any tool.


---

## Q3 — Removing one framework primitive

### Your answer

If I were shipping this to a real pub-booking business, the first production
failure I'd expect is the LLM entering an infinite ReAct loop—for example,
repeatedly calling `venue_search` with slightly different parameters (e.g.,
party size 30, 40, 50) when it cannot find a venue that exactly matches all the
user's obscure constraints. Because generative models default to retrying
rather than gracefully failing, this can quickly burn through token budgets. 

The sovereign-agent primitive that would surface this failure is the **ticket
state machine**. By tracking metrics like `turns_used` and `tool_calls_made`
for each executing ticket, the state machine will eventually hit its hard
threshold (e.g., the 8-turn limit). Instead of spinning forever, the ticket
state machine will halt execution and transition the subgoal's status to
`failed`, surfacing the failure to the planner or bridge for appropriate
recovery.

### Citation

Reference: `docs/real-mode-failures.md` (Section: Ex5 — Qwen3-32B spiral on
venue_search) and Sovereign-Agent Architecture (Ticket execution limits).

