import glob
import json
from datetime import date

import pytest

from ketana_drishti.facts import build_facts

PATHS = sorted(glob.glob("tests/fixtures/*.json"))


def load(p):
    return json.load(open(p, encoding="utf-8"))


def by_id(facts):
    return {f.id: f for f in facts}


def resolve(chart, source):
    node = chart
    for part in source.replace("]", "").replace("[", ".").split("."):
        node = node[int(part)] if part.isdigit() else node[part]
    return node


@pytest.mark.parametrize("path", PATHS)
def test_balance_fact_matches_chart(path):
    chart = load(path)
    f = by_id(build_facts(chart))["dasha.balance"]
    assert f.values["years"] == chart["dashas"]["balance"][f.values["planet"]]


def test_no_running_dasha_without_as_of():
    facts = by_id(build_facts(load("tests/fixtures/chart1.json")))
    assert "dasha.mahadasha" not in facts


def test_chart1_running_dasha_2001_01_01():
    facts = by_id(build_facts(load("tests/fixtures/chart1.json"), date(2001, 1, 1)))
    assert facts["dasha.mahadasha"].values["planet"] == "Ketu"
    assert facts["dasha.mahadasha"].values["end"] == "2007-12-03"
    assert facts["dasha.antardasha"].values["planet"] == "Ketu"
    assert facts["dasha.pratyantardasha"].values["planet"] == "Venus"


@pytest.mark.parametrize("path", PATHS)
def test_running_dashas_contain_the_date_and_have_real_sources(path):
    chart = load(path)
    as_of = date(2026, 11, 16)
    facts = by_id(build_facts(chart, as_of))
    for fid in ("dasha.mahadasha", "dasha.antardasha", "dasha.pratyantardasha"):
        f = facts[fid]
        assert date.fromisoformat(f.values["start"]) <= as_of < date.fromisoformat(f.values["end"])
        node = resolve(chart, f.source)
        assert node["start"] == f.values["start"]
        assert node["end"] == f.values["end"]