import json

import pytest
from fastapi.testclient import TestClient

import ketana_drishti.api as api


def chart1():
    with open("tests/fixtures/chart1.json", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api, "build_chart",
                        lambda when, place=None, lat=None, lon=None, name=None: chart1())
    return TestClient(api.app)


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_chart_returns_chart_and_facts(client):
    r = client.post("/api/chart", json={"datetime": "1998-05-14T08:30:21",
                                        "place": "Ahmedabad, India", "as_of": "2001-01-01"})
    assert r.status_code == 200
    data = r.json()
    assert "d1Chart" in data["chart"]
    facts = {f["id"]: f for f in data["facts"]}
    assert facts["lagna.sign"]["values"]["sign"] == "Gemini"
    assert facts["dasha.mahadasha"]["values"]["planet"] == "Ketu"
    assert facts["dasha.pratyantardasha"]["values"]["planet"] == "Venus"


def test_coordinates_instead_of_place(client):
    r = client.post("/api/chart", json={"datetime": "1998-05-14T08:30:21", "lat": 23.03, "lon": 72.58})
    assert r.status_code == 200


@pytest.mark.parametrize("body", [
    {"datetime": "1998-05-14T08:30:21"},                          # no place or coordinates
    {"datetime": "1998-05-14T08:30:21", "lat": 95, "lon": 10},    # latitude out of range
    {"datetime": "1998-05-14T08:30:21", "lat": 10},               # longitude missing
])
def test_invalid_input_is_rejected(client, body):
    assert client.post("/api/chart", json=body).status_code == 422


@pytest.mark.parametrize("when", ["not-a-date", "1850-01-01T00:00:00", "2999-01-01T00:00:00"])
def test_bad_birth_moment_is_rejected(client, when):
    r = client.post("/api/chart", json={"datetime": when, "place": "Anywhere"})
    assert r.status_code == 400


def test_unknown_place_gives_a_helpful_error(monkeypatch):
    def boom(*a, **k):
        raise ValueError("geocode failed")
    monkeypatch.setattr(api, "build_chart", boom)
    r = TestClient(api.app).post("/api/chart", json={"datetime": "1998-05-14T08:30:21", "place": "Nowhereville"})
    assert r.status_code == 400
    assert "latitude and longitude" in r.json()["detail"]


def test_page_is_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Ketana Drishti" in r.text
