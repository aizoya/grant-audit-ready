import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ember_ledger.inject import CATEGORIES, Finding, inject, is_hit, score_document
from ember_ledger.verifier import Evidence, verify_quote

PAGES = [
    "Schedule of Expenditures of Federal Awards. Assistance Listing 93.558 expended $500,000 and Assistance Listing 84.010 expended $750,000. Total federal awards expended $1,250,000.",
    "The fiscal year ended June 30, 2025. The audit was required because expenditures exceeded the threshold. A prior year finding on cash management was resolved during the year. The report was received on December 1, 2025.",
]


def test_every_category_injects_and_changes_text():
    for cat in CATEGORIES:
        res = inject(PAGES, cat, seed=7)
        assert res is not None, cat
        new_pages, truth = res
        assert new_pages != PAGES, cat
        assert truth.category == cat


def test_injection_is_deterministic():
    a = inject(PAGES, "arithmetic", seed=3)
    b = inject(PAGES, "arithmetic", seed=3)
    assert a[0] == b[0] and a[1] == b[1]


def test_original_pages_not_mutated():
    snapshot = list(PAGES)
    for cat in CATEGORIES:
        inject(PAGES, cat, seed=1)
    assert PAGES == snapshot


def test_missing_site_returns_none():
    assert inject(["nothing numeric here at all"], "arithmetic", 1) is None


def test_correct_quote_is_hit_and_unrelated_quote_is_false_positive():
    new_pages, truth = inject(PAGES, "arithmetic", seed=2)
    page = new_pages[truth.page - 1]
    # quote containing the modified amount
    quote = page[page.index(truth.modified) - 20: page.index(truth.modified) + len(truth.modified) + 10]
    assert verify_quote(new_pages, Evidence(quote, truth.page)).ok
    s = score_document(truth, [Finding("arithmetic", quote), Finding("date", "The fiscal year ended June 30")])
    assert s.detected == 1 and s.recall == 1.0 and s.false_positive_flags == 1


def test_miss_scores_zero_recall():
    _, truth = inject(PAGES, "award_id", seed=5)
    s = score_document(truth, [Finding("date", "The report was received on December 1")])
    assert s.detected == 0 and s.recall == 0.0 and s.false_positive_flags == 1


def test_short_quote_never_hits():
    _, truth = inject(PAGES, "date", seed=1)
    assert not is_hit(truth, Finding("date", "2025"))


def test_prior_finding_omission_removes_sentence():
    new_pages, truth = inject(PAGES, "prior_finding_omitted", seed=1)
    assert "prior year finding" not in " ".join(new_pages).lower()
    assert truth.modified == ""
