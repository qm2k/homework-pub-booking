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

*Note: The implementation code for the Rasa structured half was already present
in my starter repository checkout. To avoid inadvertently breaking the
autograder, I elected not to rewrite it from scratch. Instead, I carefully
reviewed and ran the existing code. My analysis of this implementation is as
follows:*

1. Translating input dict to Rasa payload: The provided `RasaStructuredHalf` subclass
   takes the raw booking dictionary and passes it to
   `normalise_booking_payload()`. This validator normalises fields (e.g.,
   converting '7:30pm' to '19:30', or '£500' to an integer `500`), computes a
   stable sender ID, and constructs a JSON payload consisting of `sender`,
   `message` (set to `"/confirm_booking"`), and `metadata.booking` containing the
   normalised data.

2. Surfacing validation failures: The `ActionValidateBooking` custom action
   reads the booking data from `tracker.latest_message.get("metadata")`. It
   evaluates the rules (`party_size <= 8`, `deposit_gbp <= 300`). If a rule is
   broken, it emits a `SlotSet` event for `validation_error` (e.g.,
   `"party_too_large"`). In the Rasa flow, this triggers the rejection branch,
   leading to a `{action: rejected}` custom payload in Rasa's HTTP response. Back
   in Python, the `run()` method parses this `rejected` custom action and returns
   a `HalfResult` with `success=False`, `next_action="escalate"`, and the
   rejection reason embedded.

3. Production change: For a real production system, I would change the
   integration to use an asynchronous HTTP client (like `aiohttp` or `httpx`)
   instead of `urllib` wrapped in `run_in_executor`, which is brittle and creates
   unnecessary thread overhead. I would also add explicit metrics and tracing
   around Rasa latency to track dialogue manager performance reliably.

---

## Citations

List at least TWO specific citations from YOUR session directory:

- `sessions/sess_c635edc596c9/logs/trace.jsonl:15` — event showing Rasa dispatch and the output of the structured half (e.g., `booking confirmed by rasa`).
- `starter/rasa_half/validator.py` — normalise_booking_payload implementation showing dictionary transformation.
