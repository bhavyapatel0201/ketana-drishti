import json

d = json.load(open("tests/fixtures/chart1.json", encoding="utf-8"))
da = d["dashas"]

print("top-level keys:", list(da.keys()))
print("balance:", json.dumps(da.get("balance"))[:300])
print()

allm = da["all"]
print("all keys:", list(allm.keys()))
md = allm["mahadashas"]
print("mahadashas type:", type(md).__name__, "count:", len(md))

items = list(md.items()) if isinstance(md, dict) else list(enumerate(md))
for key, m in items[:2]:
    print()
    print("MAHADASHA", key, "->", json.dumps(m)[:600])