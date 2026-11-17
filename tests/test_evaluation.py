import copy
import datetime as dt
import glob
import json
from dataclasses import dataclass, field

import pytest

from ketana_drishti.evaluation import (
    adversarial_payloads, check, evaluate_chart, resolve, trace_problems,
)
from ketana_drishti.facts import build_facts
from ketana_drishti.retrieval import load_corpus

AS_OF = dt.date(2026, 11, 16)
FIXTURES = sorted(glob.glob("tests/fixtures/chart*.json"))


def test_resolve_follows_paths():
    chart = {"a": {"b": [{"c": 1}, {"c": 2}]}}
    assert resolve(chart, "a.b[1].c") == 2
    with pytest.raises(KeyError):
        resolve(chart, "a.nope")
    with pytest.raises(KeyError):
        resolve(chart, "a.b[1]..c")


@pytest.mark.parametrize("path", FIXTURES)
def test_every_fact_traces_to_the_chart(path):
    chart = json.load(open(path, encoding="utf-8"))
    for f in build_facts(chart, AS_OF):
        assert trace_problems(chart, f) == [], f.id


@pytest.mark.parametrize("path", FIXTURES)
def test_tampered_chart_is_detected(path):
    chart = json.load(open(path, encoding="utf-8"))
    facts = build_facts(chart, AS_OF)
    tampered = copy.deepcopy(chart)
    tampered["d1Chart"]["houses"][0]["sign"] = "Nonexistent"
    assert any(trace_problems(tampered, f) for f in facts if f.id == "lagna.sign")


@pytest.mark.parametrize("path", FIXTURES)
def test_full_evaluation_passes_on_fixtures(path):
    chart = json.load(open(path, encoding="utf-8"))
    r = evaluate_chart(chart, AS_OF)
    assert r.ok, (r.trace, r.gaps, r.checker_missed, r.deterministic, r.pipeline_ok)


@dataclass
class F:
    id: str
    text: str = ""
    values: dict = field(default_factory=dict)


def test_every_adversarial_reading_is_rejected():
    facts = [F("moon.sign", "x")]
    class P:  # noqa
        id = "planet.moon"
    for label, payload in adversarial_payloads(facts, [P()]):
        assert not check(payload, facts, [P()])[0], label
