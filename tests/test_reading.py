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
    assert "ONLY the numbered facts" in build_system("en")
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
