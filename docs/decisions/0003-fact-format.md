# ADR-0003: Fact format for the rules layer

Status: Accepted (2026-11-16)

## Context
The LLM layer (Phase 3) must not invent astrology. It should only describe
what was computed, and every statement must be traceable.

## Decision
Rules turn the chart JSON into `Fact(id, text, source, values)`:
- `id`: stable dotted name, e.g. `moon.dignity`, `rahu.aspect.saturn`
- `text`: one plain-English sentence
- `source`: path into the chart JSON the fact came from
- `values`: the raw values, so tests and the LLM layer never parse `text`

Facts restate library output (positions, house, retrograde, dignity, aspects),
with one exception: the dasha (below). Running dashas need an explicit `as_of`
date so results are reproducible. The LLM layer may only use facts and must
cite fact ids.

## Dasha is computed here, not taken from the library
The library's `dashas.balance` disagrees with its own Moon longitude: for the three
test charts it is -11.7, +46.4 and +15.9 days off (`scripts/check_dasha.py`). The error
is not constant, so it cannot be corrected with a shift. `dasha.py` computes the
Vimshottari periods from the Moon's sidereal longitude, the birth time and
365.2422-day years. Chart 1 matches Jagannatha Hora's nine Mahadasha dates to within
one day. Dasha facts cite the Moon's entry in the chart JSON as their source.

## Consequences
- Every fact can be checked against the chart JSON (tests do this).
- Library quirks pass through: dignity has five levels (no friendly/enemy), and
  Rahu/Ketu aspects follow the library's choice.
- A fact the library does not provide does not exist yet.
- Our Moon longitude is the library's; JHora differs by 20 to 70 arcseconds on
  planets (ayanamsa definition) and by about 27' on Rahu/Ketu (JHora: mean node,
  library: true node). See ADR-0002.

## Open items
- The year length is a convention (JHora uses 365.2422, others use 365.25).
  `YEAR_DAYS` in `dasha.py` makes it a one-line change.
- Only chart 1 has an independent dasha reference (JHora). Charts 2 and 3 are
  checked for internal consistency only.