"""Synthetic documents only (no real customer data). Three 'PDFs' as page lists."""
from __future__ import annotations


def make_docs(sefa_total_stated=1_240_000, fs_revenue=1_240_000, line_items=(700_000, 340_000, 200_000),
              prior_finding=True, addressed=False) -> dict[str, list[str]]:
    p = ["Harbor Youth Services Inc.", "Schedule of Expenditures of Federal Awards",
         "For the year ended June 30, 2026"]
    names = [("Head Start Cluster", "93.600"), ("Community Services Block Grant", "93.569"), ("WIOA Youth Activities", "17.259")]
    rows = [f"{n} | ALN {a} | Expended ${v:,}" for (n, a), v in zip(names, line_items)]
    sefa = ["\n".join(p + rows + [f"Total expenditures of federal awards ${sefa_total_stated:,}",
                                   "The organization expended more than the Single Audit threshold and a Single Audit is required."])]
    fs = [f"Statement of Activities, year ended June 30, 2026\nGovernment grants - federal revenue ${fs_revenue:,}\nIndependent Auditor's Report dated October 15, 2026"]
    prior = ["Prior year Schedule of Findings\nFinding 2025-001: Timekeeping records for Head Start staff were not signed by supervisors."]
    if prior_finding and addressed:
        prior.append("Management response to 2025-001: corrective action implemented.")
    return {"sefa": sefa, "statements": fs, "prior": prior}
