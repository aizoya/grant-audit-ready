import csv
import os
import tempfile
import unittest

from ember_ledger import checks


class AlnListTests(unittest.TestCase):
    def test_default_three_programs_still_work(self):
        self.assertTrue(checks.check_aln_program("Head Start Cluster", "93.600").passed)
        self.assertFalse(checks.check_aln_program("Head Start Cluster", "93.569").passed)

    def test_loads_file_and_flags_wrong_number(self):
        # Synthetic rows made up for this test, not the real catalog.
        rows = [("10.001", "Example Crop Program"), ("20.002", "Example Road Safety Grant")]
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "aln.csv")
            with open(path, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["number", "title"])
                w.writerows(rows)
            known = checks.load_aln(path)
        self.assertEqual(set(known), {"10.001", "20.002"})
        self.assertTrue(checks.check_aln_program("Example Crop Program", "10.001", known).passed)
        self.assertTrue(checks.check_aln_program("Crop Program (Example)", "10.001", known).passed)  # abbreviated order
        self.assertFalse(checks.check_aln_program("Example Road Safety Grant", "10.001", known).passed)

    def test_unknown_number_is_not_a_finding_with_a_big_list(self):
        known = {f"1{i}.00{i}": f"program number {i}" for i in range(9)}
        c = checks.check_aln_program("Anything Else", "99.999", known)
        self.assertTrue(c.passed)
        self.assertIn("not checked", c.detail)

    def test_bad_rows_ignored_and_empty_file_falls_back(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "aln.csv")
            with open(path, "w") as f:
                f.write("number,title\nnot-a-number,Bad\n")
            self.assertEqual(checks.load_aln(path), checks._DEFAULT_ALN)


if __name__ == "__main__":
    unittest.main()
