"""Zero-spend stand-ins for the model so the whole pipeline runs end to end.
RegexAdapter behaves like a competent extractor; LyingAdapter invents quotes to prove the verifier drops them."""
from __future__ import annotations

import re

from .adapter import rough_tokens
from .ledger import Ledger, Usage
import json


class RegexAdapter:
    def __init__(self, ledger: Ledger):
        self.ledger = ledger
        self._seen: set[str] = set()

    def _bill(self, label, prefix, document, out, max_out):
        in_tok = rough_tokens(prefix) + rough_tokens(document)
        self.ledger.preflight(in_tok, max_out)
        cached = rough_tokens(prefix) if prefix in self._seen else 0
        self._seen.add(prefix)
        self.ledger.record(label, Usage(in_tok, rough_tokens(json.dumps(out)), cached))

    def complete(self, label, prefix, document, schema, effort="minimal", max_output_tokens=2000):
        out = getattr(self, "_" + label)(document)
        self._bill(label, prefix, document, out, max_output_tokens)
        return out

    def _extract_sefa(self, doc):
        rows = []
        for m in re.finditer(r"^(.+?) \| ALN ([\d.]+) \| Expended \$([\d,]+)$", doc, re.M):
            rows.append({"program": m.group(1), "assistance_listing": m.group(2),
                         "expended": int(m.group(3).replace(",", "")), "quote": m.group(0)})
        t = re.search(r"Total expenditures of federal awards \$([\d,]+)", doc)
        a = re.search(r"[^.\n]*Single Audit is required\.", doc)
        fy = re.search(r"year ended June 30, (\d{4})", doc)
        out = {"rows": rows, "stated_total": int(t.group(1).replace(",", "")), "stated_total_quote": t.group(0)}
        if fy:
            y = int(fy.group(1))
            out["fiscal_year_start"], out["fiscal_year_end"] = f"{y-1}-07-01", f"{y}-06-30"
        if a:
            out["audit_required_statement"], out["audit_required_quote"] = True, a.group(0).strip()
        return out

    def _extract_statements(self, doc):
        m = re.search(r"Government grants - federal revenue \$([\d,]+)", doc)
        return {"federal_revenue": int(m.group(1).replace(",", "")), "federal_revenue_quote": m.group(0)}

    def _extract_prior(self, doc):
        f = [{"reference": m.group(1), "summary": m.group(2), "quote": m.group(0)}
             for m in re.finditer(r"Finding (\d{4}-\d{3}): (.+?\.)", doc)]
        return {"findings": f}


class LyingAdapter(RegexAdapter):
    """Same extraction, but every quote is fabricated."""

    def complete(self, label, prefix, document, schema, effort="minimal", max_output_tokens=2000):
        out = super().complete(label, prefix, document, schema, effort, max_output_tokens)
        s = json.dumps(out)
        s = re.sub(r'"((?:stated_total_|federal_revenue_|audit_required_)?quote)": "[^"]*"', r'"\1": "fabricated text that is not in the document"', s)
        return json.loads(s)
