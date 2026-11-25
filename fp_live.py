"""False-positive rate on CLEAN synthetic packs (both templates), N runs each. Hard cap $0.20."""
import collections
from ember_ledger.adapter import LiveAdapter
from ember_ledger.ledger import Ledger
from ember_ledger.pipeline import run
from ember_ledger.synth import make_docs
from ember_ledger.synth_b import make_docs_b
led = Ledger(budget=0.20, hard_stop=0.18); ad = LiveAdapter(led)
for name, mk in (("A", lambda: make_docs(prior_finding=True, addressed=True)), ("B", make_docs_b)):
    c = collections.Counter(); bad = 0
    for _ in range(10):
        r = run(ad, led, mk(), effort="minimal"); codes = [f.code for f in r.findings]
        bad += bool(codes); c.update(codes)
    print(f"template {name}: runs with any finding {bad}/10", dict(c), "spent $%.4f" % led.spent, flush=True)
