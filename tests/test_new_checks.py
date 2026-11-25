from datetime import date
from ember_ledger import checks
from ember_ledger.ingest import looks_scanned, pdf_pages


def test_aln_match_and_mismatch():
    assert checks.check_aln_program("Head Start Cluster", "93.600").passed
    assert not checks.check_aln_program("Head Start Cluster", "93.569").passed
    assert not checks.check_aln_program("Mystery Program", "99.999").passed


def test_report_date_window():
    fy = date(2026, 6, 30)
    assert checks.check_report_date(fy, date(2026, 10, 15)).passed
    assert not checks.check_report_date(fy, date(2025, 10, 15)).passed   # before year end
    assert not checks.check_report_date(fy, date(2027, 6, 1)).passed     # past nine months


def test_pdf_roundtrip(tmp_path):
    from reportlab.pdfgen import canvas
    p = tmp_path / "a.pdf"
    c = canvas.Canvas(str(p)); c.drawString(72, 720, "Total expenditures of federal awards $1,240,000"); c.showPage(); c.save()
    pages = pdf_pages(p)
    assert "1,240,000" in pages[0] and not looks_scanned(pages)


def test_period_match():
    from datetime import date
    from ember_ledger.checks import check_period_match
    assert check_period_match(date(2026, 6, 30), date(2026, 6, 30)).passed
    assert not check_period_match(date(2026, 6, 30), date(2025, 6, 30)).passed
