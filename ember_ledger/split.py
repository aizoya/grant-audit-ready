"""Split one combined audit report into the three documents the checks need.

Real Single Audit reports are one PDF. This finds the section each page belongs to from its heading, by plain
keyword rules (no model call, no cost). A page with no heading continues the section before it. Pages that
belong to other sections (compliance reports and so on) end the current section so they do not leak in.
If a section cannot be found we say which one, and never guess."""
from __future__ import annotations

import re

# Checked in this order. The first match in the top of the page wins.
_RULES = [
    ("sefa", ["schedule of expenditures of federal awards", "schedules of expenditures of federal awards"]),
    ("prior", ["schedule of findings", "prior year findings", "prior audit findings", "summary schedule of prior audit findings", "schedule of prior audit findings",
               "schedule of findings and questioned costs", "status of prior audit findings"]),
    ("other", ["report on compliance for each major", "report on internal control over financial reporting and on compliance",
               "corrective action plan", "independent auditor's report on compliance",
               "independent auditors' report on compliance"]),
    ("statements", ["statement of financial position", "statements of financial position",
                    "statement of activities", "statements of activities", "statement of net position",
                    "statements of net position", "statement of revenues", "statements of revenues",
                    "statement of cash flows", "statements of cash flows", "balance sheet",
                    "notes to financial statements", "notes to the financial statements",
                    "independent auditor's report", "independent auditors' report", "independent auditor’s report"]),
]
HEAD_LINES = 3  # only the first non-empty lines (organization, title, period) count as the heading


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("’", "'")).strip()


def page_role(text: str) -> str | None:
    lines = [ln for ln in text.splitlines() if ln.strip()][:HEAD_LINES]
    head = _norm(" ".join(lines))
    for role, markers in _RULES:
        if any(m in head for m in markers):
            return role
    return None


def split_package(pages: list[str]) -> dict:
    """Returns {"sefa": [...], "statements": [...], "prior": [...]} page texts, or raises ValueError naming what is missing."""
    out = {"sefa": [], "statements": [], "prior": []}
    current = None
    for text in pages:
        role = page_role(text)
        if role is not None:
            current = role
        if current in out:
            out[current].append(text)
    missing = [k for k, v in out.items() if not v]
    if missing:
        names = {"sefa": "the schedule of expenditures of federal awards", "statements": "the financial statements",
                 "prior": "the schedule of findings or prior findings"}
        raise ValueError("Could not find " + ", ".join(names[m] for m in missing)
                         + " in this PDF. Upload the three parts separately instead.")
    return out
