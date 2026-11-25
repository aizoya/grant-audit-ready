"""First live probe (needs approval, key in env, network allowed). Hard cap $0.50 via the ledger.
Checks: endpoint works, usage fields, cached_tokens on a repeated prefix, effort effect on output tokens."""
from ember_ledger.adapter import LiveAdapter
from ember_ledger.ledger import Ledger
from ember_ledger.pipeline import RULES_PREFIX, run
from ember_ledger.synth import make_docs

led = Ledger(budget=0.50, hard_stop=0.45)
ad = LiveAdapter(led)
rep = run(ad, led, make_docs(sefa_total_stated=1_250_000, fs_revenue=1_100_000), effort="minimal")
rep2 = run(ad, led, make_docs(sefa_total_stated=1_250_000, fs_revenue=1_100_000), effort="minimal")  # repeat: prefix cache check
print("calls", led.calls, "spent $%.5f" % led.spent, "by_label", {k: round(v, 6) for k, v in led.by_label.items()})
print("findings", [f.code for f in rep.findings], "dropped", rep.dropped_unverified)
