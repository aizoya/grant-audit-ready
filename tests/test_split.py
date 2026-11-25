import unittest

from ember_ledger.split import page_role, split_package


def pg(title, body="line items and amounts"):
    return f"Harbor Youth Services Inc.\n{title}\nFor the year ended June 30, 2026\n{body}"


class SplitTests(unittest.TestCase):
    PAGES = [
        pg("Independent Auditor's Report", "We have audited the accompanying financial statements. See the Schedule of Expenditures of Federal Awards."),
        pg("Statement of Financial Position"),
        pg("Statement of Activities"),
        "Notes continued with no heading, still the financial statements.",
        pg("Schedule of Expenditures of Federal Awards"),
        "Notes to the Schedule of Expenditures of Federal Awards\nBasis of presentation",
        pg("Independent Auditor's Report on Compliance for Each Major Federal Program"),
        pg("Schedule of Findings and Questioned Costs"),
        "Finding 2025-001 continued.",
    ]

    def test_heading_beats_body_mentions(self):
        self.assertEqual(page_role(self.PAGES[0]), "statements")  # mentions SEFA in body only
        self.assertEqual(page_role(self.PAGES[6]), "other")

    def test_split_assigns_sections_and_continues_headingless_pages(self):
        parts = split_package(self.PAGES)
        self.assertEqual(len(parts["statements"]), 4)
        self.assertEqual(len(parts["sefa"]), 2)
        self.assertEqual(len(parts["prior"]), 2)      # compliance report page is not included anywhere
        self.assertNotIn("Compliance", " ".join(parts["prior"]).split("Schedule of Findings")[0])

    def test_missing_section_is_named_not_guessed(self):
        with self.assertRaises(ValueError) as cm:
            split_package([pg("Statement of Financial Position")])
        self.assertIn("schedule of expenditures", str(cm.exception))
        self.assertIn("separately", str(cm.exception))


if __name__ == "__main__":
    unittest.main()


class CombinedPdfTests(unittest.TestCase):
    def test_merged_sample_pdfs_run_through_the_api(self):
        import base64
        import io
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            self.skipTest("pypdf not installed")
        from ember_ledger.fakes import RegexAdapter
        from ember_ledger.webapi import handle_check
        w = PdfWriter()
        for n in ("statements", "sefa", "prior"):
            for page in PdfReader(f"public/samples/text-{n}.pdf").pages:
                w.add_page(page)
        buf = io.BytesIO()
        w.write(buf)
        status, body = handle_check({"package": base64.b64encode(buf.getvalue()).decode()}, env={}, ip="split-test",
                                    adapter_factory=lambda led: RegexAdapter(led))
        self.assertEqual(status, 200)
        self.assertEqual({f["code"] for f in body["report"]["findings"]}, {"sefa_total", "sefa_vs_statements"})
