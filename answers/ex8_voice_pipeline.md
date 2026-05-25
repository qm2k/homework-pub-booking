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

Conversation history is persisted in-memory as a list of message dictionaries
inside `ManagerPersona`, ensuring the Llama-3.3-70B persona maintains context
and character across turns. I am utilizing text-mode degradation; a plausible
voice failure mode is STT misinterpretation of venue names, which could be
mitigated by supplying a custom vocabulary payload.

---

## Citations

List at least TWO specific citations:

- `sessions/sess_386b68b706ea/logs/trace.jsonl:1` — `voice.utterance_in` trace event representing the incoming user text.
- `sessions/sess_386b68b706ea/logs/trace.jsonl:2` — evidence of persona: the trace `voice.utterance_out` event capturing Alasdair's in-character reply ("Aye, we can do that. I'll pencil you in").
