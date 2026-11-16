# Ketana Drishti

AI-assisted Vedic astrology. Principle: **compute first, then interpret**. The ephemeris engine calculates; an LLM (later phases) only explains facts it is given.

## Quick start
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m ketana_drishti.cli --datetime 1998-05-14T08:30 --lat 23.0225 --lon 72.5714
```
Use `--place "City, Country"` instead of lat/lon when you have internet access.

Entertainment and reflection only; astrology has no validated predictive evidence.

## Status

| Phase | Status | Release |
|---|---|---|
| 1. Chart engine | Done | v0.1.0 |
| 2. Rules layer | Done | v0.2.0 |
| 3. LLM layer | Next | v0.3.0 |

## Facts

Turn a saved chart JSON into the facts the AI layer will be allowed to use:

```
python -m ketana_drishti.facts_cli chart.json --as-of 2026-11-16
```

Each fact has an id, a sentence, the path it came from in the chart JSON, and its raw values.
Positions, houses, retrograde, dignity and aspects come from the chart library;
the Vimshottari dasha is computed from the Moon's longitude (see ADR-0003).
Add `--json` for machine-readable output.
