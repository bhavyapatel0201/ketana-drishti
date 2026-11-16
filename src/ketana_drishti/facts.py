from dataclasses import dataclass
from datetime import date


@dataclass
class Fact:
    id: str
    text: str
    source: str
    values: dict


def _houses(chart: dict) -> list:
    return chart["d1Chart"]["houses"]

DIGNITY_TEXT = {
    "exalted": "exalted",
    "debilitated": "debilitated",
    "own_sign": "in its own sign",
    "moolatrikona": "in its moolatrikona sign",
    "neutral": "neutral (no special dignity)",
}


def lagna_facts(chart: dict) -> list[Fact]:
    facts = []
    for i, h in enumerate(_houses(chart)):
        if h["number"] != 1:
            continue
        src = f"d1Chart.houses[{i}]"
        facts.append(Fact(
            "lagna.sign", f"Lagna (ascendant) is {h['sign']}", src,
            {"sign": h["sign"], "degrees": h["signDegrees"]}))
        facts.append(Fact(
            "lagna.nakshatra",
            f"Lagna is in {h['nakshatra']}, pada {h['pada']}", src,
            {"nakshatra": h["nakshatra"], "pada": h["pada"]}))
    return facts


def planet_facts(chart: dict) -> list[Fact]:
    facts = []
    for i, h in enumerate(_houses(chart)):
        for j, o in enumerate(h.get("occupants", [])):
            body = o["celestialBody"]
            key = body.lower()
            src = f"d1Chart.houses[{i}].occupants[{j}]"
            facts.append(Fact(
                f"{key}.sign", f"{body} is in {o['sign']}", src,
                {"sign": o["sign"], "degrees": o["signDegrees"]}))
            facts.append(Fact(
                f"{key}.nakshatra",
                f"{body} is in {o['nakshatra']}, pada {o['pada']}", src,
                {"nakshatra": o["nakshatra"], "pada": o["pada"]}))
            facts.append(Fact(
                f"{key}.house", f"{body} is in house {o['house']}", src,
                {"house": o["house"]}))
            if body not in ("Rahu", "Ketu") and o.get("motion_type") == "retrograde":
                facts.append(Fact(
                    f"{key}.retrograde", f"{body} is retrograde", src,
                    {"motion": "retrograde"}))
            dignity = o.get("dignities", {}).get("dignity")
            if dignity:
                words = DIGNITY_TEXT.get(dignity, dignity)
                facts.append(Fact(f"{key}.dignity", f"{body} is {words}", src,
                                  {"dignity": dignity}))
    return facts

def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

def aspect_facts(chart: dict) -> list[Fact]:
    facts = []
    for i, h in enumerate(_houses(chart)):
        for j, o in enumerate(h.get("occupants", [])):
            body = o["celestialBody"]
            key = body.lower()
            gives = (o.get("aspects") or {}).get("gives", [])
            for k, a in enumerate(gives):
                n = int(a["aspect_type"])
                src = f"d1Chart.houses[{i}].occupants[{j}].aspects.gives[{k}]"
                if "to_planet" in a:
                    target = a["to_planet"]
                    facts.append(Fact(f"{key}.aspect.{target.lower()}",
                                      f"{body} aspects {target} ({_ordinal(n)} aspect)", src,
                                      {"from": body, "to_planet": target, "aspect": n}))
                elif "to_house" in a:
                    hn = a["to_house"]
                    facts.append(Fact(f"{key}.aspect.house{hn}",
                                      f"{body} aspects house {hn} ({_ordinal(n)} aspect)", src,
                                      {"from": body, "to_house": hn, "aspect": n}))
    return facts

def _parse(s: str) -> date:
    return date.fromisoformat(s)

def _pick(periods: dict, as_of: date):
    for name, p in periods.items():
        if _parse(p["start"]) <= as_of < _parse(p["end"]):
            return name, p
    return None, None

def dasha_facts(chart: dict, as_of: date | None = None) -> list[Fact]:
    facts = []
    d = chart.get("dashas")
    if not d:
        return facts
    for planet, years in (d.get("balance") or {}).items():
        facts.append(Fact("dasha.balance",
                          f"Dasha balance at birth: {planet}, {years:.2f} years remaining",
                          "dashas.balance", {"planet": planet, "years": years}))
    if as_of is None:
        return facts
    src = "dashas.all.mahadashas"
    levels = [("mahadasha", "Mahadasha", "antardashas"),
              ("antardasha", "Antardasha", "pratyantardashas"),
              ("pratyantardasha", "Pratyantardasha", None)]
    periods = d["all"]["mahadashas"]
    for fid, label, child_key in levels:
        name, p = _pick(periods, as_of)
        if p is None:
            break
        src = f"{src}.{name}"
        facts.append(Fact(f"dasha.{fid}",
                          f"Running {label} as of {as_of.isoformat()}: {name}, "
                          f"{p['start']} to {p['end']}",
                          src, {"planet": name, "start": p["start"], "end": p["end"]}))
        if child_key is None:
            break
        periods = p.get(child_key) or {}
        src = f"{src}.{child_key}"
    return facts

def build_facts(chart: dict, as_of: date | None = None) -> list[Fact]:
    return (lagna_facts(chart) + planet_facts(chart)
            + aspect_facts(chart) + dasha_facts(chart, as_of))