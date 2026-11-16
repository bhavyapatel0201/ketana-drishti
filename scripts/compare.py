import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))


def dms(x):
    d = int(x)
    m = int((x - d) * 60)
    s = ((x - d) * 60 - m) * 60
    return f"{d:2d}d {m:02d}' {s:05.2f}\""


print("Ayanamsa:", data["ayanamsa"]["name"], data["ayanamsa"]["value"])
print(f"{'Body':8} {'Sign':12} {'Degrees in sign':16} {'Nakshatra':16} Pada  Motion")
for h in data["d1Chart"]["houses"]:
    if h["number"] == 1:
        print(f"{'Lagna':8} {h['sign']:12} {dms(h['signDegrees']):16} "
              f"{h['nakshatra']:16} {h['pada']}")
    for o in h.get("occupants", []):
        print(f"{o['celestialBody']:8} {o['sign']:12} {dms(o['signDegrees']):16} "
              f"{o['nakshatra']:16} {o['pada']}     {o.get('motion_type', '')}")