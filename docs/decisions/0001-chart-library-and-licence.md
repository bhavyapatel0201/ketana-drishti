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