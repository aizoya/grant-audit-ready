"""Template B: different wording, layout and program set than synth.py, for generalization checks.
Synthetic only. Never used to tune prompts or rules; scored once per run."""
from __future__ import annotations

_PROGRAMS = [
    ("U.S. Department of Health and Human Services", "Head Start Cluster", "93.600", 812_450),
    ("U.S. Department of Health and Human Services", "Community Services Block Grant", "93.569", 265_300),
    ("U.S. Department of Labor", "WIOA Youth Activities", "17.259", 190_725),
    ("U.S. Department of Agriculture", "Child and Adult Care Food Program", "10.558", 121_000),
    ("U.S. Department of Housing and Urban Development", "Emergency Solutions Grants Program", "14.231", 98_400),
]


def make_docs_b(total_override: int | None = None, fs_revenue_override: int | None = None,
                fy_end: str = "September 30, 2026", report_date: str = "February 12, 2027"):
    total = sum(p[3] for p in _PROGRAMS)
    stated = total_override if total_override is not None else total
    rev = fs_revenue_override if fs_revenue_override is not None else total
    rows = [f"{g} / {n} (Assistance Listing {a}): ${v:,}" for g, n, a, v in _PROGRAMS]
    sefa = [
        "Cedar Valley Family Alliance\nSCHEDULE OF EXPENDITURES OF FEDERAL AWARDS\nFiscal year ended " + fy_end,
        "\n".join(rows) + f"\nTOTAL FEDERAL AWARDS EXPENDED: ${stated:,}",
        "Note 1. Basis of presentation. Because federal expenditures exceeded the threshold, a Single Audit is required "
        "for this fiscal year. Note 2. The prior year finding 2025-003 on subrecipient monitoring was resolved in the current year.",
    ]
    statements = [
        f"Cedar Valley Family Alliance\nStatement of Activities for the year ended {fy_end}\nRevenue from federal grants: ${rev:,}\n"
        f"Independent Auditor's Report dated {report_date}",
    ]
    prior = [
        "Prior year Schedule of Findings and Questioned Costs\nFinding 2025-003: The Alliance did not perform required "
        "monitoring visits of its subrecipients during the year.",
    ]
    return {"sefa": sefa, "statements": statements, "prior": prior}
