import datetime as dt
import glob
import json
import re
from dataclasses import dataclass, field

import pytest

from ketana_drishti import i18n
from ketana_drishti.classic import classic_payload
from ketana_drishti.reading import check
from ketana_drishti.retrieval import load_corpus, retrieve

CORPUS = load_corpus()
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
GUJARATI = re.compile(r"[઀-૿]")
SCRIPT = {"hi": DEVANAGARI, "gu": GUJARATI}


@dataclass
class F:
    id: str
    text: str = ""
    values: dict = field(default_factory=dict)


def test_every_passage_has_both_translations_in_the_right_script():
    for p in CORPUS.by_id.values():
        assert DEVANAGARI.search(p["text_hi"]), p["id"]
        assert GUJARATI.search(p["text_gu"]), p["id"]


@pytest.mark.parametrize("kind,count", [("planet", 9), ("sign", 12), ("nakshatra", 27)])
def test_names_exist_and_are_unique(kind, count):
    for lang in ("hi", "gu"):
        names = [p[f"name_{lang}"] for p in CORPUS.by_id.values() if p["kind"] == kind]
        assert len(names) == count and len(set(names)) == count


def test_ordinals_cover_all_twelve_houses():
    for lang in ("hi", "gu"):
        assert set(i18n.HOUSE_ORD[lang]) == set(range(1, 13)) == set(i18n.ASPECT_ORD[lang])


def test_name_lookup_uses_aliases():
    assert CORPUS.name("nakshatra", "Jyestha", "hi") == "ज्येष्ठा"
    assert CORPUS.name("sign", "Scorpio", "gu") == "વૃશ્ચિક"
    assert CORPUS.name("planet", "Moon", "en") == "Moon"
    assert CORPUS.name("nakshatra", "Unknown", "hi") == "Unknown"


@pytest.mark.parametrize("lang,expected", [
    ("hi", {"moon.sign": "चंद्र वृश्चिक राशि में है।", "lagna.sign": "लग्न मिथुन है।",
            "moon.nakshatra": "चंद्र ज्येष्ठा नक्षत्र, पद 4 में है।", "moon.house": "चंद्र छठे भाव में है।",
            "moon.dignity": "चंद्र नीच का है।"}),
    ("gu", {"moon.sign": "ચંદ્ર વૃશ્ચિક રાશિમાં છે.", "lagna.sign": "લગ્ન મિથુન છે.",
            "moon.nakshatra": "ચંદ્ર જ્યેષ્ઠા નક્ષત્ર, પદ 4માં છે.", "moon.house": "ચંદ્ર છઠ્ઠા ભાવમાં છે.",
            "moon.dignity": "ચંદ્ર નીચનો છે."}),
])
def test_fact_sentences(lang, expected):
    facts = {
        "moon.sign": F("moon.sign", values={"sign": "Scorpio"}),
        "lagna.sign": F("lagna.sign", values={"sign": "Gemini"}),
        "moon.nakshatra": F("moon.nakshatra", values={"nakshatra": "Jyeshtha", "pada": 4}),
        "moon.house": F("moon.house", values={"house": 6}),
        "moon.dignity": F("moon.dignity", values={"dignity": "debilitated"}),
    }
    for fid, want in expected.items():
        assert i18n.fact_sentence(facts[fid], lang, CORPUS) == want


def test_dasha_and_aspect_sentences():
    md = F("dasha.mahadasha", "Running Mahadasha as of 2026-11-16: Venus, 2007-12-15 to 2027-12-14",
           {"planet": "Venus", "start": "2007-12-15", "end": "2027-12-14"})
    assert i18n.fact_sentence(md, "hi", CORPUS) == "2026-11-16 को चल रही महादशा: शुक्र, 2007-12-15 से 2027-12-14 तक।"
    assert "મહાદશા: શુક્ર" in i18n.fact_sentence(md, "gu", CORPUS)
    ap = F("rahu.aspect.saturn", "x", {"from": "Rahu", "to_planet": "Saturn", "aspect": 9})
    assert i18n.fact_sentence(ap, "hi", CORPUS) == "राहु शनि पर दृष्टि डालता है (नौवीं दृष्टि)"
    ah = F("jupiter.aspect.house1", "x", {"from": "Jupiter", "to_house": 1, "aspect": 5})
    assert "पहले भाव पर" in i18n.fact_sentence(ah, "hi", CORPUS)
    assert i18n.fact_sentence(F("moon.dignity", values={"dignity": "neutral"}), "hi", CORPUS) is None


FACTS = [
    F("lagna.sign", "Lagna (ascendant) is Gemini", {"sign": "Gemini"}),
    F("moon.sign", "Moon is in Scorpio", {"sign": "Scorpio"}),
    F("moon.nakshatra", "Moon is in Jyeshtha, pada 4", {"nakshatra": "Jyeshtha", "pada": 4}),
    F("moon.house", "Moon is in house 6", {"house": 6}),
    F("moon.dignity", "Moon is debilitated", {"dignity": "debilitated"}),
    F("sun.sign", "Sun is in Aries", {"sign": "Aries"}),
    F("mars.sign", "Mars is in Aries", {"sign": "Aries"}),
    F("dasha.mahadasha", "Running Mahadasha as of 2026-11-16: Venus, 2007-12-15 to 2027-12-14",
      {"planet": "Venus", "start": "2007-12-15", "end": "2027-12-14"}),
    F("rahu.aspect.saturn", "Rahu aspects Saturn (9th aspect)", {"from": "Rahu", "to_planet": "Saturn", "aspect": 9}),
]


@pytest.mark.parametrize("lang", ["hi", "gu"])
def test_localized_classic_has_same_structure_and_no_english_leak(lang):
    passages = retrieve(FACTS, CORPUS)
    en = classic_payload(FACTS, passages, "en", CORPUS)
    loc = classic_payload(FACTS, passages, lang, CORPUS)
    assert [(s["fact_ids"], s["passage_ids"]) for s in en["statements"]] == \
           [(s["fact_ids"], s["passage_ids"]) for s in loc["statements"]]
    for s in loc["statements"]:
        assert SCRIPT[lang].search(s["text"])
        assert "Moon is in" not in s["text"] and "is traditionally" not in s["text"]
    valid, problems = check(loc, FACTS, passages)
    assert not problems and len(valid) == len(loc["statements"])
    mars = [s for s in loc["statements"] if s["fact_ids"] == ["mars.sign"]][0]
    assert ("ऊपर" if lang == "hi" else "ઉપર") in mars["text"]


def test_unsupported_language_is_rejected():
    with pytest.raises(ValueError):
        classic_payload(FACTS, [], "fr", CORPUS)


@pytest.mark.parametrize("path", sorted(glob.glob("tests/fixtures/chart*.json")))
@pytest.mark.parametrize("lang", ["hi", "gu"])
def test_real_charts_localize_cleanly(path, lang):
    from ketana_drishti.facts import build_facts
    facts = build_facts(json.load(open(path, encoding="utf-8")), dt.date(2026, 11, 16))
    passages = retrieve(facts, CORPUS, limit=500)
    payload = classic_payload(facts, passages, lang, CORPUS)
    valid, problems = check(payload, facts, passages)
    assert not problems and len(valid) >= 15
    for s in payload["statements"]:
        assert SCRIPT[lang].search(s["text"])
        assert not re.search(r"\b(?:is in|aspects|Running)\b", s["text"])
