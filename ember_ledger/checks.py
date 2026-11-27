"""Deterministic Single Audit rule checks (no model involved).

Sources (read 2026-11-24, secondary; confirm against 2 CFR 200 before relying):
- Threshold: $1,000,000 for fiscal years beginning on/after 2024-10-01,
  $750,000 before (FAC audit submission guide, via Ramp summary).
- Submission due: earlier of 30 calendar days after receipt of the auditor's
  report or nine months after end of the audit period (2 CFR 200.512).
These are screening aids for human review, not audit opinions.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

THRESHOLD_CHANGE = date(2024, 10, 1)


def single_audit_threshold(fy_start: date) -> int:
    return 1_000_000 if fy_start >= THRESHOLD_CHANGE else 750_000


def add_months(d: date, months: int) -> date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    # clamp day to month length
    for day in (d.day, 30, 29, 28):
        try:
            return date(y, m, day)
        except ValueError:
            continue
    raise AssertionError("unreachable")


def submission_due(fy_end: date, auditor_report_received: date | None) -> date:
    nine_months = add_months(fy_end, 9)
    if auditor_report_received is None:
        return nine_months
    return min(auditor_report_received + timedelta(days=30), nine_months)


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


def check_threshold(fy_start: date, federal_expended: int, audit_claimed_required: bool) -> Check:
    t = single_audit_threshold(fy_start)
    required = federal_expended >= t
    ok = required == audit_claimed_required
    return Check(
        "threshold_applicability",
        ok,
        f"expended ${federal_expended:,} vs threshold ${t:,}: audit {'required' if required else 'not required'}; document says "
        f"{'required' if audit_claimed_required else 'not required'}",
    )


def check_sefa_total(line_items: list[int], stated_total: int, tolerance: int = 0) -> Check:
    s = sum(line_items)
    return Check("sefa_total", abs(s - stated_total) <= tolerance, f"line items sum ${s:,} vs stated total ${stated_total:,}")


def check_submission_timeliness(fy_end: date, report_received: date | None, submitted: date) -> Check:
    due = submission_due(fy_end, report_received)
    return Check("submission_timeliness", submitted <= due, f"due {due.isoformat()}, submitted {submitted.isoformat()}")


def check_sefa_vs_statements(sefa_total: int, fs_federal_revenue: int, tolerance: int = 0) -> Check:
    return Check(
        "sefa_vs_financial_statements",
        abs(sefa_total - fs_federal_revenue) <= tolerance,
        f"SEFA ${sefa_total:,} vs financial statement federal revenue ${fs_federal_revenue:,} (differences can be legitimate timing/accrual items: route to human)",
    )


# Reference list of federal programs (Assistance Listing number -> official title).
# Built-in default is a three-program demo list. If data/aln.csv exists (columns: number,title) it replaces the
# default; that file is meant to come from the official SAM.gov Assistance Listings and carries a source line
# in data/aln.SOURCE.txt. We never claim coverage the file does not have.
import csv
import os
import re

_DEFAULT_ALN = {"93.600": "head start", "93.569": "community services block grant", "17.259": "youth workforce"}
_STOP = {"the", "of", "and", "for", "to", "a", "an", "in", "program", "programs", "grant", "grants", "services", "state", "states", "federal"}


def _tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOP and len(t) > 1}


def load_aln(path: str = None) -> dict:
    path = path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "aln.csv")
    if not os.path.exists(path):
        return dict(_DEFAULT_ALN)
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            num, title = (row.get("number") or "").strip(), (row.get("title") or "").strip()
            if re.fullmatch(r"\d{2}\.\d{3}", num) and title:
                out[num] = title.lower()
    return out or dict(_DEFAULT_ALN)


KNOWN_ALN = load_aln()


def _same_program(listed: str, schedule_name: str) -> bool:
    """Lenient on purpose: schedules abbreviate. Match if one contains the other, or most distinctive words overlap."""
    a, b = listed.lower(), schedule_name.lower()
    if a in b or b in a:
        return True
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return True  # not enough words to judge: never raise a finding on that
    return len(ta & tb) / min(len(ta), len(tb)) > 0.5


def _other_listing(program: str, known: dict, exclude: str):
    p = program.lower()
    tp = _tokens(p)
    best = None
    for num, title in known.items():
        if num == exclude:
            continue
        if title in p or (len(title) > 8 and p in title):
            return (num, title)
        tt = _tokens(title)
        shared = tp & tt
        if len(shared) >= 2 and len(shared) / min(len(tp), len(tt)) > 0.6 and best is None:
            best = (num, title)
    return best


def check_aln_program(program: str, aln: str, known: dict = None) -> Check:
    known = KNOWN_ALN if known is None else known
    name = known.get(aln)
    if name is None:
        # A number we do not know is a finding only if the program NAME matches a listed program under another number
        # (then the number is wrong for it). Otherwise it is "not checked", never a finding.
        if len(known) <= 5:
            for known_aln, known_name in known.items():
                if known_name in program.lower():
                    return Check("aln_program_match", False, f"'{program}' is listed under ALN {known_aln}; schedule says {aln}")
        return Check("aln_program_match", True, f"ALN {aln} and '{program}' are not in the reference list: not checked")
    if _same_program(name, program):
        return Check("aln_program_match", True, f"ALN {aln} is listed as '{name}'; schedule says '{program}'")
    # Titles differ. Real schedules use common names, act names and abbreviations, so a different title alone is not a
    # finding. Flag only when the program name clearly belongs to ANOTHER listing (evidence the number is wrong).
    other = _other_listing(program, known, aln)
    if other:
        return Check("aln_program_match", False,
                     f"ALN {aln} is listed as '{name}'; schedule says '{program}', which matches ALN {other[0]} ('{other[1]}')")
    return Check("aln_program_match", True,
                 f"ALN {aln} is listed as '{name}'; schedule says '{program}' (title differs, no other listing matches: not flagged)")


def check_report_date(fy_end: date, report_date: date) -> Check:
    due = add_months(fy_end, 9)
    ok = fy_end < report_date <= due
    return Check("auditor_report_date", ok,
                 f"auditor report dated {report_date.isoformat()}; fiscal year ended {fy_end.isoformat()}; nine-month mark {due.isoformat()}")


def check_period_match(sefa_end: date, statements_end: date) -> Check:
    ok = sefa_end == statements_end
    return Check("period_match", ok, f"SEFA fiscal year ends {sefa_end.isoformat()}; financial statements cover year ended {statements_end.isoformat()}")
