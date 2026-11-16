# Changelog

All notable changes to this project are documented here.
Format based on Keep a Changelog; versions follow Semantic Versioning.

## [0.1.0] - 2026-11-15

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