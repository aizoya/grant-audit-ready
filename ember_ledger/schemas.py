"""JSON schemas for constrained-decoding extraction (no recursion, depth <= 10)
and the evidence-linked report model."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict

QUOTE = {"type": "string", "description": "Exact verbatim text copied from the document supporting this value"}

SEFA_SCHEMA = {
    "type": "object",
    "properties": {
        "fiscal_year_start": {"type": "string", "description": "YYYY-MM-DD"},
        "fiscal_year_end": {"type": "string", "description": "YYYY-MM-DD"},
        "rows": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "program": {"type": "string"},
                    "assistance_listing": {"type": "string"},
                    "expended": {"type": "integer", "description": "whole dollars"},
                    "quote": QUOTE,
                },
                "required": ["program", "assistance_listing", "expended", "quote"],
                "additionalProperties": False,
            },
        },
        "stated_total": {"type": "integer"},
        "stated_total_quote": QUOTE,
        "audit_required_statement": {"type": "boolean"},
        "audit_required_quote": QUOTE,
    },
    "required": ["rows", "stated_total", "stated_total_quote"],
    "additionalProperties": False,
}

STATEMENTS_SCHEMA = {
    "type": "object",
    "properties": {
        "federal_revenue": {"type": "integer"},
        "federal_revenue_quote": QUOTE,
        "auditor_report_date": {"type": "string", "description": "YYYY-MM-DD or empty"},
        "auditor_report_quote": QUOTE,
        "statements_year_end": {"type": "string", "description": "Fiscal year end the financial statements cover, YYYY-MM-DD or empty"},
        "statements_year_end_quote": QUOTE,
    },
    "required": ["federal_revenue", "federal_revenue_quote"],
    "additionalProperties": False,
}

PRIOR_AUDIT_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "reference": {"type": "string"},
                    "summary": {"type": "string"},
                    "quote": QUOTE,
                },
                "required": ["reference", "summary", "quote"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["findings"],
    "additionalProperties": False,
}


@dataclass
class ReportFinding:
    code: str            # e.g. sefa_total, sefa_vs_statements, prior_finding_unaddressed
    severity: str        # "review" | "likely" (never "audit opinion")
    message: str
    evidence: list[dict] = field(default_factory=list)  # {quote, page, doc}


@dataclass
class Report:
    findings: list[ReportFinding]
    passed_checks: list[str]
    dropped_unverified: int
    cost_usd: float
    cost_per_verified_finding: float | None
    disclaimer: str = ("Screening aid for the organization and its CPA. Not an audit, "
                       "opinion or legal advice. Every finding quotes the source text.")

    def to_dict(self) -> dict:
        return asdict(self)
