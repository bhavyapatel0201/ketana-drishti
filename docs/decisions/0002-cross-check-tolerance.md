# ADR-0002: Cross-check tolerance against Jagannatha Hora

Status: accepted

## Context
Three charts (Ahmedabad 1998, Toronto 2020, Sydney 2005) were compared with JHora using
identical inputs, including JHora's stray seconds.

## Decision
Accept differences under 1 arcminute in planet and Lagna longitude.

## Findings
- Largest differences: 56", 21" and 30" for the three charts.
- Our ayanamsa is "True Chitra Paksha" (23.8212 deg in 1998); JHora's shows 23-49-06.71.
- Cause of the remaining difference is not established. Hypothesis, untested: how each
  program applies apparent-position corrections.
- A difference of 43" put Saturn on opposite sides of the Ashwini pada 1/2 boundary
  (3 deg 20') in chart 1.
- Dasha balance at birth differs by about 9 days (2.5555 y vs ~2.58 y); lord matches.

## Consequences
- Tests must compare with a tolerance, not exact equality.
- Text that depends on the pada must handle positions near a pada boundary.
- Always use identical birth time (seconds included) when comparing with other software.
- Dasha end dates to be compared in Phase 2.