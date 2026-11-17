"""Hindi and Gujarati wording for the classic reading.

Names of planets, signs and nakshatras live in the corpus (name_hi / name_gu), so
spelling variants are matched the same way as for passages. This module holds the
sentence templates, ordinals and fixed notes. All Hindi and Gujarati text here and in
the corpus is a DRAFT that needs review by a fluent reader.
"""

from __future__ import annotations

import re

from .reading import DISCLAIMER

LANGS = ("en", "hi", "gu")

HOUSE_ORD = {
    "hi": {1: "पहले", 2: "दूसरे", 3: "तीसरे", 4: "चौथे", 5: "पाँचवें", 6: "छठे", 7: "सातवें",
           8: "आठवें", 9: "नौवें", 10: "दसवें", 11: "ग्यारहवें", 12: "बारहवें"},
    "gu": {1: "પહેલા", 2: "બીજા", 3: "ત્રીજા", 4: "ચોથા", 5: "પાંચમા", 6: "છઠ્ઠા", 7: "સાતમા",
           8: "આઠમા", 9: "નવમા", 10: "દસમા", 11: "અગિયારમા", 12: "બારમા"},
}
ASPECT_ORD = {  # for "drishti", a feminine noun
    "hi": {1: "पहली", 2: "दूसरी", 3: "तीसरी", 4: "चौथी", 5: "पाँचवीं", 6: "छठी", 7: "सातवीं",
           8: "आठवीं", 9: "नौवीं", 10: "दसवीं", 11: "ग्यारहवीं", 12: "बारहवीं"},
    "gu": {1: "પહેલી", 2: "બીજી", 3: "ત્રીજી", 4: "ચોથી", 5: "પાંચમી", 6: "છઠ્ઠી", 7: "સાતમી",
           8: "આઠમી", 9: "નવમી", 10: "દસમી", 11: "અગિયારમી", 12: "બારમી"},
}
DIGNITY_SENTENCE = {
    "hi": {"exalted": "{p} उच्च का है।", "debilitated": "{p} नीच का है।",
           "own_sign": "{p} स्वराशि में है।", "moolatrikona": "{p} मूलत्रिकोण में है।"},
    "gu": {"exalted": "{p} ઉચ્ચનો છે.", "debilitated": "{p} નીચનો છે.",
           "own_sign": "{p} સ્વરાશિમાં છે.", "moolatrikona": "{p} મૂળત્રિકોણમાં છે."},
}
DIGNITY_LABEL = {
    "hi": {"exalted": "उच्च", "debilitated": "नीच", "ownsign": "स्वराशि", "moolatrikona": "मूलत्रिकोण"},
    "gu": {"exalted": "ઉચ્ચ", "debilitated": "નીચ", "ownsign": "સ્વરાશિ", "moolatrikona": "મૂળત્રિકોણ"},
}
T = {
    "hi": {
        "lagna_sign": "लग्न {s} है।", "lagna_nak": "लग्न {n} नक्षत्र, पद {pada} में है।",
        "sign": "{p} {s} राशि में है।", "nak": "{p} {n} नक्षत्र, पद {pada} में है।",
        "house": "{p} {o} भाव में है।",
        "md": "{d} को चल रही महादशा: {p}, {a} से {b} तक।",
        "ad": "{d} को चल रही अंतर्दशा: {p}, {a} से {b} तक।",
        "pd": "{d} को चल रही प्रत्यंतर दशा: {p}, {a} से {b} तक।",
        "asp_planet": "{f} {t} पर दृष्टि डालता है ({k} दृष्टि)", "asp_house": "{f} {o} भाव पर दृष्टि डालता है ({k} दृष्टि)",
        "asp_intro": "इस कुंडली में ग्रहों की दृष्टियाँ इस प्रकार हैं: ", "asp_end": "।",
        "see": "(ऊपर {x} वाला विवरण भी देखें।)", "and": " और ", "house_label": "भाव {n}", "dasha_label": "{p} दशा",
    },
    "gu": {
        "lagna_sign": "લગ્ન {s} છે.", "lagna_nak": "લગ્ન {n} નક્ષત્ર, પદ {pada}માં છે.",
        "sign": "{p} {s} રાશિમાં છે.", "nak": "{p} {n} નક્ષત્ર, પદ {pada}માં છે.",
        "house": "{p} {o} ભાવમાં છે.",
        "md": "{d} ના રોજ ચાલતી મહાદશા: {p}, {a} થી {b} સુધી.",
        "ad": "{d} ના રોજ ચાલતી અંતર્દશા: {p}, {a} થી {b} સુધી.",
        "pd": "{d} ના રોજ ચાલતી પ્રત્યંતર દશા: {p}, {a} થી {b} સુધી.",
        "asp_planet": "{f} {t} પર દૃષ્ટિ કરે છે ({k} દૃષ્ટિ)", "asp_house": "{f} {o} ભાવ પર દૃષ્ટિ કરે છે ({k} દૃષ્ટિ)",
        "asp_intro": "આ કુંડળીમાં ગ્રહોની દૃષ્ટિઓ આ પ્રમાણે છે: ", "asp_end": ".",
        "see": "(ઉપર {x} વિશેનું વર્ણન પણ જુઓ.)", "and": " અને ", "house_label": "ભાવ {n}", "dasha_label": "{p} દશા",
    },
}
DISCLAIMERS = {
    "en": DISCLAIMER,
    "hi": "यह पठन चिंतन और मनोरंजन के लिए है। यह चिकित्सा, वित्तीय, कानूनी या संबंधों से जुड़ी सलाह नहीं है।",
    "gu": "આ વાચન ચિંતન અને મનોરંજન માટે છે. તે તબીબી, નાણાકીય, કાનૂની કે સંબંધો અંગેની સલાહ નથી.",
}
NOTES = {
    "en": "Classic reading: built from the computed facts and traditional passages, with no AI. Each line says which facts and passages it uses.",
    "hi": "क्लासिक पठन: यह गणना किए गए तथ्यों और पारंपरिक अंशों से बना है, इसमें AI का उपयोग नहीं हुआ है। हर पंक्ति बताती है कि वह किन तथ्यों और अंशों पर आधारित है। (हिंदी पाठ अभी प्रारूप है और समीक्षा की प्रतीक्षा में है।)",
    "gu": "ક્લાસિક વાચન: આ ગણતરી કરેલા તથ્યો અને પરંપરાગત અંશોમાંથી બન્યું છે, તેમાં AIનો ઉપયોગ થયો નથી. દરેક પંક્તિ બતાવે છે કે તે કયા તથ્યો અને અંશો પર આધારિત છે. (ગુજરાતી લખાણ હાલ પ્રારૂપ છે અને સમીક્ષાની રાહ જુએ છે.)",
}
_ASOF = re.compile(r"as of (\d{4}-\d{2}-\d{2})")


