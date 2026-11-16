"""Vimshottari dasha computed from the Moon's sidereal longitude.

Why not use the library's `dashas` block: its birth balance disagrees with its own
Moon longitude by -12 to +46 days (see ADR-0003). Computing it here from the Moon,
the birth time and a fixed year length reproduces Jagannatha Hora to within a day.
"""
from datetime import date, datetime, time, timedelta

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
         "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
         "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
SPAN = 360 / 27          # one nakshatra, in degrees
CYCLE = 120              # years in the full Vimshottari cycle
YEAR_DAYS = 365.2422     # tropical year; Jagannatha Hora's default


def find_moon(chart: dict):
    """Return (house index, occupant index, occupant) of the Moon in the D1 chart."""
    for i, h in enumerate(chart["d1Chart"]["houses"]):
        for j, o in enumerate(h.get("occupants", [])):
            if o["celestialBody"] == "Moon":
                return i, j, o
    raise ValueError("Moon not found in d1Chart")


def moon_longitude(moon: dict) -> float:
    return SIGNS.index(moon["sign"]) * 30 + float(moon["signDegrees"])


def birth_datetime(chart: dict) -> datetime:
    dt = datetime.fromisoformat(chart["_input"]["datetime"])
    return dt.replace(tzinfo=None)


def _children(parent_lord: str, start: datetime, length_days: float):
    """Split a period into 9 sub-periods, starting with the parent's own lord."""
    first = ORDER.index(parent_lord)
    out, t = [], start
    for k in range(9):
        lord = ORDER[(first + k) % 9]
        end = t + timedelta(days=length_days * YEARS[lord] / CYCLE)
        out.append({"lord": lord, "start": t, "end": end})
        t = end
    return out


def mahadashas(chart: dict, year_days: float = YEAR_DAYS):
    """Return (balance_lord, balance_years, [9 mahadashas])."""
    _, _, moon = find_moon(chart)
    lon = moon_longitude(moon)
    idx = int(lon // SPAN)
    frac = (lon - idx * SPAN) / SPAN
    lord = ORDER[idx % 9]
    balance = (1 - frac) * YEARS[lord]
    t = birth_datetime(chart) - timedelta(days=frac * YEARS[lord] * year_days)
    periods = []
    for k in range(9):
        name = ORDER[(idx % 9 + k) % 9]
        end = t + timedelta(days=YEARS[name] * year_days)
        periods.append({"lord": name, "start": t, "end": end})
        t = end
    return lord, balance, periods


def running(chart: dict, as_of: date, year_days: float = YEAR_DAYS):
    """Return [mahadasha, antardasha, pratyantardasha] containing as_of (may be shorter)."""
    _, _, periods = mahadashas(chart, year_days)
    moment = datetime.combine(as_of, time.min)
    chain = []
    level = periods
    for _ in range(3):
        hit = next((p for p in level if p["start"] <= moment < p["end"]), None)
        if hit is None:
            break
        chain.append(hit)
        length = (hit["end"] - hit["start"]).total_seconds() / 86400
        level = _children(hit["lord"], hit["start"], length)
    return chain