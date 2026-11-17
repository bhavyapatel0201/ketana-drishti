"""Place search for the birth-place box (type-ahead suggestions).

Uses the free Open-Meteo geocoding service: no key and no cost. The server makes the
request, so the browser never contacts a third party; only the text typed in the place
box is sent. If the service is unreachable the page falls back to plain typing, and
the chart can still be made from a place name or from latitude and longitude.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import httpx

log = logging.getLogger("ketana_drishti.places")
URL = "https://geocoding-api.open-meteo.com/v1/search"
MIN_CHARS, MAX_CHARS, TIMEOUT = 2, 80, 4.0


class PlacesUnavailable(Exception):
    """The place service could not be reached or gave an unusable answer."""


def _get(query: str, limit: int) -> dict:
    r = httpx.get(URL, params={"name": query, "count": limit, "language": "en", "format": "json"},
                  timeout=TIMEOUT, headers={"User-Agent": "ketana-drishti/0.5 (open source)"})
    r.raise_for_status()
    return r.json()


def label(item: dict) -> str:
    parts = [item.get("name"), item.get("admin1"), item.get("country")]
    out: list = []
    for p in parts:
        if p and p not in out:
            out.append(p)
    return ", ".join(out)


def normalize(raw: dict) -> list[dict]:
    """Keep only usable results, in a small fixed shape."""
    results = []
    for it in raw.get("results") or []:
        try:
            lat, lon = float(it["latitude"]), float(it["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180) or not it.get("name"):
            continue
        results.append({"label": label(it), "lat": round(lat, 4), "lon": round(lon, 4),
                        "timezone": it.get("timezone") or "", "country": it.get("country") or ""})
    return results


@lru_cache(maxsize=256)
def _cached(query: str, limit: int) -> tuple:
    try:
        return tuple(normalize(_get(query, limit)))
    except (httpx.HTTPError, ValueError) as e:
        log.warning("place search failed: %s", type(e).__name__)
        raise PlacesUnavailable from e


def search_places(query: str, limit: int = 6) -> list[dict]:
    """Suggestions for `query`; [] for too-short text. Raises PlacesUnavailable on failure."""
    q = " ".join((query or "").split())[:MAX_CHARS]
    if len(q) < MIN_CHARS:
        return []
    return [dict(x) for x in _cached(q.lower(), max(1, min(limit, 10)))]
