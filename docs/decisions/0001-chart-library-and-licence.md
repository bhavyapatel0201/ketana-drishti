# ADR-0001: Chart library and licence

Status: accepted

## Context
Phase 1 needs a Vedic chart engine. Candidates: jyotishganit (MIT), kalagana, PyJHora,
Kerykeion and pyswisseph (AGPL).

## Decision
Use jyotishganit. The repo is licensed AGPL-3.0, chosen at repo creation as a safe default.

## Alternatives considered
- Kerykeion / pyswisseph: AGPL, which would force an open-source service anyway.
- Permissive engines (openephem, JyotiPy): less Vedic coverage.

## Consequences
- jyotishganit and skyfield are permissively licensed, so the licence can be revisited.
- The engine downloads planet ephemeris data and the Hipparcos catalog on first run.

## Update 2026-11-16
The repository is licensed under MIT (the `LICENSE` file), not AGPL-3.0 as first written.
All current dependencies (jyotishganit, Skyfield, geopy, timezonefinder, FastAPI) are
permissively licensed, so MIT is compatible. Revisit this if an AGPL library
(e.g. Kerykeion or pyswisseph) is ever added.