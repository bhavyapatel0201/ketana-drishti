"""The site-wide language switch: translations must be complete and consistent."""
import json
import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "web"
HTML = (WEB / "index.html").read_text(encoding="utf-8")
DATA = json.loads((WEB / "lang.js").read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
UI = DATA["ui"]
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
GUJARATI = re.compile(r"[઀-૿]")
PLACEHOLDER = re.compile(r"\{(\w+)\}")
# values that may legitimately have no Hindi/Gujarati letters
LATIN_OK = {"lat", "lon"}


def test_same_keys_in_all_languages():
    assert set(UI["en"]) == set(UI["hi"]) == set(UI["gu"])


def test_placeholders_match_english():
    for lang in ("hi", "gu"):
        for k, v in UI[lang].items():
            if k == "aspN":  # English uses the ordinal {o} ("9th"), Hindi/Gujarati use the number {n}
                assert PLACEHOLDER.findall(v) == ["n"]
                continue
            assert set(PLACEHOLDER.findall(v)) == set(PLACEHOLDER.findall(UI["en"][k])), (lang, k)


def test_translations_use_the_right_script():
    for k, v in UI["hi"].items():
        assert DEVANAGARI.search(v) and v != UI["en"][k], ("hi", k)
    for k, v in UI["gu"].items():
        assert GUJARATI.search(v) and v != UI["en"][k], ("gu", k)


def test_every_key_used_by_the_page_exists():
    used = set(re.findall(r'data-(?:i|ip|ia)="(\w+)"', HTML))
    used |= set(re.findall(r'\bt\("(\w+)"', HTML))
    used |= {"dgExalted", "dgDebilitated", "dgOwnsign", "dgMoolatrikona"}
    assert used and not used - set(UI["en"]), used - set(UI["en"])


def test_no_english_left_in_static_markup():
    body = HTML.split("<header>")[1].split("<script")[0]
    stripped = re.sub(r"<[^>]+>", "\n", body)
    leftover = [s.strip() for s in stripped.splitlines()
                if re.search(r"[A-Za-z]{3}", s) and s.strip() not in {"English", "हिन्दी", "ગુજરાતી", "Ketana Drishti"}]
    assert not leftover, leftover


def test_names_cover_planets_signs_and_nakshatras():
    for lang in ("hi", "gu"):
        names = DATA["names"]
        assert len({v for k, v in names["planet"][lang].items()}) >= 10
        for planet in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu", "lagna"):
            assert planet in names["planet"][lang]
        for sign in ("aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio",
                     "sagittarius", "capricorn", "aquarius", "pisces"):
            assert sign in names["sign"][lang]
        assert names["nakshatra"][lang]["jyeshtha"] and names["nakshatra"][lang]["jyestha"]
        assert len({v for v in names["nakshatra"][lang].values()}) == 27


def test_server_serves_lang_file():
    from fastapi.testclient import TestClient
    from ketana_drishti import api
    r = TestClient(api.app).get("/lang.js")
    assert r.status_code == 200 and "KD_LANG" in r.text


def test_no_local_variable_shadows_the_translation_function():
    """`t` is the translation function; a local `const t=` in a function that calls t() breaks the page."""
    script = HTML.split("<script>")[-1]
    for m in re.finditer(r"(?:const|let|var)\s+t\s*=", script):
        start = script.rfind("function ", 0, m.start())
        end = script.find("\nfunction ", m.start())
        body = script[start:end if end != -1 else len(script)]
        assert not re.search(r"(?<![\w.$])t\(", body), "t() is shadowed in: " + body[:60]
