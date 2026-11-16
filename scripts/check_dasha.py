import glob
import json

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
         "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
SPAN = 360 / 27

for p in sorted(glob.glob("tests/fixtures/*.json")):
    d = json.load(open(p, encoding="utf-8"))
    moon = None
    for h in d["d1Chart"]["houses"]:
        for o in h.get("occupants", []):
            if o["celestialBody"] == "Moon":
                moon = o
    lon = SIGNS.index(moon["sign"]) * 30 + float(moon["signDegrees"])
    idx = int(lon // SPAN)
    frac = (lon - idx * SPAN) / SPAN
    expected = (1 - frac) * YEARS[idx % 9]
    (planet, lib), = d["dashas"]["balance"].items()
    print(p, "| lord:", ORDER[idx % 9], "| library:", planet, lib,
          "| from Moon:", round(expected, 4),
          "| diff days:", round((lib - expected) * 365.25, 1))