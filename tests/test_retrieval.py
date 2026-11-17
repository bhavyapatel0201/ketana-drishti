import glob
import json
import datetime as dt
from dataclasses import dataclass, field

import pytest

from ketana_drishti.reading import is_blocked
from ketana_drishti.retrieval import keys_for_fact, load_corpus, retrieve, unmatched


@dataclass
class F:
    id: str
    text: str = ""
    values: dict = field(default_factory=dict)


CORPUS = load_corpus()

NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
              "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
              "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
              "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
              "Uttara Bhadrapada", "Revati"]


def test_corpus_shape():
    assert len(CORPUS) == 75
    for p in CORPUS.by_id.values():
        assert p["text"].strip() and len(p["text"]) < 450
        assert p["id"].startswith(p["kind"] + ".")


def test_corpus_text_passes_the_reading_guardrail():
    # The model may quote passages, so they must not contain blocked topic words.
    for p in CORPUS.by_id.values():
        assert not is_blocked(p["text"]), p["id"]


@pytest.mark.parametrize("n", NAKSHATRAS)
def test_every_nakshatra_present(n):
    assert CORPUS.find("nakshatra", n)


def test_aliases_and_spelling_variants():
    assert CORPUS.find("nakshatra", "Jyestha") == CORPUS.find("nakshatra", "Jyeshtha")
    assert CORPUS.find("nakshatra", "purva-bhadrapada") == "nakshatra.purvabhadrapada"
    assert CORPUS.find("sign", "Mesha") == "sign.aries"


def test_keys_for_each_fact_kind():
    assert keys_for_fact(F("moon.sign", values={"sign": "Scorpio"})) == [("planet", "moon"), ("sign", "Scorpio")]
    assert keys_for_fact(F("lagna.sign", values={"sign": "Gemini"})) == [("concept", "lagna"), ("sign", "Gemini")]
    assert keys_for_fact(F("moon.house", values={"house": 6})) == [("house", 6)]
    assert keys_for_fact(F("moon.dignity", values={"dignity": "neutral"})) == []
    assert keys_for_fact(F("moon.dignity", values={"dignity": "debilitated"})) == [("dignity", "debilitated")]
    assert keys_for_fact(F("dasha.mahadasha", values={"planet": "Venus"})) == [("dasha", "Venus")]
    assert keys_for_fact(F("rahu.aspect.saturn")) == [("concept", "drishti")]


FACTS = [
    F("rahu.sign", values={"sign": "Leo"}),
    F("moon.sign", values={"sign": "Scorpio"}),
    F("moon.nakshatra", values={"nakshatra": "Jyeshtha"}),
    F("moon.house", values={"house": 6}),
    F("moon.dignity", values={"dignity": "debilitated"}),
    F("lagna.sign", values={"sign": "Gemini"}),
    F("dasha.mahadasha", values={"planet": "Venus"}),
    F("rahu.aspect.saturn"),
]


def test_retrieve_finds_expected_passages_with_reasons():
    got = {p.id: p for p in retrieve(FACTS, CORPUS)}
    for pid in ["planet.moon", "sign.scorpio", "nakshatra.jyeshtha", "house.6", "dignity.debilitated",
                "concept.lagna", "sign.gemini", "dasha.venus", "concept.drishti", "planet.rahu", "sign.leo"]:
        assert pid in got, pid
    assert got["nakshatra.jyeshtha"].because == ["moon.nakshatra"]


def test_priority_and_limit_and_determinism():
    out = retrieve(FACTS, CORPUS)
    ids = [p.id for p in out]
    assert ids[0] in ("concept.lagna", "sign.gemini")          # lagna facts first
    assert ids.index("planet.moon") < ids.index("planet.rahu")  # Moon before Rahu
    assert [p.id for p in retrieve(FACTS, CORPUS)] == ids
    assert len(retrieve(FACTS, CORPUS, limit=3)) == 3
    assert len({p.id for p in out}) == len(out)


def test_shared_passage_collects_all_reasons():
    facts = [F("sun.sign", values={"sign": "Aries"}), F("mars.sign", values={"sign": "Aries"})]
    aries = [p for p in retrieve(facts, CORPUS) if p.id == "sign.aries"][0]
    assert aries.because == ["sun.sign", "mars.sign"]


def test_unmatched_reports_spelling_gaps():
    bad = [F("moon.nakshatra", values={"nakshatra": "Nonexistentia"})]
    assert unmatched(bad, CORPUS) == [("moon.nakshatra", "nakshatra", "Nonexistentia")]
    assert retrieve(bad, CORPUS) == []


@pytest.mark.parametrize("path", sorted(glob.glob("tests/fixtures/chart*.json")))
def test_real_fixture_charts_have_no_spelling_gaps(path):
    from ketana_drishti.facts import build_facts
    chart = json.load(open(path, encoding="utf-8"))
    facts = build_facts(chart, dt.date(2026, 11, 16))
    assert unmatched(facts, CORPUS) == []
    assert len(retrieve(facts, CORPUS)) >= 10
