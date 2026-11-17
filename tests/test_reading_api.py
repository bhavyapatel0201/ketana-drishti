import pytest
from fastapi.testclient import TestClient

from ketana_drishti import api
from ketana_drishti.llm import FakeClient, LLMError

client = TestClient(api.app)
FACTS = [{"id": "moon.sign", "text": "The Moon is in Scorpio.", "values": {"sign": "Scorpio"}},
         {"id": "lagna.sign", "text": "The Lagna is Gemini."}]


def post(**over):
    body = {"facts": FACTS, "language": "en", "mode": "ai", **over}
    return client.post("/api/reading", json=body)


def test_demo_mode_needs_no_key(monkeypatch):
    monkeypatch.setenv("KETANA_DEMO", "1")
    r = post()
    assert r.status_code == 200
    d = r.json()
    assert d["demo"] is True and d["statements"]
    assert d["statements"][0]["fact_ids"] == ["moon.sign"]
    assert "not medical" in d["disclaimer"]


def test_real_path_uses_client_and_checks(monkeypatch):
    monkeypatch.delenv("KETANA_DEMO", raising=False)
    fake = FakeClient([{"statements": [{"text": "Thoughtful.", "fact_ids": ["moon.sign"]}]}])
    monkeypatch.setattr(api, "make_client", lambda facts, passages=None: fake)
    r = post(question="my mind")
    assert r.status_code == 200 and r.json()["demo"] is False
    assert "my mind" in fake.calls[0]["user"]


def test_uncited_answer_is_rejected(monkeypatch):
    monkeypatch.delenv("KETANA_DEMO", raising=False)
    bad = {"statements": [{"text": "Invented.", "fact_ids": ["nope"]}]}
    monkeypatch.setattr(api, "make_client", lambda facts, passages=None: FakeClient([bad, bad]))
    assert post().status_code == 502


def test_llm_failure_is_503_with_message(monkeypatch):
    monkeypatch.delenv("KETANA_DEMO", raising=False)

    def boom(facts, passages=None):
        raise LLMError("Your credit balance is too low")

    monkeypatch.setattr(api, "make_client", boom)
    r = post()
    assert r.status_code == 503 and "credit balance" in r.json()["detail"]


def test_bad_language_and_empty_facts():
    assert post(language="fr").status_code == 400
    assert client.post("/api/reading", json={"facts": []}).status_code == 422


def test_demo_reading_returns_passages(monkeypatch):
    monkeypatch.setenv("KETANA_DEMO", "1")
    d = post().json()
    ids = [p["id"] for p in d["passages"]]
    assert "planet.moon" in ids or "sign.scorpio" in ids
    assert d["statements"][0]["passage_ids"]
    assert all(p["because"] for p in d["passages"])


def test_default_mode_is_classic_and_needs_no_model(monkeypatch):
    monkeypatch.delenv("KETANA_DEMO", raising=False)

    def boom(*a, **k):
        raise AssertionError("classic mode must not create a model client")

    monkeypatch.setattr(api, "make_client", boom)
    r = client.post("/api/reading", json={"facts": FACTS, "language": "en"})
    assert r.status_code == 200
    d = r.json()
    assert d["mode"] == "classic" and d["model"] == "" and d["demo"] is False
    assert d["statements"][0]["fact_ids"] and "not medical" in d["disclaimer"]


def test_classic_in_hindi_and_gujarati():
    for lang, word in (("hi", "क्लासिक"), ("gu", "ક્લાસિક")):
        r = client.post("/api/reading", json={"facts": FACTS, "language": lang})
        d = r.json()
        assert r.status_code == 200 and d["language"] == lang and word in d["note"]
        assert d["disclaimer"] != "" and "not medical" not in d["disclaimer"]
        assert "Moon is in" not in d["statements"][0]["text"] + d["statements"][-1]["text"]


def test_bad_mode_is_rejected():
    assert client.post("/api/reading", json={"facts": FACTS, "mode": "magic"}).status_code == 400


def test_health_reports_ai_availability(monkeypatch):
    monkeypatch.delenv("KETANA_DEMO", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert client.get("/api/health").json()["ai"] is False
    monkeypatch.setenv("KETANA_DEMO", "1")
    assert client.get("/api/health").json()["ai"] is True


def test_classic_keeps_every_planet_passage_even_for_a_full_chart():
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius"]
    facts = [{"id": "lagna.sign", "text": "Lagna is Gemini", "values": {"sign": "Gemini"}}]
    for pl, sg in zip(planets, signs):
        facts.append({"id": f"{pl.lower()}.sign", "text": f"{pl} is in {sg}", "values": {"sign": sg}})
        facts.append({"id": f"{pl.lower()}.nakshatra", "text": f"{pl} is in Ashwini, pada 1", "values": {"nakshatra": "Ashwini"}})
        facts.append({"id": f"{pl.lower()}.house", "text": f"{pl} is in house 3", "values": {"house": 3}})
    d = client.post("/api/reading", json={"facts": facts, "language": "en"}).json()
    got = {p["id"] for p in d["passages"]}
    for pl in planets:
        assert f"planet.{pl.lower()}" in got, pl
    text = " ".join(s["text"] for s in d["statements"])
    assert "(See also the note on house 3 above.)" in text
