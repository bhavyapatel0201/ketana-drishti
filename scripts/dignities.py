import glob
import json
from collections import Counter

c = Counter()
for p in sorted(glob.glob("tests/fixtures/*.json")):
    d = json.load(open(p, encoding="utf-8"))
    for h in d["d1Chart"]["houses"]:
        for o in h.get("occupants", []):
            c[(o["celestialBody"], o.get("dignities", {}).get("dignity"))] += 1
for k, v in sorted(c.items(), key=lambda kv: (str(kv[0][1]), kv[0][0])):
    print(k, v)