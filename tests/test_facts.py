import json
from pathlib import Path

from ketana_drishti.facts import build_facts

FIX = Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def by_id(facts):
    return {f.id: f for f in facts}


def test_chart1_lagna_and_moon():
    f = by_id(build_facts(load("chart1.json")))
    assert f["lagna.sign"].values["sign"] == "Gemini"
    assert f["moon.nakshatra"].values["nakshatra"] == "Jyeshtha"
    assert f["moon.nakshatra"].values["pada"] == 4
    assert f["moon.dignity"].values["dignity"] == "debilitated"


def test_chart3_saturn_retrograde():
    f = by_id(build_facts(load("chart3.json")))
    assert "saturn.retrograde" in f
    assert f["moon.sign"].values["sign"] == "Virgo"


def test_nodes_not_flagged_retrograde():
    f = by_id(build_facts(load("chart1.json")))
    assert "rahu.retrograde" not in f