from dataclasses import dataclass

import pytest

from ketana_drishti.llm import FakeClient
from ketana_drishti.reading import (
    DISCLAIMER, TOOL, ReadingError, build_system, build_user,
    check, generate_reading, render,
)


@dataclass
class F:
    id: str
    text: str


FACTS = [
    F("lagna.sign", "The Lagna (Ascendant) is Gemini."),
    F("moon.sign", "The Moon is in Scorpio."),
    F("moon.dignity", "The Moon is debilitated."),
]


def good(*ids, text="Your mind is sensitive and thoughtful."):
    return {"statements": [{"text": text, "fact_ids": list(ids)}]}


def test_prompt_has_only_ids_and_text():
    u = build_user(FACTS, "Tell me about my mind")
    assert "[moon.sign] The Moon is in Scorpio." in u
    assert "Tell me about my mind" in u
    assert "source" not in u.lower()


def test_system_prompt_languages_and_rules():
    assert "Hindi" in build_system("hi")
    assert "Gujarati" in build_system("gu")
    assert "Use only the facts and passages" in build_system("en")
    with pytest.raises(ReadingError):
        build_system("fr")


def test_tool_schema_requires_fact_ids():
    item = TOOL["input_schema"]["properties"]["statements"]["items"]
    assert "fact_ids" in item["required"]
    assert item["properties"]["fact_ids"]["minItems"] == 1


def test_check_accepts_valid():
    valid, problems = check(good("moon.sign"), FACTS)
    assert len(valid) == 1 and not problems


@pytest.mark.parametrize("payload,word", [
    ({"statements": [{"text": "x", "fact_ids": []}]}, "no fact id"),
    ({"statements": [{"text": "x", "fact_ids": ["nope"]}]}, "unknown"),
    ({"statements": [{"text": "", "fact_ids": ["moon.sign"]}]}, "empty"),
    ({"statements": []}, "no statements"),
    (None, "no statements"),
    ({"statements": [{"text": "You may marry soon.", "fact_ids": ["moon.sign"]}]}, "not allowed"),
    ({"statements": [{"text": "Risk of cancer.", "fact_ids": ["moon.sign"]}]}, "not allowed"),
])
def test_check_rejects(payload, word):
    valid, problems = check(payload, FACTS)
    assert not valid and any(word in p for p in problems)


def test_generate_happy_path_no_retry():
    c = FakeClient([good("moon.sign", "moon.dignity")])
    r = generate_reading(c, FACTS)
    assert not r.retried and r.disclaimer == DISCLAIMER
    assert len(c.calls) == 1 and c.calls[0]["tool"] is TOOL


def test_generate_retries_once_then_succeeds():
    c = FakeClient([good("made.up"), good("moon.sign")])
    r = generate_reading(c, FACTS)
    assert r.retried and len(c.calls) == 2
    assert "unknown fact id" in c.calls[1]["user"]


def test_generate_fails_after_second_bad_answer():
    c = FakeClient([good("made.up"), good("made.up")])
    with pytest.raises(ReadingError):
        generate_reading(c, FACTS)
    assert len(c.calls) == 2


def test_partial_answer_keeps_only_valid_statements():
    mixed = {"statements": [
        {"text": "Thoughtful nature.", "fact_ids": ["moon.sign"]},
        {"text": "Invented claim.", "fact_ids": ["nope"]},
    ]}
    c = FakeClient([mixed, mixed])
    r = generate_reading(c, FACTS)
    assert len(r.statements) == 1 and r.dropped == 1


def test_no_facts_raises():
    with pytest.raises(ReadingError):
        generate_reading(FakeClient([]), [])


def test_render_lists_citations_and_disclaimer():
    c = FakeClient([good("moon.sign")])
    r = generate_reading(c, FACTS)
    out = render(r, FACTS)
    assert "[moon.sign]" in out and "The Moon is in Scorpio." in out
    assert out.strip().endswith(DISCLAIMER)


@pytest.mark.parametrize("text,blocked", [
    ("The Moon is in Cancer, linked with care.", False),
    ("Mula is linked with investigation and uprooting.", False),
    ("Risk of cancer later.", True),
    ("A good time to invest in stocks.", True),
    ("An investment will pay off.", True),
    ("You may marry soon.", True),
])
def test_guardrail_allows_sign_cancer_and_investigation(text, blocked):
    from ketana_drishti.reading import is_blocked
    assert is_blocked(text) is blocked


# ---- passages (Phase 4) ----
@dataclass
class P:
    id: str
    text: str
    because: list = None


PASSAGES = [P("planet.moon", "The Moon is traditionally associated with the mind."),
            P("sign.scorpio", "Scorpio is linked with intensity.")]


def test_prompt_lists_passages_separately_from_facts():
    u = build_user(FACTS, None, PASSAGES)
    assert "FACTS (true of this chart)" in u and "PASSAGES (traditional meanings" in u
    assert "[planet.moon] The Moon is traditionally" in u
    assert "PASSAGES" not in build_user(FACTS)


def test_statement_may_cite_passages_with_a_fact():
    payload = {"statements": [{"text": "Mind-focused.", "fact_ids": ["moon.sign"], "passage_ids": ["planet.moon"]}]}
    valid, problems = check(payload, FACTS, PASSAGES)
    assert valid[0].passage_ids == ["planet.moon"] and not problems


def test_unknown_passage_id_is_rejected():
    payload = {"statements": [{"text": "x y.", "fact_ids": ["moon.sign"], "passage_ids": ["nope"]}]}
    valid, problems = check(payload, FACTS, PASSAGES)
    assert not valid and "unknown passage" in problems[0]


def test_passage_alone_is_not_a_citation():
    payload = {"statements": [{"text": "Generic.", "fact_ids": [], "passage_ids": ["planet.moon"]}]}
    valid, problems = check(payload, FACTS, PASSAGES)
    assert not valid and "no fact id" in problems[0]


def test_generate_reports_only_passages_actually_used():
    c = FakeClient([{"statements": [{"text": "Mind-focused.", "fact_ids": ["moon.sign"],
                                      "passage_ids": ["planet.moon"]}]}])
    r = generate_reading(c, FACTS, passages=PASSAGES)
    assert [p.id for p in r.passages] == ["planet.moon"]
    assert "PASSAGES" in c.calls[0]["user"]
    assert "planet.moon" in render(r, FACTS)
