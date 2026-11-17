import httpx
import pytest
from fastapi.testclient import TestClient

from ketana_drishti import api, places

client = TestClient(api.app)
RAW = {"results": [
    {"name": "Ahmedabad", "admin1": "Gujarat", "country": "India", "latitude": 23.02579, "longitude": 72.58727,
     "timezone": "Asia/Kolkata"},
    {"name": "Delhi", "admin1": "Delhi", "country": "India", "latitude": 28.65, "longitude": 77.23},
    {"name": "Bad", "latitude": 99, "longitude": 10},
    {"name": "NoCoords"},
    {"latitude": 1, "longitude": 1},
]}


@pytest.fixture(autouse=True)
def fresh_cache():
    places._cached.cache_clear()
    yield
    places._cached.cache_clear()


def test_normalize_keeps_only_usable_results():
    out = places.normalize(RAW)
    assert [r["label"] for r in out] == ["Ahmedabad, Gujarat, India", "Delhi, India"]
    assert out[0]["lat"] == 23.0258 and out[0]["timezone"] == "Asia/Kolkata"
    assert places.normalize({}) == []


def test_short_or_blank_query_makes_no_request(monkeypatch):
    monkeypatch.setattr(places, "_get", lambda *a: pytest.fail("should not be called"))
    assert places.search_places("a") == [] and places.search_places("   ") == []


def test_search_is_cached_and_limit_clamped(monkeypatch):
    calls = []
    monkeypatch.setattr(places, "_get", lambda q, n: calls.append((q, n)) or RAW)
    places.search_places("Ahmedabad", 99); places.search_places("  ahmedabad ", 99)
    assert calls == [("ahmedabad", 10)]


def test_service_failure_raises_unavailable(monkeypatch):
    def boom(*a):
        raise httpx.ConnectError("down")
    monkeypatch.setattr(places, "_get", boom)
    with pytest.raises(places.PlacesUnavailable):
        places.search_places("Ahmedabad")


def test_api_returns_results_and_degrades_quietly(monkeypatch):
    monkeypatch.setattr(places, "_get", lambda q, n: RAW)
    d = client.get("/api/places", params={"q": "Ahmed"}).json()
    assert d["unavailable"] is False and len(d["results"]) == 2

    def boom(*a):
        raise httpx.ConnectError("down")
    places._cached.cache_clear()
    monkeypatch.setattr(places, "_get", boom)
    r = client.get("/api/places", params={"q": "Ahmed"})
    assert r.status_code == 200 and r.json() == {"results": [], "unavailable": True}


def test_api_validates_input():
    assert client.get("/api/places", params={"q": "x" * 200}).status_code == 422
    assert client.get("/api/places", params={"q": "ab", "limit": 50}).status_code == 422
    assert client.get("/api/places").json()["results"] == []
