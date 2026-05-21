# Ex5 — Edinburgh research loop scenario

## Prompt

Describe the trajectory your Ex5 scenario takes through the loop half. Which
subgoals did the planner produce? Which tools were called? Were there any
tool calls that the dataflow integrity check would have flagged if you had
left them uncorrected?

**Word count:** 150-300 words.

## Your answer

*(Write your answer below this line. Do not remove the heading.)*

The `FakeLLMClient` offline trajectory produced exactly one subgoal (`sg_1`)
rather than decomposing the task further. This was a deliberate choice so the
executor can share state between the research gathering and the flyer writing
steps without relying on the orchestrator to pass context via the data plane.

Within this single subgoal, the executor called four tools in sequence:
`venue_search` (with parameters `near='Haymarket'`, `party_size=6`),
`get_weather` (`city='Edinburgh'`), `calculate_cost`
(`venue_id='haymarket_tap'`, etc.), and finally `generate_flyer`. The first
three tools are `parallel_safe=True` because they only read from static JSON
fixtures, meaning they could theoretically run simultaneously. However,
`generate_flyer` is `parallel_safe=False` because it produces a side effect
(writing the HTML flyer to the workspace).

If left uncorrected, the dataflow integrity check would have flagged any
discrepancy between the numbers used in the flyer and the outputs of the tools.
For example, if the LLM hallucinated the deposit as `£150` instead of the
actual `£112` returned by `calculate_cost`, the `ex5_integrity` logic (which
inspects the `_TOOL_CALL_LOG`) would throw a `SA_INTEGRITY_VIOLATION` since
`150` never appeared in the tool outputs. This prevents plausible-looking but
fabricated constraints from leaking into customer-facing outputs.

*Note on implementation:* To get this scenario working smoothly, I implemented
the required tools but also had to apply several out-of-assignment framework
fixes to the underlying codebase. These included optimizing the planner prompt
to prevent executor state loss, replacing a hardcoded `half.run` with proper
Orchestrator dispatch, fixing `ToolError` missing messages, defining an
explicit schema for `generate_flyer`, and correcting the flyer facts
verification logic in the integrity checker itself.

---

## Citations

List at least TWO specific citations from YOUR session directory. Format:

- `sessions/sess_2791d51f1e2e/logs/tickets/tk_fcb35db4/summary.md` — planner producing a single subgoal
- `sessions/sess_2791d51f1e2e/logs/trace.jsonl:3` — executor calling venue_search, get_weather, and calculate_cost
