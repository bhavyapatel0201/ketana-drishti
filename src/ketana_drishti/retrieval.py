"""Retrieval: pick reference passages for a chart from its facts.

No embeddings: each fact already names exactly what it is about (a planet in a sign,
a nakshatra, a house, a running dasha), so the lookup is a deterministic key match.
Same chart, same passages, every time; it runs offline and costs nothing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

CORPUS_PATH = Path(__file__).resolve().parents[2] / "corpus" / "passages.json"
DEFAULT_LIMIT = 30


def norm(s) -> str:
    return "".join(c for c in str(s).lower() if c.isalnum())


@dataclass
class Passage:
    id: str
    kind: str
    key: str
    text: str
    because: list = field(default_factory=list)  # ids of the facts that brought it in


class Corpus:
    def __init__(self, passages: list, source: str = ""):
        self.source = source
        self.by_id = {p["id"]: p for p in passages}
        self.index = {}
        for p in passages:
            for name in [p["key"], *p.get("aliases", [])]:
                self.index[(p["kind"], norm(name))] = p["id"]

    def __len__(self):
        return len(self.by_id)

    def find(self, kind: str, key) -> str | None:
        return self.index.get((kind, norm(key)))


def load_corpus(path=None) -> Corpus:
    data = json.loads(Path(path or CORPUS_PATH).read_text(encoding="utf-8"))
    return Corpus(data["passages"], data.get("source", ""))


def keys_for_fact(fact) -> list:
    """The (kind, key) pairs a fact points at."""
    parts = str(fact.id).split(".")
    head, tail = parts[0], (parts[1] if len(parts) > 1 else "")
    v = getattr(fact, "values", None) or {}
    out = []
    if head == "dasha":
        if v.get("planet"):
            out.append(("dasha", v["planet"]))
    elif tail == "sign":
        if head == "lagna":
            out.append(("concept", "lagna"))
        else:
            out.append(("planet", head))
        if v.get("sign"):
            out.append(("sign", v["sign"]))
    elif tail == "nakshatra" and v.get("nakshatra"):
        out.append(("nakshatra", v["nakshatra"]))
    elif tail == "house" and v.get("house") is not None:
        out.append(("house", v["house"]))
    elif tail == "dignity":
        d = v.get("dignity")
        if d and d != "neutral":
            out.append(("dignity", d))
    elif tail == "aspect":
        out.append(("concept", "drishti"))
    return out


def _priority(fact) -> int:
    head = str(fact.id).split(".")[0]
    return {"lagna": 0, "moon": 1, "sun": 2, "dasha": 3}.get(head, 4)


def retrieve(facts, corpus: Corpus | None = None, limit: int = DEFAULT_LIMIT) -> list:
    """Passages for these facts: lagna, Moon, Sun and running dasha first, then the rest."""
    corpus = corpus or load_corpus()
    found: dict = {}
    for order, f in enumerate(facts):
        for kind, key in keys_for_fact(f):
            pid = corpus.find(kind, key)
            if pid is None:
                continue
            rank = (_priority(f), order)
            if pid not in found:
                p = corpus.by_id[pid]
                found[pid] = [rank, Passage(pid, p["kind"], p["key"], p["text"], [f.id])]
            else:
                found[pid][0] = min(found[pid][0], rank)
                if f.id not in found[pid][1].because:
                    found[pid][1].because.append(f.id)
    ranked = sorted(found.values(), key=lambda x: x[0])
    return [p for _, p in ranked][:limit]


def unmatched(facts, corpus: Corpus | None = None) -> list:
    """(fact id, kind, key) for facts whose key has no passage. Used to catch spelling gaps."""
    corpus = corpus or load_corpus()
    return [(f.id, k, key) for f in facts for k, key in keys_for_fact(f) if corpus.find(k, key) is None]
