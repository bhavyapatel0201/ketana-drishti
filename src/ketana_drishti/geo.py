from datetime import datetime
from zoneinfo import ZoneInfo

from timezonefinder import TimezoneFinder


def geocode(place: str) -> tuple[float, float]:
    """Look up latitude/longitude for a place name (needs internet)."""
    from geopy.geocoders import Nominatim

    loc = Nominatim(user_agent="ketana-drishti-learning").geocode(place)
    if loc is None:
        raise ValueError(f"Could not geocode place: {place!r}")
    return loc.latitude, loc.longitude


def utc_offset_hours(lat: float, lon: float, when: datetime) -> tuple[str, float]:
    """IANA timezone name and UTC offset (hours) at the birth moment, DST-aware."""
    tz_name = TimezoneFinder().timezone_at(lat=lat, lng=lon)
    if tz_name is None:
        raise ValueError("Could not determine timezone for coordinates")
    offset = when.replace(tzinfo=ZoneInfo(tz_name)).utcoffset()
    return tz_name, offset.total_seconds() / 3600
