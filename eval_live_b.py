"""Held-out style live eval on template B (never tuned on). One shared ledger, hard cap $0.50.
Also measures false positives on the CLEAN template-B pack. Run once per change and report as is."""
import sys
from ember_ledger.adapter import LiveAdapter
from ember_ledger.inject import CATEGORIES, Finding, is_hit, inject
from ember_ledger.ledger import Ledger
from ember_ledger.pipeline import run
from ember_ledger.synth_b import make_docs_b
from eval_run import DOC_FOR
DOC_FOR = dict(DOC_FOR, prior_finding_omitted=("sefa",))  # template B keeps the sentence in the SEFA notes

led = Ledger(budget=0.50, hard_stop=0.45); ad = LiveAdapter(led)
clean = run(ad, led, make_docs_b(), effort="minimal")
print("CLEAN pack findings:", [f.code for f in clean.findings], "dropped", clean.dropped_unverified, flush=True)
for cat in CATEGORIES:
    n = hit = 0
    for seed in range(100, 105):
        docs = make_docs_b(); truth = None
        for key in DOC_FOR[cat]:
            r = inject(docs[key], cat, seed)
            if r: docs[key], truth = r; break
        if not truth: continue
        rep = run(ad, led, docs, effort="minimal"); n += 1
        if cat == "prior_finding_omitted":
            hit += any(f.code == "prior_finding_no_followup" for f in rep.findings)
        else:
            hit += any(is_hit(truth, Finding(cat, e["quote"])) for f in rep.findings for e in f.evidence)
    print(f"{cat:24s} {hit}/{n}  spent ${led.spent:.4f}", flush=True)
print("calls", led.calls, "total $%.4f" % led.spent)
