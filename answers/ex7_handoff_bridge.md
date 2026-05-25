# Ex7 — Handoff bridge

## Prompt

Walk through the bidirectional round-trip your handoff bridge performs. Start
with the initial task, describe each handoff event (forward and reverse), and
explain what session state the system is in at each transition. Identify the
exact line in your logs where the second research cycle begins after the
structured half's first rejection.

**Word count:** 200-400 words.

## Your answer

*(Write your answer below this line. Do not remove the heading.)*

The bridge handles bidirectional round-trips by orchestrating state transitions:
it executes the loop half, catches forward handoffs to pass to the structured
half, and if rejected (e.g. `party_too_large`), creates a reverse task with the
rejection reason, prompting a second research cycle logged by
`bridge.round_start`.

---

## Citations

List at least THREE specific citations, one per transition you describe:

- `sessions/sess_a6f62ecbf5e0/logs/trace.jsonl:6` — forward handoff event (`from: loop, to: structured`)
- `sessions/sess_a6f62ecbf5e0/logs/trace.jsonl:7` — structured half rejection and reverse handoff (`from: structured, to: loop, rejection_reason: party_too_large`)
- `sessions/sess_a6f62ecbf5e0/logs/trace.jsonl:8` — reverse handoff triggers Round 2 (`bridge.round_start` for round 2)
