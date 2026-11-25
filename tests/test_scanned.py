import base64, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
from make_scanned_fixture import scanned_pdf
from ember_ledger import webapi
from ember_ledger.fakes import RegexAdapter
from ember_ledger.synth import make_docs
from ember_ledger.ledger import Usage
from ember_ledger.scanned import confirmed, numbers

DOCS = make_docs(sefa_total_stated=1_250_000, fs_revenue=1_100_000, prior_finding=True)
SPDF = {k: scanned_pdf(v) for k, v in DOCS.items()}
B64 = {k: base64.b64encode(v).decode() for k, v in SPDF.items()}
BYTES_TO_PAGES = {SPDF[k]: v for k, v in DOCS.items()}


class ScanFake(RegexAdapter):
    """Pretends to read the scanned PDFs. read B can be altered to simulate a disagreeing read."""
    def __init__(self, ledger, alter_b=None):
        super().__init__(ledger); self.alter_b = alter_b; self.reads = []

    def read_pdf(self, label, raw, n_pages, variant="a", effort="minimal"):
        self.reads.append((label, variant))
        self.ledger.preflight(2500 * n_pages, 900 * n_pages)
        self.ledger.record(label, Usage(1800 * n_pages, 300 * n_pages))
        pages = list(BYTES_TO_PAGES[raw])
        if variant == "b" and self.alter_b:
            pages = [self.alter_b(p) for p in pages]
        return pages


def setup_function(_): webapi._hits.clear()


def test_scanned_is_detected_and_read_twice():
    holder = {}
    def factory(led):
        holder["a"] = ScanFake(led); return holder["a"]
    st, b = webapi.handle_check({"docs": B64}, env={}, adapter_factory=factory)
    assert st == 200 and b["ok"]
    assert set(b["scanned"]) == {"sefa", "statements", "prior"} and "twice" in b["assurance"]
    assert len(holder["a"].reads) == 6                    # 3 docs x 2 reads
    codes = [f["code"] for f in b["report"]["findings"]]
    assert "sefa_total" in codes and b["report"]["unconfirmed_by_second_read"] == 0
    assert b["report"]["cost_usd"] < 0.05


def test_second_read_disagreement_drops_finding():
    def corrupt(p): return p.replace("1,250,000", "1,260,000")
    st, b = webapi.handle_check({"docs": B64}, env={}, adapter_factory=lambda led: ScanFake(led, corrupt))
    assert st == 200
    assert "sefa_total" not in [f["code"] for f in b["report"]["findings"]]
    assert b["report"]["unconfirmed_by_second_read"] >= 1 and b["report"]["dropped_unverified"] >= 1


def test_mixed_text_and_scanned():
    from tests.test_webapi import pdf  # text pdf helper
    mixed = dict(B64); mixed["statements"] = pdf(DOCS["statements"][0].splitlines())
    st, b = webapi.handle_check({"docs": mixed}, env={}, adapter_factory=lambda led: ScanFake(led))
    assert st == 200 and set(b["scanned"]) == {"sefa", "prior"}


def test_too_many_scanned_pages():
    big = scanned_pdf(["x " * 5] * (webapi.MAX_SCANNED_PAGES + 1))
    st, b = webapi.handle_check({"docs": {**B64, "sefa": base64.b64encode(big).decode()}}, env={})
    assert st == 413


def test_confirm_helpers():
    assert numbers("Total $1,250,000 and 93.600.") == {"1250000", "93.600"}
    assert confirmed("Expended $700,000", "Head Start | Expended $700,000")
    assert not confirmed("Expended $700,000", "Expended $70,000")
