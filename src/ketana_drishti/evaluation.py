"""Evaluation: does every claim trace back to the chart or to a retrieved passage?

Per chart it checks:
 1. trace      - each fact's `source` resolves in the chart JSON and the fact's
                 values agree with the node it points at (sign, house, nakshatra,
                 dignity, planet);
 2. retrieval  - no fact key lacks a passage, enough passages come back, and the
                 result is identical on a second run;
 3. checker    - a good scripted reading is accepted, and every bad one (unknown
                 id, no fact id, passage only, blocked topic, empty text) is rejected;
 4. pipeline   - generate_reading accepts the good reading end to end;
 5. classic    - the no-model classic reading passes the same checker and is repeatable.
Nothing here calls a real model, so it is free and repeatable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .classic import classic_payload
from .facts import build_facts
from .llm import FakeClient
from .reading import ReadingError, check, generate_reading
from .retrieval import load_corpus, retrieve, unmatched

_STEP = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(?:\[(\d+)\])?$")


def resolve(chart, path: str):
    """Follow a path like d1Chart.houses[2].occupants[0] into the chart JSON."""
    node = chart
    for part in path.split("."):
        m = _STEP.match(part)
        if not m:
            raise KeyError(f"bad path step: {part}")
        node = node[m.group(1)]
        if m.group(2) is not None:
            node = node[int(m.group(2))]
    return node


def _dignity(node):
    d = node.get("dignities")
    return d.get("dignity") if isinstance(d, dict) else None


def trace_problems(chart, fact) -> list:
    """Why this fact does not agree with the chart at its source (empty list = fine)."""
    try:
        node = resolve(chart, fact.source)
    except (KeyError, IndexError, TypeError) as e:
        return [f"{fact.id}: source {fact.source} does not resolve ({type(e).__name__})"]
    v = fact.values or {}
    head = fact.id.split(".")[0]
    out = []
    if head == "dasha":
        if node.get("celestialBody") != "Moon":
            out.append(f"{fact.id}: source is not the Moon")
        return out
    if ".aspect." in fact.id:
        return out
    if head != "lagna" and node.get("celestialBody", "").lower() != head:
        out.append(f"{fact.id}: source node is {node.get('celestialBody')}, expected {head}")
    for key, got in (("sign", node.get("sign")), ("nakshatra", node.get("nakshatra")),
                     ("pada", node.get("pada")), ("dignity", _dignity(node))):
        if key in v and got is not None and v[key] != got:
            out.append(f"{fact.id}: {key} {v[key]!r} differs from chart {got!r}")
    if "house" in v and node.get("house") is not None and v["house"] != node["house"]:
        out.append(f"{fact.id}: house {v['house']!r} differs from chart {node['house']!r}")
    return out


def adversarial_payloads(facts, passages) -> list:
    """Bad readings the checker must reject. Each is (label, payload)."""
    fid = facts[0].id
    pid = passages[0].id if passages else "planet.moon"
    return [
        ("unknown fact id", {"statements": [{"text": "A claim.", "fact_ids": ["nope.nope"]}]}),
        ("no fact id", {"statements": [{"text": "A claim.", "fact_ids": []}]}),
        ("passage only", {"statements": [{"text": "A claim.", "fact_ids": [], "passage_ids": [pid]}]}),
        ("unknown passage id", {"statements": [{"text": "A claim.", "fact_ids": [fid], "passage_ids": ["nope.nope"]}]}),
        ("blocked topic", {"statements": [{"text": "You will marry soon.", "fact_ids": [fid]}]}),
        ("empty text", {"statements": [{"text": " ", "fact_ids": [fid]}]}),
        ("no statements", {"statements": []}),
    ]


@dataclass
class ChartResult:
    facts: int = 0
    passages: int = 0
    trace: list = None
    gaps: list = None
    checker_missed: list = None
    deterministic: bool = False
    pipeline_ok: bool = False
    classic_ok: bool = False

    @property
    def ok(self) -> bool:
        return (not self.trace and not self.gaps and not self.checker_missed
                and self.deterministic and self.pipeline_ok and self.classic_ok
                and self.passages >= 10)


def evaluate_chart(chart, as_of, corpus=None) -> ChartResult:
    corpus = corpus or load_corpus()
    facts = build_facts(chart, as_of)
    r = ChartResult(facts=len(facts))
    r.trace = [p for f in facts for p in trace_problems(chart, f)]
    r.gaps = unmatched(facts, corpus)
    passages = retrieve(facts, corpus)
    r.passages = len(passages)
    r.deterministic = [p.id for p in passages] == [p.id for p in retrieve(facts, corpus)]
    r.checker_missed = [label for label, payload in adversarial_payloads(facts, passages)
                        if check(payload, facts, passages)[0]]
    good_fact = facts[0]
    good_passage = next((p for p in passages if good_fact.id in p.because), None)
    good = {"statements": [{"text": "A grounded statement.", "fact_ids": [good_fact.id],
                            "passage_ids": [good_passage.id] if good_passage else []}]}
    try:
        reading = generate_reading(FakeClient([good]), facts, passages=passages)
        r.pipeline_ok = len(reading.statements) == 1 and not reading.retried
    except ReadingError:
        r.pipeline_ok = False
    payload = classic_payload(facts, passages)
    valid, problems = check(payload, facts, passages)
    r.classic_ok = bool(valid) and not problems and payload == classic_payload(facts, passages)
    return r
