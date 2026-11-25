"""Builds ui/demo.html: a self-contained report viewer from the pipeline run on SYNTHETIC packs."""
import json
from ember_ledger.fakes import RegexAdapter, LyingAdapter
from ember_ledger.ledger import Ledger
from ember_ledger.pipeline import run
from ember_ledger.synth import make_docs

SCEN = [
    ("Clean pack, prior finding unaddressed", RegexAdapter, dict()),
    ("SEFA total typo + statements gap", RegexAdapter, dict(sefa_total_stated=1_250_000, fs_revenue=1_100_000)),
    ("Model invents evidence (all dropped)", LyingAdapter, dict(sefa_total_stated=1_250_000, fs_revenue=1_100_000)),
]
out = []
for name, A, kw in SCEN:
    led = Ledger(); docs = make_docs(**kw)
    rep = run(A(led), led, docs)
    out.append({"name": name, "report": rep.to_dict(), "docs": docs, "calls": led.calls})
tpl = open("ui/template.html").read()
open("ui/demo.html", "w").write(tpl.replace("__DATA__", json.dumps(out)))
print("ok", len(out))
