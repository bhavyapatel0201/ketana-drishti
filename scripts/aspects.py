import json

d = json.load(open("tests/fixtures/chart1.json", encoding="utf-8"))
houses = d["d1Chart"]["houses"]

for h in houses:
    for o in h.get("occupants", []):
        print(o["celestialBody"], "-> aspects:", json.dumps(o.get("aspects"))[:300])
        break
    else:
        continue
    break

print()
for h in houses[:3]:
    print("house", h["number"], "aspectsReceived:", json.dumps(h.get("aspectsReceived"))[:300])