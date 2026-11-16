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