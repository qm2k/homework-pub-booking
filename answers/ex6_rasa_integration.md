# Ex6 — Rasa integration

## Prompt

How did you wire Rasa CALM into the sovereign-agent `StructuredHalf` protocol?
Describe specifically: (1) how your subclass translates an input `dict` into a
Rasa-compatible intent payload, (2) how your `ActionValidateBooking` custom
action surfaces validation failures back into a `HalfResult`, and (3) one thing
you would change about the integration if you were building this for production.

**Word count:** 200-400 words.

## Your answer

*(Write your answer below this line. Do not remove the heading.)*

The Rasa integration translates the input dictionary via
`normalise_booking_payload` into a JSON payload routed to `/confirm_booking`.
Validation failures are detected by the `ActionValidateBooking` custom action,
triggering a rejection flow that is surfaced back to Python as a `HalfResult`
with an "escalate" action.

---

## Citations

List at least TWO specific citations from YOUR session directory:

- `sessions/sess_c635edc596c9/logs/trace.jsonl:15` — event showing Rasa dispatch and the output of the structured half (e.g., `booking confirmed by rasa`).
- `starter/rasa_half/validator.py` — normalise_booking_payload implementation showing dictionary transformation.
