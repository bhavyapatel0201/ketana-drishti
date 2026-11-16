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
