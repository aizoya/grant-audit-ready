"""Records LIVE Ember runs on synthetic packs into public/demo-runs.json (zero uploads, no customer data).
Needs META_MODEL_API_KEY in the environment. Cap: $0.20 total."""
import json, datetime
from ember_ledger.adapter import LiveAdapter
from ember_ledger.inject import inject
from ember_ledger.ledger import Ledger
from ember_ledger.pipeline import run
from ember_ledger.synth import make_docs

SCENARIOS = [
    ("clean", "Clean package", "Everything ties out and last year's finding was answered. Expect no findings.", None, 0, dict(prior_finding=True, addressed=True)),
    ("arithmetic", "Awards total does not add up", "A program amount was changed, so the schedule no longer sums to its stated total.", "arithmetic", 1, dict(prior_finding=True, addressed=True)),
    ("award_id", "Wrong award number", "An Assistance Listing number was swapped for another program's number.", "award_id", 2, dict(prior_finding=True, addressed=True)),
    ("prior", "Last year's finding never answered", "The prior-year finding appears with no corrective action anywhere in the package.", None, 0, dict(prior_finding=True, addressed=False)),
]
DOC_FOR = {"arithmetic": ("sefa",), "award_id": ("sefa",)}

led = Ledger(budget=0.20, hard_stop=0.15)
ad = LiveAdapter(led)
out = []
for sid, title, blurb, cat, seed, kw in SCENARIOS:
    docs = make_docs(**kw)
    if cat:
        for key in DOC_FOR[cat]:
            r = inject(docs[key], cat, seed)
            if r:
                docs[key] = r[0]; break
    before = led.spent
    rep = run(ad, led, docs)
    out.append({"id": sid, "title": title, "blurb": blurb, "docs": docs, "report": rep.to_dict(),
                "model": "muse-ember-1.0", "run_cost_usd": round(led.spent - before, 6),
                "recorded_at": datetime.date.today().isoformat(), "synthetic": True})
    print(sid, "findings:", [f.code for f in rep.findings], "cost $%.5f" % (led.spent - before), flush=True)
json.dump(out, open("public/demo-runs.json", "w"), indent=1)
print("total $%.5f calls %d" % (led.spent, led.calls))
