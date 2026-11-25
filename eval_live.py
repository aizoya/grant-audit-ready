"""Live recall eval with Ember on injected errors. One shared ledger, hard cap $0.50. Dev seeds 0-4 only."""
import sys
from ember_ledger.adapter import LiveAdapter
from ember_ledger.inject import CATEGORIES, Finding, is_hit, inject
from ember_ledger.ledger import Ledger
from ember_ledger.pipeline import run
from ember_ledger.synth import make_docs
from eval_run import DOC_FOR

effort = sys.argv[1] if len(sys.argv) > 1 else "minimal"
led = Ledger(budget=0.50, hard_stop=0.45)
ad = LiveAdapter(led)
res = {}
for cat in CATEGORIES:
    n = hit = 0
    for seed in range(5):
        docs = make_docs(prior_finding=True, addressed=True)
        truth = None
        for key in DOC_FOR[cat]:
            r = inject(docs[key], cat, seed)
            if r: docs[key], truth = r; break
        if not truth: continue
        rep = run(ad, led, docs, effort=effort)
        n += 1
        hit += any(is_hit(truth, Finding(cat, e["quote"])) for f in rep.findings for e in f.evidence)
    res[cat] = (hit, n)
    print(f"{cat:24s} {hit}/{n}  spent ${led.spent:.4f}", flush=True)
print("calls", led.calls, "total $%.4f" % led.spent)
