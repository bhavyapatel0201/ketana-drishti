# ADR-0005: RAG corpus and retrieval

Date: 2026-11-17
Status: Accepted

## Context

Phase 4 lets readings draw on reference passages (what a planet, sign, house,
nakshatra, dignity or dasha lord traditionally signifies) as well as on computed
facts. Two questions: where does the text come from, and how are passages found?

## Decision

**Corpus.** Short passages (1-2 sentences) **written for this project in original
wording**, stored in `corpus/passages.json` under the repository's MIT licence.
They record traditional associations, not predictions. No text is copied from
books or websites, so there is no licence question. Modern translations of the
classical texts are in copyright, so they are not used. Public-domain
translations may be considered later, but only after their status is checked and
recorded here.

First version (75 passages): 9 planets, 12 signs, 12 houses, 27 nakshatras, 4
dignities, 9 dasha lords, plus Lagna and drishti.

**Retrieval is a deterministic key match, not embedding search.** A fact already
says what it is about (`moon.nakshatra` = Jyeshtha, `venus.house` = 10, a running
dasha of Venus), so the lookup is exact: same chart, same passages. Spelling
variants and Sanskrit names are handled by aliases and normalisation. Passages
are ranked Lagna first, then Moon, Sun, running dasha, then the rest, and capped
at 30 to bound prompt size. Each passage records which facts brought it in.

**Chroma and embeddings are deferred.** They would add a model download,
non-determinism and a harder evaluation, and they solve a problem we do not yet
have. They may be added later to match a free-text *question* to passages, as an
optional re-ranker, never as the only path.

**Passages follow the Phase 3 rules.** Passage text must pass the same topic
guardrail as model output (a test enforces this). Passages will get ids of their
own and be cited like facts; a statement may cite only facts or passages that
were supplied.

## Consequences

- Retrieval is free, offline and fully testable; the evaluation (Day 12) can
  assert exact passages for a chart.
- Coverage is only as wide as the corpus: combinations (a planet in a particular
  house or sign) are not written yet and can be added as new `kind`s.
- The corpus is an editorial work product. It should be reviewed by someone who
  knows Jyotish, and corrections are normal pull requests.
- A test over the fixture charts fails if the chart library spells a
  nakshatra or sign in a way the corpus does not know, so gaps cannot hide.
