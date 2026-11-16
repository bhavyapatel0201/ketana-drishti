import glob
import json

for p in sorted(glob.glob("tests/fixtures/*.json")):
    d = json.load(open(p, encoding="utf-8"))
    print(p, "| birth:", d.get("_input", {}).get("datetime"), "| balance:", d["dashas"]["balance"])
    for name, m in d["dashas"]["all"]["mahadashas"].items():
        print("   ", name, m["start"], "->", m["end"])