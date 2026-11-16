# Devlog - Ketana Drishti

A running record of what was built, what broke, and what was decided.
Newest entries at the bottom.

---

## Phase 1 - Chart engine (v0.1.0)

### YYYY-MM-DD - Project setup
- Created the public repo `ketana-drishti` (AGPL-3.0, see ADR-0001).
- Set up branch protection on `main` (pull request required), milestones, issues and the project board.
- Workflow: branch -> pull request -> squash merge, Conventional Commits, CHANGELOG, tagged releases.

### YYYY-MM-DD - Chart library and geocoding
- Chose jyotishganit for Vedic (sidereal) charts. Ayanamsa is Lahiri, reported as "True Chitra Paksha".
- Added `geo.py`: place name -> lat/lon (geopy), then the DST-aware UTC offset at the birth moment (timezonefinder).
- Added `chart.py` (`build_chart`) and `cli.py` (`--datetime`, `--place`, `--lat`, `--lon`, `--name`, `--out`).
- Problem: the library downloads `de421.bsp` and the Hipparcos catalog `hip_main.dat` (~51 MB). The Strasbourg server was unreachable, so the file came from the Harvard mirror. Both files are in `.gitignore`.
- Problem: `--out` to a missing folder raised FileNotFoundError. Fixed with `mkdir(parents=True, exist_ok=True)`.

### YYYY-MM-DD - Cross-check against Jagannatha Hora
- Compared 3 charts, 30 values (Lagna and planets: sign, degrees, nakshatra, pada).
- Result: all within about 1 arcminute (tolerance decided in ADR-0002).
- Lesson: JHora keeps stray seconds in the birth time (e.g. :21). Run our CLI with JHora's exact time, or the Lagna differs by minutes of arc.
- Lesson: when entering charts in JHora, double-check the time and time zone fields (they were swapped once).
- Open items: small unexplained residuals, and a dasha balance difference of about 9 days. Both are carried into Phase 2.
- Saved the three JHora-checked charts as test fixtures in `tests/fixtures/`.
- Released v0.1.0.

---

## Phase 2 - Rules layer (v0.2.0)

### YYYY-MM-DD - Fact format (issue #8)
- A `Fact` is `(id, text, source, values)`. `source` is the path into the chart JSON, so every statement can be traced back.
- Facts are the only material the later LLM layer may use, and every statement must cite fact ids.
- Added Lagna facts (sign, nakshatra and pada) and planet facts (sign, nakshatra and pada, house, retrograde, dignity).
- Rahu and Ketu are never flagged retrograde.
- Tests: Lagna Gemini and Moon Jyeshtha pada 4 and debilitated (chart 1), Saturn retrograde (chart 3), Rahu not retrograde.

### 2026-11-16 - Dignity facts (issue #9)
- The library returns five dignity words: exalted, debilitated, own_sign, moolatrikona, neutral. There is no friendly/enemy level, so "neutral" means no special dignity.
- Facts keep the raw word in `values` and use readable text (e.g. "in its own sign").
- Added tests that run on every fixture: house/sign/nakshatra, retrograde, dignity words, and that each fact's `source` path exists in the chart JSON.
- 16 tests passing. The 2 warnings are a NumPy deprecation inside skyfield, not our code.

### Next
- Issue #10: drishti (aspect) facts from the library's `aspects` / `aspectsReceived` data.
- Issue #11: current dasha facts, and the dasha balance and end-date comparison with JHora.
- Issue #12: `facts` CLI command, ADR-0003 (fact format), README example, CHANGELOG, tag v0.2.0.

### 2026-11-16 - Aspect facts (issue #10)
- The library already provides aspects: each planet has `aspects.gives` (target planet or house plus `aspect_type`), and each house has `aspectsReceived`. We turn that data into facts and compute nothing ourselves.
- `aspect_type` is the house count from the planet (7 = opposite house). A test checks this on all three fixtures.
- Rahu and Ketu get 5th, 7th and 9th aspects from the library. Traditions differ on whether the nodes aspect at all, so the text only reports what the library says.
- 23 tests passing.

### 2026-11-16 - Dasha facts (issue #11)
- Library dasha data: `dashas.balance` (birth-nakshatra lord and years remaining) and `dashas.all.mahadashas`, nested Mahadasha > Antardasha > Pratyantardasha, each with ISO `start` and `end` dates. It has no "current dasha" marker.
- Facts: `dasha.balance` always; running `dasha.mahadasha`, `dasha.antardasha` and `dasha.pratyantardasha` only when `build_facts(chart, as_of=date)` is given a date. Readings stay reproducible because nothing depends on today's date.
- Chart 1 balance is consistent with 365.25-day years (Mercury ends 2000-12-02, minus 2.5555 years = birth date).
- Still open: the ~9 day gap to JHora (see below).
- 31 tests passing.

### 2026-11-16 - v0.2.0 released
- Added `facts_cli` and ADR-0003, tagged and released v0.2.0. Phases 1 and 2 are done; the rules layer works without any AI.
- A commit went straight to `main` (owner bypass of the branch protection). From now on every change goes through a branch and PR.

### Next
- Phase 3, LLM layer (v0.3.0): a Claude client that may only use the facts, a citation checker, guardrails, ADR-0004.

### 2026-11-16 - Licence corrected
- The repo is MIT (LICENSE file); ADR-0001 said AGPL-3.0. Updated the docs to match.

## 2026-11-16: Phase 3, LLM layer

- Wrote the Claude client wrapper with a fake for offline tests. Hit two setup problems: pasted the key ID instead of the secret (`apikey_...` vs `sk-ant-...`), and then a "credit balance too low" error. Made client errors show Anthropic's own message, never the key.
- Built the grounded reading flow: facts in, tool call out, citation check, one retry, disclaimer from code.
- Added `/api/reading`, the Reading tab, and a free demo mode so the feature can be shown without credit.
- Decided not to buy credit yet; the live-model choice moves to Phase 6 (ADR-0004).
- Lesson: an exposed key must be deleted at once, and secrets belong only in `.env`.