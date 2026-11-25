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
