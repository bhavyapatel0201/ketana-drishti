"""Offline demo of the reading flow using a scripted fake model (no key, no cost).

Run:  python scripts/reading_demo.py tests/fixtures/chart1.json
"""
import json
import sys

from ketana_drishti.facts import build_facts
from ketana_drishti.llm import FakeClient
from ketana_drishti.reading import generate_reading, render

chart = json.load(open(sys.argv[1], encoding="utf-8"))
facts = build_facts(chart)
ids = [f.id for f in facts[:2]]
fake = FakeClient([{"statements": [
    {"text": "A scripted example statement for the demo.", "fact_ids": ids}
]}])
r = generate_reading(fake, facts)
print(render(r, facts))
