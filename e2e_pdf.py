"""End-to-end on real PDF files: synthetic pack -> reportlab PDFs -> pypdf text -> pipeline.
Usage: python3 e2e_pdf.py [live]   (live uses Ember, hard cap $0.10)"""
import sys, tempfile, pathlib
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from ember_ledger.ingest import pdf_pages, looks_scanned
from ember_ledger.ledger import Ledger
from ember_ledger.pipeline import run
from ember_ledger.synth import make_docs

def write_pdf(path, pages):
    c = canvas.Canvas(str(path), pagesize=letter)
    for page in pages:
        y = 740
        for line in page.split("\n"):
            # wrap long lines the way a real report does
            while len(line) > 70:
                cut = line.rfind(" ", 0, 70); cut = cut if cut > 0 else 70
                c.drawString(72, y, line[:cut]); line = line[cut:].lstrip(); y -= 16
            c.drawString(72, y, line); y -= 16
        c.showPage()
    c.save()

d = pathlib.Path(tempfile.mkdtemp())
docs = make_docs(sefa_total_stated=1_250_000, fs_revenue=1_100_000, prior_finding=True)
loaded = {}
for k, pages in docs.items():
    p = d / f"{k}.pdf"; write_pdf(p, pages); loaded[k] = pdf_pages(p)
    print(k, "pages", len(loaded[k]), "scanned?", looks_scanned(loaded[k]))
live = len(sys.argv) > 1 and sys.argv[1] == "live"
led = Ledger(budget=0.10, hard_stop=0.09) if live else Ledger()
if live:
    from ember_ledger.adapter import LiveAdapter; ad = LiveAdapter(led)
else:
    from ember_ledger.fakes import RegexAdapter; ad = RegexAdapter(led)
rep = run(ad, led, loaded, effort="minimal")
print("mode", "live" if live else "regex", "spent $%.5f" % led.spent, "dropped", rep.dropped_unverified)
for f in rep.findings: print(" -", f.code, "|", f.evidence[0]["quote"][:70] if f.evidence else "")
