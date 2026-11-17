"""Classic reading: a reading built from facts and passages with no model at all.

Each statement joins one computed fact (what is true of this chart) with the
traditional passage(s) that explain it. Because it is built by fixed rules it is
free, private, repeatable, and cites its sources exactly like an AI reading; it is
checked by the same `reading.check` as model output. English, Hindi and Gujarati
are supported; the Hindi and Gujarati wording is a draft awaiting review.
"""

from __future__ import annotations

from . import i18n
from .retrieval import _priority, load_corpus

MAX_ASPECTS = 6
SKIP_IDS = {"dasha.balance"}


def _label_en(p) -> str:
    return f"house {p.key}" if p.kind == "house" else p.key


def _sentence(text: str) -> str:
    return text.strip().rstrip(".") + "."


def classic_payload(facts, passages, lang: str = "en", corpus=None) -> dict:
    """Return {"statements": [...]} in the same shape the model's tool call uses."""
    if lang not in i18n.LANGS:
        raise ValueError(f"Unsupported language: {lang}")
    corpus = corpus or load_corpus()
    facts, passages = list(facts), list(passages)
    by_fact: dict = {}
    for p in passages:
        for fid in p.because:
            by_fact.setdefault(fid, []).append(p)

    def fact_text(f):
        if lang == "en":
            return _sentence(f.text)
        return i18n.fact_sentence(f, lang, corpus) or _sentence(f.text)

    def label(p):
        return _label_en(p) if lang == "en" else i18n.label(p, lang, corpus)

    ordered = sorted(enumerate(facts), key=lambda x: (_priority(x[1]), x[0]))
    used: set = set()
    statements, aspects = [], []
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
        text = fact_text(f)
        if fresh:
            text += " " + " ".join(p.text_for(lang) for p in fresh)
            used.update(p.id for p in fresh)
        if seen:
            joiner = " and " if lang == "en" else i18n.T[lang]["and"]
            keys = joiner.join(label(p) for p in seen)
            text += (f" (See also the note on {keys} above.)" if lang == "en"
                     else " " + i18n.T[lang]["see"].format(x=keys))
        statements.append({"text": text, "fact_ids": [f.id], "passage_ids": [p.id for p in related]})

    if aspects:
        chosen = aspects[:MAX_ASPECTS]
        drishti = [p for p in passages if p.id == "concept.drishti"]
        if lang == "en":
            text = "Planetary aspects in this chart include: " + "; ".join(a.text for a in chosen) + "."
        else:
            t = i18n.T[lang]
            text = t["asp_intro"] + "; ".join(fact_text(a).rstrip("।.") for a in chosen) + t["asp_end"]
        if drishti and drishti[0].id not in used:
            text += " " + drishti[0].text_for(lang)
        statements.append({"text": text, "fact_ids": [a.id for a in chosen],
                           "passage_ids": [p.id for p in drishti]})
    return {"statements": statements}
