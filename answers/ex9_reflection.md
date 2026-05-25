# Ex9 — Reflection

Answer all three questions. The grader expects every question to be answered;
blank answers are zero.

---

## Q1 — Planner handoff decision

### Prompt

Find a point in your Ex7 logs where the planner decided to hand off to the
structured half. Quote the planner's reasoning or the specific subgoal's
`assigned_half` field. What signal caused the decision?

**Word count:** 100-250 words.

### Your answer

*(Write your answer below this line.)*

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

### Citation (required)

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

### Prompt

Describe one instance where your Ex5 dataflow integrity check caught something
manual inspection would have missed, OR (if the check never triggered in your
runs) describe a plausible scenario where it WOULD catch a failure. Your
scenario must be specific enough that someone else could construct the test
case.

**Word count:** 100-250 words.

### Your answer

*(Write your answer below this line.)*

The Ex5 dataflow integrity check initially suffered from a "circular
self-confirmation" flaw (self-verifying validation). Before it was corrected,
the check scanned both the `output` and the `arguments` of all recorded tool
calls to verify facts present in the flyer. 

Because the `generate_flyer` tool logs its own arguments (which contain the very
facts the LLM decided to put in the flyer), any hallucinated fact passed to
`generate_flyer` would vacuously validate itself. The validator was merely
confirming that the artifact contained the values it wrote, rather than checking
against an independent source of truth (the actual outputs of the upstream
research tools).

Manual inspection of the `flyer.html` completely misses this because the flyer
looks perfectly plausible (e.g., claiming a total cost of £540). The integrity
check, in its broken state, also missed it because it found `540` in the
`generate_flyer` argument log. It was only after modifying
`fact_appears_in_log` to exclusively scan the `output` fields of prior tools
that the validator successfully caught the inconsistency between the research
outputs and the generated artifact. The architectural lesson is clear: if your
validator and agent share state, you don't have validation.

### Citation (required)

Plausible test case (Circular Self-Confirmation):

1. `calculate_cost` outputs `{"total_gbp": 497}`.
2. LLM hallucinates and calls `generate_flyer` with `{"total_gbp": 540}`.
3. If `integrity.py` checks tool arguments, `540` is found in `generate_flyer`'s
   own log, and the check falsely passes.
4. Once fixed to only check `record.output`, the check correctly raises
   `SA_INTEGRITY_VIOLATION` because `540` was never an upstream output.


---

## Q3 — First production failure + primitive

### Prompt

If you were shipping this agent to a real pub-booking business next week,
what's the first production failure you'd expect, and which sovereign-agent
primitive (ticket state machine, manifest discipline, IPC atomic rename,
SessionQueue retry, drift-corrected scheduler, mount allowlist, HITL approval,
etc.) would surface it?

Name EXACTLY ONE primitive and EXACTLY ONE failure mode. Vague answers that
name multiple primitives or generic "something will break" failures lose
points.

**Word count:** 100-250 words.

### Your answer

*(Write your answer below this line.)*

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

### Citation (optional but encouraged)

Reference: `docs/real-mode-failures.md` (Section: Ex5 — Qwen3-32B spiral on
venue_search) and Sovereign-Agent Architecture (Ticket execution limits).

