# ADR-0004: Grounded LLM layer (cite or reject)

Date: 2026-11-16
Status: Accepted

## Context

Phases 1 and 2 compute the chart and turn it into facts (`Fact(id, text, source, values)`).
Phase 3 adds a language model that writes the reading. A model left alone will invent
planet positions, dashas and yogas, and will drift into health, money and relationship
predictions. The project principle is "compute first, then interpret": the model may
explain facts, never create them.

## Decision

1. **The model sees facts only.** The prompt contains each fact's id and text. It never
   receives the raw chart JSON, so it cannot read a number that is not already a fact.
2. **Structured output with citations.** The model must answer by calling one tool,
   `give_reading`, which returns statements, each with at least one `fact_ids` entry.
3. **We check the answer in code** (`reading.check`). A statement is rejected if it is
   empty, cites no fact id, cites an id that does not exist, or contains a blocked topic
   word. On any problem we retry once, listing the problems to the model. After the retry
   we keep only valid statements; if none are valid the request fails.
4. **The disclaimer is added by code**, not by the model, so it can never be dropped.
5. **Languages:** English, Hindi, Gujarati. The model writes the statement text in the
   requested language; fact ids stay unchanged.
6. **Model name from the environment** (`KETANA_MODEL`, default `claude-sonnet-5-5`), so a
   model change needs no code change. The API key is read from `.env` / the environment and
   is never printed, logged or included in an error message.
7. **Tests run offline** with `FakeClient`; no test calls the network or costs money.
8. **Demo mode** (`KETANA_DEMO=1`) makes `/api/reading` answer from a scripted fake that
   only restates facts, so the Reading tab can be built and shown without an API key or
   credit. The response says `demo: true` and the page labels it.

## Consequences

- A citation proves the model pointed at a real fact. It does **not** prove the sentence
  is a faithful reading of that fact. Faithfulness is only as good as the prompt and the
  model; later phases (RAG, review) may tighten it.
- The topic guardrail checks English words only. Hindi and Gujarati output is covered by
  the prompt rule alone. A language-aware check is future work.
- Real readings need API credit. Development did not: the whole layer is tested offline.
  Which model or provider serves the live site is decided at go-live (Phase 6); the client
  sits behind a small interface (`complete(system, user, tool)`), so a second provider
  would be an additional client, not a rewrite.
- Facts sent to `/api/reading` come from the browser. That is acceptable because the
  reading only describes what the caller supplied; the server still enforces that every
  statement cites one of those facts.
