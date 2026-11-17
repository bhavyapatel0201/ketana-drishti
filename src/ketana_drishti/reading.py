"""Grounded readings: the model may only use computed facts and must cite them.

Flow: facts -> prompt (ids + text only, never the raw chart) -> forced tool call
returning statements with fact_ids -> our checker -> one retry -> reading.
The disclaimer is added here in code, never by the model.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .llm import LLMError

DISCLAIMER = (
    "This reading is for reflection and entertainment. It is not medical, "
    "financial, legal or relationship advice."
)

LANGUAGES = {"en": "English", "hi": "Hindi", "gu": "Gujarati"}

# Simple English guardrail on the model's output (see ADR-0004 for limits).
# "cancer" is matched in lower case only, so the zodiac sign Cancer is allowed;
# "invest" matches investing/investment but not "investigation".
BLOCKED = re.compile(
    r"\b(disease|illness|surgery|die|death|dead|suicide|pregnan\w*|"
    r"lawsuit|invest(?:s|ed|ing|ments?|ors?)?|stocks?|crypto|gambl\w*|lottery|"
    r"divorce\w*|marry|marries|marriage|affair|cheat\w*)\b",
    re.IGNORECASE,
)
BLOCKED_LOWER = re.compile(r"\bcancer\b")


def is_blocked(text: str) -> bool:
    return bool(BLOCKED.search(text) or BLOCKED_LOWER.search(text))


SYSTEM_TEMPLATE = """You write short astrology readings for Ketana Drishti.

RULES (follow all of them):
1. FACTS say what is true of this chart. PASSAGES say what such placements \
traditionally mean. Use only the facts and passages given by the user. Never add \
chart details, planet positions, dashas or yogas that are not in the facts, and \
never present a passage as a fact about this chart.
2. Every statement must list, in fact_ids, the ids of the facts it is about (at \
least one). If it uses a passage for the meaning, list that passage in passage_ids. \
Use only ids that appear in the facts and passages.
3. Do not predict or comment on health, illness, death, money or investments, \
legal outcomes, or marriage and relationship outcomes. Speak about tendencies \
and themes for reflection, never certainties.
4. Write the statement text in {language}. Keep fact ids exactly as given.
5. If the facts do not support an answer, say less. Do not pad.
6. Return the reading by calling the give_reading tool."""

TOOL = {
    "name": "give_reading",
    "description": "Return the reading as a list of statements, each citing fact ids.",
    "input_schema": {
        "type": "object",
        "properties": {
            "statements": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "fact_ids": {
                            "type": "array",
                            "minItems": 1,
                            "items": {"type": "string"},
                        },
                        "passage_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["text", "fact_ids"],
                },
            }
        },
        "required": ["statements"],
    },
}


class ReadingError(Exception):
    pass


@dataclass
class Statement:
    text: str
    fact_ids: list
    passage_ids: list = field(default_factory=list)


@dataclass
class Reading:
    statements: list
    disclaimer: str = DISCLAIMER
    language: str = "en"
    model: str = ""
    retried: bool = False
    dropped: int = 0
    problems: list = field(default_factory=list)
    passages: list = field(default_factory=list)  # passages the statements actually cite


def build_system(language: str = "en") -> str:
    if language not in LANGUAGES:
        raise ReadingError(f"Unsupported language: {language}. Use one of {sorted(LANGUAGES)}.")
    return SYSTEM_TEMPLATE.format(language=LANGUAGES[language])


def build_user(facts, question: str | None = None, passages=None) -> str:
    lines = [f"[{f.id}] {f.text}" for f in facts]
    q = (question or "Give a general reading of this chart.").strip()
    out = f"QUESTION: {q}\n\nFACTS (true of this chart):\n" + "\n".join(lines)
    if passages:
        plines = [f"[{p.id}] {p.text}" for p in passages]
        out += "\n\nPASSAGES (traditional meanings, not facts about this chart):\n" + "\n".join(plines)
    return out


def check(tool_input, facts, passages=()):
    """Return (valid_statements, problems). A statement is valid only if it has
    text, at least one fact id, only known fact and passage ids, and passes the
    guardrail. A passage alone never counts as a citation."""
    known = {f.id for f in facts}
    known_p = {p.id for p in passages}
    problems, valid = [], []
    raw = (tool_input or {}).get("statements")
    if not isinstance(raw, list) or not raw:
        return [], ["The reply had no statements."]
    for i, s in enumerate(raw, 1):
        text = (s.get("text") or "").strip() if isinstance(s, dict) else ""
        ids = s.get("fact_ids") if isinstance(s, dict) else None
        if not text:
            problems.append(f"Statement {i} is empty.")
        elif not ids or not isinstance(ids, list):
            problems.append(f"Statement {i} cites no fact id.")
        elif any(x not in known for x in ids):
            bad = [x for x in ids if x not in known]
            problems.append(f"Statement {i} cites unknown fact id(s): {', '.join(map(str, bad))}.")
        elif any(x not in known_p for x in (s.get("passage_ids") or [])):
            bad = [x for x in s.get("passage_ids") if x not in known_p]
            problems.append(f"Statement {i} cites unknown passage id(s): {', '.join(map(str, bad))}.")
        elif is_blocked(text):
            problems.append(f"Statement {i} touches a topic that is not allowed.")
        else:
            valid.append(Statement(text=text, fact_ids=list(ids),
                                   passage_ids=list(s.get("passage_ids") or [])))
    return valid, problems


def generate_reading(client, facts, language: str = "en", question: str | None = None,
                     passages=None) -> Reading:
    """Ask the model, check the answer, retry once with the problems listed."""
    facts = list(facts)
    passages = list(passages or [])
    if not facts:
        raise ReadingError("No facts to build a reading from.")
    system = build_system(language)
    user = build_user(facts, question, passages)

    resp = client.complete(system, user, tool=TOOL)
    valid, problems = check(resp.tool_input, facts, passages)
    retried = False
    if problems:
        retried = True
        fix = (
            user
            + "\n\nYour previous answer had problems. Fix them and answer again:\n- "
            + "\n- ".join(problems)
        )
        resp = client.complete(system, fix, tool=TOOL)
        valid, problems2 = check(resp.tool_input, facts, passages)
        dropped = len(problems2)
        problems = problems2
    else:
        dropped = 0

    if not valid:
        raise ReadingError("The model gave no usable, cited statements. " + " ".join(problems))
    used = {i for s in valid for i in s.passage_ids}
    return Reading(
        statements=valid,
        passages=[p for p in passages if p.id in used],
        language=language,
        model=getattr(resp, "model", ""),
        retried=retried,
        dropped=dropped,
        problems=problems,
    )


def render(reading: Reading, facts) -> str:
    """Plain-text version with citations resolved to the fact text."""
    by_id = {f.id: f.text for f in facts}
    out = []
    for n, s in enumerate(reading.statements, 1):
        out.append(f"{n}. {s.text}  [{', '.join(s.fact_ids)}]")
    out.append("")
    out.append("Based on:")
    seen = []
    for s in reading.statements:
        for i in s.fact_ids:
            if i not in seen:
                seen.append(i)
    out += [f"- {i}: {by_id[i]}" for i in seen]
    if reading.passages:
        out += ["", "Traditional meanings used:"]
        out += [f"- {p.id}: {p.text}" for p in reading.passages]
    out += ["", reading.disclaimer]
    return "\n".join(out)
