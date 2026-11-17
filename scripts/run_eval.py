"""Run the evaluation over eval/births.json. Free: no model is called.

Run:  python scripts/run_eval.py
Prints a markdown table (paste it into docs/devlog.md) and writes outputs/eval_report.json.
Exit code 1 if any chart fails.
"""
import datetime as dt
import json
import sys
from pathlib import Path

from ketana_drishti.chart import build_chart
from ketana_drishti.evaluation import evaluate_chart
from ketana_drishti.retrieval import load_corpus

AS_OF = dt.date(2026, 11, 16)  # fixed, so results are reproducible
births = json.loads(Path("eval/births.json").read_text(encoding="utf-8"))
corpus = load_corpus()
rows, report, failed = [], [], 0

for b in births:
    label = b["name"]
    try:
        chart = build_chart(dt.datetime.fromisoformat(b["datetime"]), place=None,
                            lat=b["lat"], lon=b["lon"], name=label)
        r = evaluate_chart(chart, AS_OF, corpus)
    except Exception as e:  # a chart that cannot be built is itself a finding
        failed += 1
        rows.append(f"| {label} | - | - | - | - | - | FAIL: could not build ({type(e).__name__}: {str(e)[:60]}) |")
        report.append({"name": label, "ok": False, "error": f"{type(e).__name__}: {e}"})
        continue
    failed += 0 if r.ok else 1
    note = "ok" if r.ok else "FAIL: " + "; ".join(
        [*(r.trace or [])[:2], *[f"no passage for {g}" for g in (r.gaps or [])[:2]], *(r.checker_missed or []),
         *([] if r.deterministic else ["not deterministic"]), *([] if r.pipeline_ok else ["pipeline"])])
    rows.append(f"| {label} | {r.facts} | {r.passages} | {len(r.trace or [])} | {len(r.gaps or [])} | {len(r.checker_missed or [])} | {note} |")
    report.append({"name": label, "ok": r.ok, "facts": r.facts, "passages": r.passages,
                   "trace_problems": r.trace, "gaps": r.gaps, "checker_missed": r.checker_missed})

print("| Chart | Facts | Passages | Trace problems | Passage gaps | Bad readings accepted | Result |")
print("|---|---|---|---|---|---|---|")
print("\n".join(rows))
print(f"\n{len(births) - failed} of {len(births)} charts passed (as of {AS_OF}).")
Path("outputs").mkdir(exist_ok=True)
Path("outputs/eval_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
sys.exit(1 if failed else 0)
