import datetime as dt
import glob
import json
from dataclasses import dataclass, field

import pytest

from ketana_drishti.classic import classic_payload
from ketana_drishti.reading import check
from ketana_drishti.retrieval import load_corpus, retrieve

CORPUS = load_corpus()


@dataclass
class F:
    id: str
    text: str
    values: dict = field(default_factory=dict)


FACTS = [
    F("rahu.sign", "Rahu is in Leo", {"sign": "Leo"}),
    F("sun.sign", "Sun is in Aries", {"sign": "Aries"}),
    F("mars.sign", "Mars is in Aries", {"sign": "Aries"}),
    F("moon.sign", "Moon is in Scorpio", {"sign": "Scorpio"}),
    F("moon.house", "Moon is in house 6", {"house": 6}),
    F("moon.dignity", "Moon is debilitated", {"dignity": "debilitated"}),
    F("sun.dignity", "Sun is neutral (no special dignity)", {"dignity": "neutral"}),
    F("lagna.sign", "Lagna (ascendant) is Gemini", {"sign": "Gemini"}),
    F("dasha.mahadasha", "Running Mahadasha as of 2026-11-16: Venus, 2007-12-15 to 2027-12-14", {"planet": "Venus"}),
    F("dasha.balance", "Dasha balance at birth: Mercury, 2.59 years remaining", {"planet": "Mercury"}),
    F("rahu.aspect.saturn", "Rahu aspects Saturn (9th aspect)"),
]


def build():
    passages = retrieve(FACTS, CORPUS)
    return classic_payload(FACTS, passages), passages


def test_every_statement_cites_a_fact_and_passes_the_checker():
    payload, passages = build()
    valid, problems = check(payload, FACTS, passages)
    assert not problems and len(valid) == len(payload["statements"]) >= 5


def test_order_lagna_then_moon_then_sun_then_dasha():
    payload, _ = build()
    ids = [s["fact_ids"][0] for s in payload["statements"]]
    assert ids[0] == "lagna.sign"
    assert ids.index("moon.sign") < ids.index("sun.sign") < ids.index("dasha.mahadasha")


def test_statement_joins_fact_and_passage_text():
    payload, _ = build()
    moon = [s for s in payload["statements"] if s["fact_ids"] == ["moon.sign"]][0]
    assert moon["text"].startswith("Moon is in Scorpio.")
    assert "traditionally associated with the mind" in moon["text"]
    assert "planet.moon" in moon["passage_ids"]


def test_repeated_passage_is_not_repeated_in_text():
    payload, _ = build()
    mars = [s for s in payload["statements"] if s["fact_ids"] == ["mars.sign"]][0]
    assert "Mars is traditionally associated with energy" in mars["text"]
    assert "See also the note on Aries above" in mars["text"]
    assert "fixed fire" not in mars["text"] and "cardinal fire" not in mars["text"]
    assert "sign.aries" in mars["passage_ids"] and "planet.mars" in mars["passage_ids"]


def test_balance_and_neutral_dignity_are_skipped():
    payload, _ = build()
    ids = {i for s in payload["statements"] for i in s["fact_ids"]}
    assert "dasha.balance" not in ids and "sun.dignity" not in ids


def test_aspects_are_summarised_in_one_statement():
    payload, _ = build()
    asp = [s for s in payload["statements"] if s["fact_ids"] == ["rahu.aspect.saturn"]]
    assert len(asp) == 1 and "Rahu aspects Saturn" in asp[0]["text"]


def test_is_deterministic():
    a, _ = build()
    b, _ = build()
    assert a == b


@pytest.mark.parametrize("path", sorted(glob.glob("tests/fixtures/chart*.json")))
def test_real_charts_give_a_clean_classic_reading(path):
    from ketana_drishti.facts import build_facts
    chart = json.load(open(path, encoding="utf-8"))
    facts = build_facts(chart, dt.date(2026, 11, 16))
    passages = retrieve(facts, CORPUS)
    payload = classic_payload(facts, passages)
    valid, problems = check(payload, facts, passages)
    assert not problems and len(valid) >= 15
