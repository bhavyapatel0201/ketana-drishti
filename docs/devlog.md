## 2026-11-15 - Day 1 (continued): Cross-check against Jagannatha Hora
- Compared three made-up charts with JHora using identical inputs (JHora kept stray
  seconds of :21 in its time, so our CLI was run at the same second):
  1. Ahmedabad 1998-05-14 08:30:21 - largest difference 56" (Mars)
  2. Toronto 2020-07-15 09:00:21 - largest difference 21" (Sun)
  3. Sydney 2005-12-25 22:15:21 - largest difference 30" (Mercury)
- All 30 values agree on sign and Nakshatra; every difference is under 1 arcminute.
- Mistakes along the way: JHora time and time zone fields were swapped once; stray
  seconds in JHora caused a 227" Lagna gap until our CLI used the same time.
- Ayanamsa: ours is "True Chitra Paksha" (23.8212 deg in 1998); JHora shows 23-49-06.71.
- Pada boundary: in chart 1 a 43" difference put Saturn on opposite sides of the Ashwini
  pada 1/2 boundary (3 deg 20').
- Dasha check (chart 1): starting lord Mercury matches JHora. Balance at birth is 2.5555 y
  in ours vs ~2.58 y implied by JHora (15.18% of Jyeshtha left x 17). About 9 days apart;
  cause not established (year-length convention or balance calculation). To resolve in
  Phase 2 by comparing dasha end dates on JHora's Dasas tab.
- Added scripts/flatten.py and scripts/compare.py to inspect and print chart output.
- Unresolved: why Lagna/Moon/nodes differ by ~18" but planets by up to 56" in chart 1.