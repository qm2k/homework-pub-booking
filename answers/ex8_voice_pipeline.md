# Ex8 — Voice pipeline

## Prompt

Describe how your voice pipeline handles state across STT → LLM → TTS turns.
Where does the conversation history live? How does the Llama-3.3-70B manager
persona stay in character? If you ran in voice mode (not just text), describe
one failure mode you observed with real audio (latency, transcription errors,
audio quality) and how you'd address it.

If you only ran in text mode, answer the state question, the persona question,
and describe ONE plausible failure mode you'd expect from voice even without
having tested it. (Full credit still possible.)

**Word count:** 200-400 words.

## Your answer

*(Write your answer below this line. Do not remove the heading.)*

*Note: The voice pipeline implementation was also pre-populated in my starter
codebase. I reviewed its architecture and ran the text-mode simulation rather
than discarding the existing code.*

In the voice pipeline, state is maintained across turns by persisting the
conversation history within the `ManagerPersona` class as an in-memory list of
message dictionaries. Each turn appends the user's STT text as a `{"role":
"user", ...}` message, calls the `OpenAICompatibleClient`, and appends the
model's response as `{"role": "assistant", ...}` before synthesizing it via
TTS.

The Llama-3.3-70B manager persona stays in character through a highly specific
system prompt injected as the first message in the history. The prompt mandates
the persona of Alasdair, a gruff Edinburgh pub manager who only accepts
specific party sizes and uses Scottish vernacular. By carrying the full history
with this system prompt prepended on every LLM call, the persona reliably
remains consistent.

Since I ran the scenario in text mode without Speechmatics, a highly plausible
failure mode for real voice audio would be transcription errors handling
Scottish accents or venue names (e.g., "The Royal Oak" interpreted as "Roy
Look"). This can cause the LLM to misinterpret the venue context and falsely
reject or derail the booking. I would address this by providing a custom
vocabulary/dictionary payload (often supported by STT APIs like Speechmatics)
containing the names of all our valid pubs to bias the STT model toward correct
entity transcription.

---

## Citations

List at least TWO specific citations:

- `sessions/sess_386b68b706ea/logs/trace.jsonl:1` — `voice.utterance_in` trace event representing the incoming user text.
- `sessions/sess_386b68b706ea/logs/trace.jsonl:2` — evidence of persona: the trace `voice.utterance_out` event capturing Alasdair's in-character reply ("Aye, we can do that. I'll pencil you in").
