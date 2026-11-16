import glob
import json

import pytest

from ketana_drishti.facts import build_facts

PATHS = sorted(glob.glob("tests/fixtures/*.json"))


def load(p):
    return json.load(open(p, encoding="utf-8"))


def planets(chart):
    out = {}
    for h in chart["d1Chart"]["houses"]:
        for o in h.get("occupants", []):
            out[o["celestialBody"]] = o
    return out


@pytest.mark.parametrize("path", PATHS)
def test_every_library_aspect_becomes_a_fact(path):
    chart = load(path)
    expected = sum(
        len((o.get("aspects") or {}).get("gives", []))
        for o in planets(chart).values()
    )
    facts = [f for f in build_facts(chart) if ".aspect." in f.id]
    assert len(facts) == expected


@pytest.mark.parametrize("path", PATHS)
def test_aspect_number_matches_house_distance(path):
    chart = load(path)
    ps = planets(chart)
    for name, o in ps.items():
        for a in (o.get("aspects") or {}).get("gives", []):
            if "to_house" in a:
                target_house = a["to_house"]
            else:
                target_house = ps[a["to_planet"]]["house"]
            distance = (target_house - o["house"]) % 12 + 1
            assert distance == int(a["aspect_type"]), (name, a)


def test_chart1_rahu_aspects_saturn():
    facts = {f.id: f for f in build_facts(load("tests/fixtures/chart1.json"))}
    f = facts["rahu.aspect.saturn"]
    assert f.values["aspect"] == 9
    assert f.source.endswith("aspects.gives[0]")