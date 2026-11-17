"""Classic reading: a reading built from facts and passages with no model at all.

Each statement joins one computed fact (what is true of this chart) with the
traditional passage(s) that explain it. Because it is built by fixed rules it is
free, private, repeatable, and cites its sources exactly like an AI reading; it is
checked by the same `reading.check` as model output.
"""

from __future__ import annotations

from .retrieval import _priority

MAX_ASPECTS = 6
SKIP_IDS = {"dasha.balance"}


def _label(p) -> str:
    return f"house {p.key}" if p.kind == "house" else p.key


def _sentence(text: str) -> str:
    text = text.strip().rstrip(".")
    return text + "."


def classic_payload(facts, passages) -> dict:
    """Return {"statements": [...]} in the same shape the model's tool call uses."""
    facts = list(facts)
    passages = list(passages)
    by_fact: dict = {}
    for p in passages:
        for fid in p.because:
            by_fact.setdefault(fid, []).append(p)

    ordered = sorted(enumerate(facts), key=lambda x: (_priority(x[1]), x[0]))
    used: set = set()
    statements = []
    aspects = []
    for _, f in ordered:
        if f.id in SKIP_IDS:
            continue
        if ".aspect." in f.id:
            aspects.append(f)
            continue
        related = by_fact.get(f.id, [])
        if not related:
            continue
        fresh = [p for p in related if p.id not in used]
        seen = [p for p in related if p.id in used]
        text = _sentence(f.text)
        if fresh:
            text += " " + " ".join(p.text for p in fresh)
            used.update(p.id for p in fresh)
        if seen:
            keys = " and ".join(_label(p) for p in seen)
            text += f" (See also the note on {keys} above.)"
        statements.append({"text": text, "fact_ids": [f.id], "passage_ids": [p.id for p in related]})

    if aspects:
        chosen = aspects[:MAX_ASPECTS]
        drishti = [p for p in passages if p.id == "concept.drishti"]
        text = "Planetary aspects in this chart include: " + "; ".join(a.text for a in chosen) + "."
        if drishti and drishti[0].id not in used:
            text += " " + drishti[0].text
        statements.append({"text": text, "fact_ids": [a.id for a in chosen],
                           "passage_ids": [p.id for p in drishti]})
    return {"statements": statements}
