"""Deterministic orchestrator. The model only EXTRACTS (with exact quotes);
rules, arithmetic and verification are code. Findings without verified quotes are dropped."""
from __future__ import annotations

import json
from datetime import date

from . import checks
from .ledger import Ledger
from .schemas import (PRIOR_AUDIT_SCHEMA, SEFA_SCHEMA, STATEMENTS_SCHEMA, Report, ReportFinding)
from .verifier import Evidence, verify_quote

RULES_PREFIX = (  # stable, cached prefix: rules first, volatile document last
    "You extract values from grant audit documents. Copy quotes verbatim. "
    "Return only JSON matching the schema. Do not compute or judge."
)


def _doc_text(pages: list[str]) -> str:
    return "\n\n".join(f"[page {i}]\n{p}" for i, p in enumerate(pages, 1))


def _ev(doc: str, pages, quote: str, out: list[dict]) -> bool:
    r = verify_quote(pages, Evidence(quote))
    if r.ok:
        out.append({"doc": doc, "page": r.page, "quote": quote})
    return r.ok


def run(adapter, ledger: Ledger, docs: dict[str, list[str]], effort: str = "minimal") -> Report:
    sefa = adapter.complete("extract_sefa", RULES_PREFIX, _doc_text(docs["sefa"]), SEFA_SCHEMA, effort, 2000)
    fs = adapter.complete("extract_statements", RULES_PREFIX, _doc_text(docs["statements"]), STATEMENTS_SCHEMA, effort, 800)
    prior = adapter.complete("extract_prior", RULES_PREFIX, _doc_text(docs["prior"]), PRIOR_AUDIT_SCHEMA, effort, 2000)

    findings: list[ReportFinding] = []
    passed: list[str] = []
    dropped = 0

    # 1. SEFA internal total
    amounts = [r["expended"] for r in sefa["rows"]]
    c = checks.check_sefa_total(amounts, sefa["stated_total"])
    if c.passed:
        passed.append(c.name)
    else:
        ev: list[dict] = []
        ok = _ev("sefa", docs["sefa"], sefa["stated_total_quote"], ev)
        for r in sefa["rows"]:
            ok &= _ev("sefa", docs["sefa"], r["quote"], ev)
        if ok:
            findings.append(ReportFinding("sefa_total", "likely", c.detail, ev))
        else:
            dropped += 1

    # 2. SEFA vs statements
    c = checks.check_sefa_vs_statements(sefa["stated_total"], fs["federal_revenue"])
    if c.passed:
        passed.append(c.name)
    else:
        ev = []
        ok = _ev("sefa", docs["sefa"], sefa["stated_total_quote"], ev) & _ev("statements", docs["statements"], fs["federal_revenue_quote"], ev)
        if ok:
            findings.append(ReportFinding("sefa_vs_statements", "review", c.detail, ev))
        else:
            dropped += 1

    # 3. Threshold statement (needs fiscal year start)
    if sefa.get("fiscal_year_start") and "audit_required_statement" in sefa:
        c = checks.check_threshold(date.fromisoformat(sefa["fiscal_year_start"]), sefa["stated_total"], sefa["audit_required_statement"])
        if c.passed:
            passed.append(c.name)
        else:
            ev = []
            if _ev("sefa", docs["sefa"], sefa.get("audit_required_quote", ""), ev):
                findings.append(ReportFinding("threshold_applicability", "likely", c.detail, ev))
            else:
                dropped += 1

    # 3b. ALN vs program name (reference list)
    for r in sefa["rows"]:
        c = checks.check_aln_program(r["program"], r["assistance_listing"])
        if c.passed:
            passed.append(f"aln_{r['assistance_listing']}")
        else:
            ev = []
            if _ev("sefa", docs["sefa"], r["quote"], ev):
                findings.append(ReportFinding("aln_program_match", "review", c.detail, ev))
            else:
                dropped += 1

    # 3c. Auditor report date vs fiscal year
    if fs.get("auditor_report_date") and sefa.get("fiscal_year_end"):
        c = checks.check_report_date(date.fromisoformat(sefa["fiscal_year_end"]), date.fromisoformat(fs["auditor_report_date"]))
        if c.passed:
            passed.append(c.name)
        else:
            ev = []
            if _ev("statements", docs["statements"], fs.get("auditor_report_quote", ""), ev):
                findings.append(ReportFinding("auditor_report_date", "review", c.detail, ev))
            else:
                dropped += 1

    # 3d. SEFA period vs financial statements period
    if fs.get("statements_year_end") and sefa.get("fiscal_year_end"):
        c = checks.check_period_match(date.fromisoformat(sefa["fiscal_year_end"]), date.fromisoformat(fs["statements_year_end"]))
        if c.passed:
            passed.append(c.name)
        else:
            ev = []
            if _ev("statements", docs["statements"], fs.get("statements_year_end_quote", ""), ev):
                findings.append(ReportFinding("period_mismatch", "review", c.detail, ev))
            else:
                dropped += 1

    # 4. Prior-year findings with no response text anywhere in this year's pack
    pack = " ".join(" ".join(p) for p in docs.values()).lower()
    for f in prior["findings"]:
        ref = f["reference"].lower()
        if pack.count(ref) <= 1:  # appears only where it was reported
            ev = []
            if _ev("prior", docs["prior"], f["quote"], ev):
                findings.append(ReportFinding("prior_finding_no_followup", "review",
                                              f"Prior finding {f['reference']} has no corrective-action or follow-up text in the pack.", ev))
            else:
                dropped += 1
        else:
            passed.append(f"prior_finding_{f['reference']}_referenced")

    ledger.mark_verified(len(findings))
    return Report(findings, passed, dropped, round(ledger.spent, 6), ledger.cost_per_verified_result)
