import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ember_ledger.adapter import StubAdapter
from ember_ledger.checks import (
    add_months, check_sefa_total, check_submission_timeliness, check_threshold,
    single_audit_threshold, submission_due,
)
from ember_ledger.ledger import BudgetExceeded, Ledger, Usage, cost_usd, tier_for, worst_case_usd
from ember_ledger.verifier import Evidence, verify_finding, verify_quote


# ---- ledger ----
def test_short_tier_cost():
    # 100K input (20K cached), 5K output
    u = Usage(100_000, 5_000, 20_000)
    expected = (20_000 * 0.004 + 80_000 * 0.10 + 5_000 * 0.50) / 1e6
    assert cost_usd(u) == pytest.approx(expected)


def test_long_tier_applies_to_whole_request():
    u = Usage(300_000, 1_000, 0)
    assert tier_for(u.input_tokens) == "long"
    assert cost_usd(u) == pytest.approx((300_000 * 0.30 + 1_000 * 1.50) / 1e6)


def test_threshold_boundary_is_strictly_over_200k():
    assert tier_for(200_000) == "short"
    assert tier_for(200_001) == "long"


def test_cached_counts_toward_tier():
    # 150K cached + 60K new = 210K total -> long tier even though most is cached
    u = Usage(210_000, 0, 150_000)
    assert tier_for(u.input_tokens) == "long"
    assert cost_usd(u) == pytest.approx((150_000 * 0.012 + 60_000 * 0.30) / 1e6)


def test_usage_validation():
    with pytest.raises(ValueError):
        Usage(10, 0, 11)
    with pytest.raises(ValueError):
        Usage(-1, 0, 0)


def test_from_responses_api():
    u = Usage.from_responses_api({"input_tokens": 1000, "output_tokens": 50, "input_tokens_details": {"cached_tokens": 400}})
    assert (u.input_tokens, u.output_tokens, u.cached_tokens) == (1000, 50, 400)


def test_hard_stop_refuses_before_spending():
    led = Ledger(budget=10.0, hard_stop=0.001)
    with pytest.raises(BudgetExceeded):
        led.preflight(100_000, 4_000)
    assert led.spent == 0.0


def test_cost_per_verified_result():
    led = Ledger()
    assert led.cost_per_verified_result is None
    led.record("a", Usage(100_000, 2_000, 0))
    led.mark_verified(2)
    assert led.cost_per_verified_result == pytest.approx(led.spent / 2)


def test_stub_adapter_caches_repeated_prefix_cheaper():
    led = Ledger()
    stub = StubAdapter(led, {"findings": []})
    prefix = "RULES " * 5000
    stub.complete("r1", prefix, "doc one " * 1000, {}, "low", 2000)
    first = led.by_label["r1"]
    stub.complete("r2", prefix, "doc one " * 1000, {}, "low", 2000)
    assert led.by_label["r2"] < first


def test_worst_case_bound_exceeds_actual():
    u = Usage(50_000, 1_000, 0)
    assert worst_case_usd(50_000, 4_000) >= cost_usd(u)


# ---- verifier ----
PAGES = ["Schedule of Expenditures of Federal Awards\nTotal federal awards expended $1,250,000", "Notes: the Organization’s fiscal year ends June 30, 2025."]


def test_quote_found_and_page_reported():
    r = verify_quote(PAGES, Evidence("total federal awards expended $1,250,000", 1))
    assert r.ok and r.page == 1


def test_quote_normalization_handles_curly_quotes_and_whitespace():
    r = verify_quote(PAGES, Evidence("the Organization's   fiscal year ends June 30, 2025", 2))
    assert r.ok and r.page == 2


def test_fabricated_quote_rejected():
    r = verify_quote(PAGES, Evidence("total federal awards expended $9,999,999"))
    assert not r.ok


def test_wrong_page_claim_still_found_but_flagged():
    r = verify_quote(PAGES, Evidence("total federal awards expended $1,250,000", 2))
    assert r.ok and r.page == 1 and "different page" in r.reason


def test_short_quote_rejected():
    assert not verify_quote(PAGES, Evidence("federal")).ok


def test_finding_needs_one_verified_quote():
    ok, _ = verify_finding(PAGES, [Evidence("made up evidence text here"), Evidence("total federal awards expended $1,250,000")])
    assert ok
    ok2, _ = verify_finding(PAGES, [Evidence("made up evidence text here")])
    assert not ok2


# ---- rule checks ----
def test_threshold_by_fy_start():
    assert single_audit_threshold(date(2024, 9, 30)) == 750_000
    assert single_audit_threshold(date(2024, 10, 1)) == 1_000_000


def test_threshold_check_catches_wrong_applicability():
    c = check_threshold(date(2025, 7, 1), 900_000, audit_claimed_required=True)
    assert not c.passed
    assert check_threshold(date(2024, 7, 1), 900_000, audit_claimed_required=True).passed


def test_submission_due_earlier_of_30_days_or_nine_months():
    fy_end = date(2025, 6, 30)
    assert add_months(fy_end, 9) == date(2026, 3, 30)  # clamped from Mar 30 valid
    assert submission_due(fy_end, date(2025, 12, 1)) == date(2025, 12, 31)
    assert submission_due(fy_end, date(2026, 3, 15)) == date(2026, 3, 30)
    assert submission_due(fy_end, None) == date(2026, 3, 30)


def test_month_end_clamp():
    assert add_months(date(2025, 5, 31), 9) == date(2026, 2, 28)


def test_timeliness():
    assert check_submission_timeliness(date(2025, 6, 30), date(2025, 12, 1), date(2025, 12, 31)).passed
    assert not check_submission_timeliness(date(2025, 6, 30), date(2025, 12, 1), date(2026, 1, 1)).passed


def test_sefa_total():
    assert check_sefa_total([500_000, 750_000], 1_250_000).passed
    assert not check_sefa_total([500_000, 750_000], 1_300_000).passed


def test_ledger_trace_rows_match_spend():
    from ember_ledger.ledger import Ledger, Usage
    led = Ledger()
    led.record("extract_sefa", Usage(1000, 200, 400))
    led.record("extract_fs", Usage(500, 100))
    assert [r["call"] for r in led.trace] == [1, 2]
    assert led.trace[0]["cached_tokens"] == 400 and led.trace[0]["tier"] == "short"
    assert abs(sum(r["cost_usd"] for r in led.trace) - led.spent) < 1e-9
