from ember_ledger.fakes import LyingAdapter, RegexAdapter
from ember_ledger.ledger import Ledger
from ember_ledger.pipeline import run
from ember_ledger.synth import make_docs


def go(adapter_cls=RegexAdapter, **kw):
    led = Ledger()
    return run(adapter_cls(led), led, make_docs(**kw)), led


def codes(r):
    return {f.code for f in r.findings}


def test_clean_pack_has_only_prior_followup_review():
    r, _ = go(prior_finding=True, addressed=False)
    assert "sefa_total" not in codes(r) and "sefa_vs_statements" not in codes(r)
    assert "prior_finding_no_followup" in codes(r)


def test_prior_finding_addressed_passes():
    r, _ = go(addressed=True)
    assert "prior_finding_no_followup" not in codes(r)


def test_total_mismatch_found_with_verified_quotes():
    r, _ = go(sefa_total_stated=1_250_000, fs_revenue=1_250_000)
    f = [x for x in r.findings if x.code == "sefa_total"][0]
    assert len(f.evidence) == 4 and all(e["page"] == 1 for e in f.evidence)


def test_sefa_vs_statements_mismatch():
    r, _ = go(fs_revenue=1_100_000)
    assert "sefa_vs_statements" in codes(r)


def test_fabricated_quotes_are_dropped_not_reported():
    r, _ = go(LyingAdapter, sefa_total_stated=1_250_000, fs_revenue=1_100_000)
    assert r.findings == [] and r.dropped_unverified >= 2


def test_cost_is_tiny_and_metered():
    r, led = go()
    assert 0 < r.cost_usd < 0.01 and led.calls == 3
