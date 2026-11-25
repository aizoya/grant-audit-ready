"""Recall report: inject synthetic errors, run the pipeline with the zero-spend extractor, score by category.
Dev seeds 0-9 are for tuning; held-out seeds 100-109 are scored once and never used to patch rules."""
import json, sys
from ember_ledger.fakes import RegexAdapter
from ember_ledger.inject import CATEGORIES, GroundTruth, Finding, is_hit, inject
from ember_ledger.ledger import Ledger
from ember_ledger.pipeline import run
from ember_ledger.synth import make_docs

DOC_FOR = {"arithmetic": ("sefa", "statements"), "award_id": ("sefa",), "date": ("statements",),
           "threshold": ("sefa",), "prior_finding_omitted": ("prior",)}

def one(cat, seed):
    docs = make_docs(prior_finding=True, addressed=True)
    for key in DOC_FOR[cat]:
        r = inject(docs[key], cat, seed)
        if r:
            docs[key], truth = r
            led = Ledger(); rep = run(RegexAdapter(led), led, docs)
            found = any(is_hit(truth, Finding(cat, e["quote"])) for f in rep.findings for e in f.evidence)
            return True, found, len(rep.findings)
    return False, False, 0

def table(seeds):
    out = {}
    for cat in CATEGORIES:
        n = hit = 0
        for s in seeds:
            injected, found, _ = one(cat, s)
            n += injected; hit += found
        out[cat] = (hit, n)
    return out

if __name__ == "__main__":
    for name, seeds in (("dev", range(10)), ("held-out", range(100, 110))):
        print(name)
        for cat, (h, n) in table(seeds).items():
            print(f"  {cat:24s} {h}/{n}")
