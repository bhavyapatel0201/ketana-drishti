import glob
import json

import pytest

from ketana_drishti.facts import build_facts

PATHS = sorted(glob.glob("tests/fixtures/*.json"))
KNOWN_DIGNITIES = {"exalted", "debilitated", "own_sign", "moolatrikona", "neutral"}


def load(p):
    return json.load(open(p, encoding="utf-8"))


def by_id(facts):
    return {f.id: f for f in facts}


@pytest.mark.parametrize("path", PATHS)
def test_every_planet_has_house_sign_and_nakshatra(path):
    chart = load(path)
    facts = by_id(build_facts(chart))
    for h in chart["d1Chart"]["houses"]:
        for o in h.get("occupants", []):
            key = o["celestialBody"].lower()
            assert facts[f"{key}.house"].values["house"] == o["house"]
            assert facts[f"{key}.sign"].values["sign"] == o["sign"]
            assert f"{key}.nakshatra" in facts


@pytest.mark.parametrize("path", PATHS)
def test_retrograde_facts_match_chart(path):
    chart = load(path)
    facts = by_id(build_facts(chart))
    for h in chart["d1Chart"]["houses"]:
        for o in h.get("occupants", []):
            body = o["celestialBody"]
            key = body.lower()
            expected = body not in ("Rahu", "Ketu") and o.get("motion_type") == "retrograde"
            assert (f"{key}.retrograde" in facts) == expected


@pytest.mark.parametrize("path", PATHS)
def test_dignity_facts_use_known_words(path):
    chart = load(path)
    facts = by_id(build_facts(chart))
    for h in chart["d1Chart"]["houses"]:
        for o in h.get("occupants", []):
            key = o["celestialBody"].lower()
            d = o.get("dignities", {}).get("dignity")
            if d:
                assert d in KNOWN_DIGNITIES
                assert facts[f"{key}.dignity"].values["dignity"] == d
                assert "_" not in facts[f"{key}.dignity"].text


@pytest.mark.parametrize("path", PATHS)
def test_every_fact_points_to_a_real_path(path):
    chart = load(path)
    for f in build_facts(chart):
        node = chart
        for part in f.source.replace("]", "").replace("[", ".").split("."):
            node = node[int(part)] if part.isdigit() else node[part]
        assert node is not None