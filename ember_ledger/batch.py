"""Batch run over generated synthetic packages (errors injected with known ground truth).
Shows what the model + code do at volume: packages checked, total cost, cost per package, recall by check,
false alarms on clean packages. Synthetic data only."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from .inject import GroundTruth, Finding, inject, is_hit
from .ledger import Ledger
from .pipeline import run
from .synth import make_docs
from .synth_b import make_docs_b

# Injected errors go into template B (different wording and layout); template B keeps the prior-finding sentence in the SEFA notes.
DOC_FOR = {"arithmetic": ("sefa", "statements"), "award_id": ("sefa",), "date": ("statements",),
           "threshold": ("sefa",), "prior_finding_omitted": ("sefa",)}
PATTERN = ("arithmetic", "award_id", "date", "threshold", "prior_finding_omitted", "clean_a", "clean_b")
MAX_PACKS = 40
PER_PACK_BUDGET, PER_PACK_STOP = 0.02, 0.015


def make_pack(i: int, seed0: int):
    kind = PATTERN[i % len(PATTERN)]
    if kind == "clean_b":
        return kind, make_docs_b(), None
    if kind == "clean_a":
        return kind, make_docs(prior_finding=True, addressed=True), None
    docs = make_docs_b()
    for key in DOC_FOR[kind]:
        r = inject(docs[key], kind, seed0 + i)
        if r:
            docs[key], truth = r
            return kind, docs, truth
    return kind, docs, None  # nothing injectable: treated as clean-like, excluded from recall


def _one(i, seed0, adapter_factory):
    kind, docs, truth = make_pack(i, seed0)
    led = Ledger(budget=PER_PACK_BUDGET, hard_stop=PER_PACK_STOP)
    try:
        rep = run(adapter_factory(led), led, docs)
    except Exception as e:  # keep the batch going; count the failure
        return {"i": i, "kind": kind, "error": type(e).__name__, "cost": round(led.spent, 6), "calls": led.calls}
    quotes = [e["quote"] for f in rep.findings for e in f.evidence]
    if truth is not None:
        if kind == "prior_finding_omitted":
            hit = any(f.code == "prior_finding_no_followup" for f in rep.findings)
        else:
            hit = any(is_hit(truth, Finding(kind, q)) for q in quotes)
        return {"i": i, "kind": kind, "hit": hit, "findings": len(rep.findings), "cost": round(led.spent, 6), "calls": led.calls}
    return {"i": i, "kind": kind, "false_alarm": len(rep.findings) > 0, "findings": len(rep.findings),
            "codes": [f.code for f in rep.findings], "messages": [f.message[:160] for f in rep.findings],
            "cost": round(led.spent, 6), "calls": led.calls}


def run_batch(n: int, seed0: int, adapter_factory, workers: int = 10) -> dict:
    n = max(1, min(int(n), MAX_PACKS))
    t = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        rows = list(ex.map(lambda i: _one(i, seed0, adapter_factory), range(n)))
    secs = time.time() - t
    ok = [r for r in rows if "error" not in r]
    by_kind: dict[str, list[int]] = {}
    for r in ok:
        if "hit" in r:
            h = by_kind.setdefault(r["kind"], [0, 0]); h[0] += r["hit"]; h[1] += 1
    clean = [r for r in ok if "false_alarm" in r]
    total = sum(r["cost"] for r in rows)
    return {
        "packages": n, "completed": len(ok), "errors": len(rows) - len(ok),
        "calls": sum(r["calls"] for r in rows),
        "total_cost_usd": round(total, 6),
        "cost_per_package_usd": round(total / n, 6),
        "seconds": round(secs, 1), "packages_per_minute": round(len(ok) / secs * 60, 1) if secs else None,
        "recall": {k: {"found": v[0], "of": v[1]} for k, v in by_kind.items()},
        "false_alarms": {"packages": len(clean), "flagged": sum(r["false_alarm"] for r in clean)},
        "rows": rows,
    }
