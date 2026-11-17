# Changelog
## [0.3.0] - 2026-11-16

### Added
- Claude client wrapper (`llm.py`) with an offline `FakeClient`; model name from `KETANA_MODEL`, key from `.env`.
- Grounded readings (`reading.py`): the model sees fact ids and text only, answers through a forced tool call, and every statement must cite fact ids.
- Citation checker with one retry; statements with no or unknown fact ids, or blocked topics, are rejected.
- Disclaimer added by code; readings in English, Hindi and Gujarati.
- `POST /api/reading` and a Reading tab on the web page.
- Demo mode (`KETANA_DEMO=1`) so the Reading tab works without an API key or credit.
- ADR-0004 (grounded LLM layer), `scripts/llm_smoke.py`, `scripts/reading_demo.py`.

### Notes
- The topic guardrail checks English words only; see ADR-0004.
- Real readings need API credit. All tests run offline.

All notable changes to Ketana Drishti are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [0.2.0] - 2026-11-16
### Added
- Fact format (`Fact`) and rules for Lagna, planets, retrograde, dignity and aspects
- Vimshottari dasha facts (balance at birth and the running Mahadasha, Antardasha and Pratyantardasha for a given date)
- `facts_cli` command to print the facts of a saved chart
- Tests across all three fixture charts
- ADR-0003 (fact format and dasha decision)

### Changed
- Dasha periods are computed from the Moon's longitude (`dasha.py`) instead of the library's dasha block, whose balance was off by -12 to +46 days; chart 1 now matches Jagannatha Hora to within a day

### Fixed
- The "dasha balance about 9 days shorter than Jagannatha Hora" issue from 0.1.0 (see above)

## [0.1.0] - 2026-11-16
### Added
- Command-line tool that takes a birth date, time and place (or latitude and longitude)
  and prints a Vedic birth chart as JSON (jyotishganit).
- Geocoding and a daylight-saving-aware UTC offset for the birth moment.
- `--out` option that creates missing output folders.
- `scripts/flatten.py` and `scripts/compare.py` for inspecting chart output.
- Cross-check of three charts (Ahmedabad, Toronto, Sydney) against Jagannatha Hora:
  all 30 values agree on sign and Nakshatra, every difference under 1 arcminute.
- Devlog, ADR-0001 (chart library and licence), ADR-0002 (cross-check tolerance).

### Known issues
- Dasha balance at birth is about 9 days shorter than Jagannatha Hora's (lord matches).
- A 43 arcsecond difference can move a planet across a pada boundary.
- First run downloads about 60 MB of ephemeris data (planets and the Hipparcos catalog).

## [0.4.0] - 2026-11-17

### Added
- Reference corpus (`corpus/passages.json`): 75 short passages in original wording covering planets, signs, houses, nakshatras, dignities, dasha lords, Lagna and drishti.
- Retrieval from facts (`retrieval.py`): deterministic key match with aliases for spelling variants; no embeddings. Ranked Lagna, Moon, Sun, running dasha first; capped at 30.
- Readings cite passages as well as facts. Every statement must still cite at least one fact; a passage alone is rejected.
- `/api/reading` returns the passages used; the Reading tab shows them.
- Evaluation (`evaluation.py`, `scripts/run_eval.py`, `eval/births.json`): 24 charts; checks that each fact traces to the chart, retrieval has no gaps and is repeatable, and every kind of bad reading is rejected. Results in `docs/eval-results-v0.4.0.md`.
- ADR-0005 (corpus and retrieval).

### Fixed
- The topic guardrail rejected the zodiac sign Cancer and the word "investigation". Cancer is now allowed (only lower-case "cancer" is blocked) and "invest" no longer matches "investigation".

### Notes
- Chroma and embeddings are deferred (ADR-0005).
- The corpus is a draft for review by someone who knows Jyotish.