from datetime import datetime

from jyotishganit import calculate_birth_chart, get_birth_chart_json

from .geo import geocode, utc_offset_hours


def build_chart(when: datetime, place: str | None = None,
                lat: float | None = None, lon: float | None = None,
                name: str | None = None) -> dict:
    """Return the full Vedic birth chart as a JSON-ready dict."""
    if lat is None or lon is None:
        if not place:
            raise ValueError("Provide a place or lat/lon")
        lat, lon = geocode(place)
    tz_name, offset = utc_offset_hours(lat, lon, when)
    chart = calculate_birth_chart(when, lat, lon, offset,
                                  location_name=place, name=name)
    data = get_birth_chart_json(chart)
    data["_input"] = {"datetime": when.isoformat(), "lat": lat, "lon": lon,
                      "timezone": tz_name, "utc_offset_hours": offset}
    return data
