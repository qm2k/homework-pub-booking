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

*Note: As with Exercise 6, the Handoff Bridge code was already provided in my
repository. I chose to review and trace its execution rather than rewrite it,
ensuring the autograder remained intact. I did, however, have to make an
out-of-assignment fix to the `Makefile` to add a missing `ex7-real` target.*

The round-trip begins in Round 1 with the initial task to book a party of 12
near Haymarket. The `bridge` invokes the loop half, transitioning the session
state conceptually to executing the `loop` half. The loop half identifies
`Haymarket Tap` and uses the `handoff_to_structured` tool, resulting in a
forward handoff file. The bridge detects this and emits a
`session.state_changed` trace event (from `loop` to `structured`), passing the
booking data (party of 12) to the Rasa structured half.

Because `Haymarket Tap` can't handle a party of 12 under policy rules, the
structured half rejects it with the reason `party_too_large`. This causes a
reverse handoff: the bridge catches the rejection, marks the session state from
`structured` back to `loop`, and formulates a new `initial_task` that includes
the rejection reason.

This triggers the second research cycle (Round 2) in the loop half, which is
logged with the `bridge.round_start` trace event. The loop half is re-invoked
with the updated context, scales down the proposal to fit the policy (e.g.,
party of 6 at `The Royal Oak`), and performs another forward handoff. The
structured half accepts this new proposal, and the bridge marks the session as
`complete`.

---

## Citations

List at least THREE specific citations, one per transition you describe:

- `sessions/sess_a6f62ecbf5e0/logs/trace.jsonl:6` — forward handoff event (`from: loop, to: structured`)
- `sessions/sess_a6f62ecbf5e0/logs/trace.jsonl:7` — structured half rejection and reverse handoff (`from: structured, to: loop, rejection_reason: party_too_large`)
- `sessions/sess_a6f62ecbf5e0/logs/trace.jsonl:8` — reverse handoff triggers Round 2 (`bridge.round_start` for round 2)
