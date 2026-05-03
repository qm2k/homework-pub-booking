🍺 **Week 5 Homework is live — build an AI agent that books a pub**

Hi @everyone ! The Module 1 Week 5 homework is out. You'll build an agent that researches Edinburgh pubs, negotiates with a manager, and has a real voice conversation about the booking.

**Repo:** https://github.com/sovereignagents/homework-pub-booking
**Deadline:** 2026-05-22 23:59 UTC-12 (≈ 2026-05-23 noon London)

## Getting started (do this first)

Don't overthink it. Go to https://github.com/sovereignagents/homework-pub-booking for the repo, and then from your fork:

```bash
git clone git@github.com:sovereignagents/homework-pub-booking
cd homework-pub-booking
make
```

That's it. The `make` command (no arguments) prints a structured walkthrough. **Read it.** Everything you need is in there.

Then, when you're not sure what to do next at any point, just run:

```bash
make next
```

It looks at your repo state and tells you the literal next command. Haven't implemented Ex5 yet? It'll say "open starter/edinburgh_research/tools.py and implement TODO 1." Stuck after running a scenario? It'll tell you to run `make narrate-latest` to see what happened in English.

## What you're building (5 exercises)

| Ex | What | Time |
|---|---|---|
| **Ex5** | Loop half with 4 tools + dataflow-integrity check that catches LLM fabrication. You'll produce an HTML flyer you can actually open in a browser. | ~3–4h |
| **Ex6** | Rasa CALM dialog engine running alongside your agent. Your agent POSTs to it; Rasa decides whether to confirm or reject the booking. Three terminals. ⚠️ | ~4–5h |
| **Ex7** | Handoff bridge — when Rasa rejects, send control back to the loop to find an alternative. Round-trip state machine. | ~2–3h |
| **Ex8** | Real voice pipeline. Speechmatics STT + Rime.ai Arcana TTS. Talk to your agent. | ~3–5h |
| **Ex9** | Reflection. 3 written questions grounded in YOUR session logs. | ~1–2h |

## This homework uses our open-source agent framework

The homework is built on **sovereign-agent**, which we released publicly. If you look at the pedagogy you'll see why. It bakes the 8 architectural decisions we teach straight into the library:

> **⭐ Star it here:** https://github.com/sovereignagents/sovereign-agent
> (Your homework pins `sovereign-agent == 0.2.0` exactly. Same version the grader runs.)

It's a young library. Stars help others find it. Issues help us improve it. If the framework surprises you in any way during the homework, good or bad, open an issue.

## Grading

The grader breakdown is honest. A fresh clone scores **4/76** (just scaffold-preservation points). A complete, well-implemented submission scores **~70/76** locally (30 Reasoning points come from CI with LLM-as-judge).

```
Mechanical    27 pts    lint, format, tests pass without skips
Behavioural   19 pts    each exercise runs end-to-end
Reasoning     30 pts    Ex9 answers, graded by CI's LLM-as-judge
────────────────────
Total         76 pts
```

Run `make check-submit` anytime to see your local score. It's advisory — CI at the deadline is authoritative.

**Grading submission app** — in the coming days I'll release the app where you connect your GitHub ID for submission. I'll post the link here as soon as it's ready. For now, just focus on making it work on your machine.

**Bonus content** — I'll also share a notebook pack in the next few days covering exercises from **all 5 weeks** of Module 1. Great for review, for reinforcing concepts, and for seeing each week connect to the next.

## When things break (and they will, that's part of the curriculum)

Four layers of help, in order:

1. **`make verify`** — one-shot env diagnostic. Run this FIRST when anything seems weird.
2. **`make narrate-latest`** — replays your last run in plain English with tool-call timeline.
3. **`docs/real-mode-failures.md`** — catalogue of every known real-mode failure (Qwen spiraling, Rasa cache issues, voice SDK quirks) with diagnosis + fix.
4. **Open an issue** with the output of `make educator-diagnostics` — that gives us everything we need to help.

**A note on real-mode failures** — when you run `make ex5-real` and Qwen spirals, or `make ex6-real` and Rasa is confused, those aren't bugs you lost marks on. They're the curriculum. Real agent systems fail like this. Learning to read a trace (`make narrate-latest` + `docs/real-mode-failures.md`) is the point.

## ⚠The three gotchas that trip people up

1. **Ex6 needs THREE terminals.** Read `make ex6-help` before starting. `make rasa-actions` in one terminal, `make rasa-serve` in another, `make ex6-real` in a third.
2. **After editing any file in `rasa_project/actions/`, restart `make rasa-actions`.** Rasa caches Python modules in memory; your changes won't load until restart.
3. **The `make ex5-real` Qwen spiral is real.** It's documented. Don't panic when it happens; read the failure doc.

## API keys

Free tier works for everything:

- **NEBIUS_KEY** (mandatory for Ex5, Ex7, Ex8) — https://tokenfactory.nebius.com
- **RASA_PRO_LICENSE** (mandatory for Ex6 real mode) — https://rasa.com/rasa-pro-developer-edition/
- **SPEECHMATICS_KEY** (Ex8 voice, optional) — https://portal.speechmatics.com
- **RIME_API_KEY** (Ex8 voice, optional) — https://rime.ai

## Deadline (again, because it matters)

**Deadline: 2026-05-22 23:59 UTC-12**
Equivalent: **2026-05-23, noon London time.**

Timezone is UTC-12 (the latest possible cutoff globally), so if it's still the 22nd anywhere on Earth, you're fine.

