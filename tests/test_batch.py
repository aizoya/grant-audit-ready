from ember_ledger.batch import MAX_PACKS, PATTERN, make_pack, run_batch
from ember_ledger.fakes import RegexAdapter
from ember_ledger import webapi


def test_every_injected_kind_gets_a_truth():
    for i in range(len(PATTERN)):
        kind, docs, truth = make_pack(i, 2000)
        assert set(docs) == {"sefa", "statements", "prior"}
        assert (truth is None) == kind.startswith("clean"), kind


def test_run_batch_counts_failures_and_continues():
    class Boom:
        def __init__(self, led): pass
        def complete(self, *a, **k): raise RuntimeError("x")
    out = run_batch(7, 2000, lambda led: Boom(led), workers=3)
    assert out["packages"] == 7 and out["errors"] == 7 and out["total_cost_usd"] == 0


def test_clean_template_a_has_no_false_alarm_with_stand_in():
    out = run_batch(7, 2000, lambda led: RegexAdapter(led), workers=3)
    clean_a = [r for r in out["rows"] if r["kind"] == "clean_a"]
    assert clean_a and all(r.get("false_alarm") is False for r in clean_a)


def test_package_cap():
    out = run_batch(10_000, 1, lambda led: type("E", (), {"__init__": lambda s, l: None,
                                                          "complete": lambda s, *a, **k: (_ for _ in ()).throw(RuntimeError())})(led), workers=8)
    assert out["packages"] == MAX_PACKS


def test_live_disabled_switch():
    st, b = webapi.handle_check({"docs": {}}, env={"LIVE_DISABLED": "1"})
    assert st == 503