def label(p, lang: str, corpus) -> str:
    """Short name of a passage, for the 'see also' pointer."""
    t = T[lang]
    if p.kind == "house":
        return t["house_label"].format(n=p.key)
    if p.kind == "dignity":
        return DIGNITY_LABEL[lang].get(p.id.split(".", 1)[1], p.key)
    if p.kind == "dasha":
        return t["dasha_label"].format(p=corpus.name("planet", p.key, lang))
    return corpus.name(p.kind, p.key, lang)


def fact_sentence(f, lang: str, corpus) -> str | None:
    """The fact as a sentence in `lang`, built from its values; None if the kind is unknown."""
    t, v = T[lang], (f.values or {})
    parts = f.id.split(".")
    head, tail = parts[0], (parts[1] if len(parts) > 1 else "")
    pl = lambda x: corpus.name("planet", x, lang)  # noqa: E731
    if head == "dasha":
        kind = {"mahadasha": "md", "antardasha": "ad", "pratyantardasha": "pd"}.get(tail)
        m = _ASOF.search(f.text or "")
        if not (kind and m and v.get("planet")):
            return None
        return t[kind].format(d=m.group(1), p=pl(v["planet"]), a=v.get("start", ""), b=v.get("end", ""))
    if tail == "aspect":
        k = ASPECT_ORD[lang].get(int(v.get("aspect", 0)), str(v.get("aspect", "")))
        if "to_planet" in v:
            return t["asp_planet"].format(f=pl(v["from"]), t=pl(v["to_planet"]), k=k)
        if "to_house" in v:
            return t["asp_house"].format(f=pl(v["from"]), o=HOUSE_ORD[lang].get(int(v["to_house"]), v["to_house"]), k=k)
        return None
    if tail == "sign" and v.get("sign"):
        s = corpus.name("sign", v["sign"], lang)
        return t["lagna_sign"].format(s=s) if head == "lagna" else t["sign"].format(p=pl(head), s=s)
    if tail == "nakshatra" and v.get("nakshatra"):
        n = corpus.name("nakshatra", v["nakshatra"], lang)
        if head == "lagna":
            return t["lagna_nak"].format(n=n, pada=v.get("pada", ""))
        return t["nak"].format(p=pl(head), n=n, pada=v.get("pada", ""))
    if tail == "house" and v.get("house") is not None:
        return t["house"].format(p=pl(head), o=HOUSE_ORD[lang].get(int(v["house"]), v["house"]))
    if tail == "dignity":
        tmpl = DIGNITY_SENTENCE[lang].get(v.get("dignity"))
        return tmpl.format(p=pl(head)) if tmpl else None
    return None
