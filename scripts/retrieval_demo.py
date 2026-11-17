"""Show which passages a chart's facts bring in.

Run:  python scripts/retrieval_demo.py tests/fixtures/chart1.json
"""
import datetime as dt
import json
import sys

from ketana_drishti.facts import build_facts
from ketana_drishti.retrieval import load_corpus, retrieve, unmatched

chart = json.load(open(sys.argv[1], encoding="utf-8"))
facts = build_facts(chart, dt.date.today())
corpus = load_corpus()
for p in retrieve(facts, corpus):
    print(f"{p.id:28} <- {', '.join(p.because)}")
gaps = unmatched(facts, corpus)
print("\nfacts with no passage:", gaps or "none")
