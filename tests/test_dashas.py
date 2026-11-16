import glob
import json
from datetime import date, datetime, time

import pytest

from ketana_drishti.dasha import YEAR_DAYS, birth_datetime, mahadashas, running
from ketana_drishti.facts import build_facts

PATHS = sorted(glob.glob("tests/fixtures/*.json"))

# Mahadasha dates for chart 1 as shown by Jagannatha Hora (tropical years)
JHORA_CHART1 = [
    ("Mercury", "1983-12-15", "2000-12-14"),
    ("Ketu", "2000-12-14", "2007-12-14"),
    ("Venus", "2007-12-14", "2027-12-14"),
    ("Sun", "2027-12-14", "2033-12-14"),
    ("Moon", "2033-12-14", "2043-12-14"),
    ("Mars", "2043-12-14", "2050-12-14"),
    ("Rahu", "2050-12-14", "2068-12-13"),
    ("Jupiter", "2068-12-13", "2084-12-13"),
    ("Saturn", "2084-12-13", "2103-12-15"),
]


def load(p):
    return json.load(open(p, encoding="utf-8"))


def by_id(facts):
    return {f.id: f for f in facts}


def resolve(chart, source):
    node = chart
    for part in source.replace("]", "").replace("[", ".").split("."):
        node = node[int(part)] if part.isdigit() else node[part]
    return node


def days_apart(d, iso):
    return abs((d - date.fromisoformat(iso)).days)


def test_chart1_matches_jhora_within_a_day():
    lord, balance, mds = mahadashas(load("tests/fixtures/chart1.json"))
    assert lord == "Mercury"
    assert abs(balance - 2.5875) < 0.001
    for p, (name, start, end) in zip(mds, JHORA_CHART1):
        assert p["lord"] == name
        assert days_apart(p["start"].date(), start) <= 1, (name, "start")
        assert days_apart(p["end"].date(), end) <= 1, (name, "end")


@pytest.mark.parametrize("path", PATHS)
def test_mahadashas_are_contiguous_and_cover_birth(path):
    chart = load(path)
    _, _, mds = mahadashas(chart)
    assert len(mds) == 9
    for a, b in zip(mds, mds[1:]):
        assert a["end"] == b["start"]
    total_days = (mds[-1]["end"] - mds[0]["start"]).total_seconds() / 86400
    assert abs(total_days - 120 * YEAR_DAYS) < 0.01
    assert mds[0]["start"] <= birth_datetime(chart) < mds[0]["end"]


@pytest.mark.parametrize("path", PATHS)
def test_running_periods_nest_and_contain_the_date(path):
    chart = load(path)
    as_of = date(2026, 11, 16)
    moment = datetime.combine(as_of, time.min)
    chain = running(chart, as_of)
    assert len(chain) == 3
    for p in chain:
        assert p["start"] <= moment < p["end"]
    for outer, inner in zip(chain, chain[1:]):
        assert inner["start"] >= outer["start"]
        assert (outer["end"] - inner["end"]).total_seconds() > -1


def test_no_running_dasha_without_as_of():
    facts = by_id(build_facts(load("tests/fixtures/chart1.json")))
    assert "dasha.balance" in facts
    assert "dasha.mahadasha" not in facts


def test_chart1_running_dasha_2001_01_01():
    facts = by_id(build_facts(load("tests/fixtures/chart1.json"), date(2001, 1, 1)))
    assert facts["dasha.mahadasha"].values["planet"] == "Ketu"
    assert days_apart(date.fromisoformat(facts["dasha.mahadasha"].values["end"]), "2007-12-14") <= 1
    assert facts["dasha.antardasha"].values["planet"] == "Ketu"
    assert facts["dasha.pratyantardasha"].values["planet"] == "Venus"


@pytest.mark.parametrize("path", PATHS)
def test_dasha_facts_point_to_the_moon(path):
    chart = load(path)
    facts = [f for f in build_facts(chart, date(2026, 11, 16)) if f.id.startswith("dasha.")]
    assert len(facts) == 4
    for f in facts:
        assert resolve(chart, f.source)["celestialBody"] == "Moon"