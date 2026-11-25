"""Deterministic evidence check: a model finding only counts if its quoted
evidence appears verbatim (after whitespace/case/quote normalization) in the
source document, and we report the page it was found on."""
from __future__ import annotations

import re
from dataclasses import dataclass

_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-"})


def normalize(text: str) -> str:
    text = text.translate(_QUOTES)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


@dataclass(frozen=True)
class Evidence:
    quote: str
    page_hint: int | None = None  # 1-based page the model claims


@dataclass(frozen=True)
class VerifyResult:
    ok: bool
    page: int | None
    reason: str


MIN_QUOTE_CHARS = 12  # reject trivially short "evidence"


def verify_quote(pages: list[str], ev: Evidence) -> VerifyResult:
    q = normalize(ev.quote)
    if len(q) < MIN_QUOTE_CHARS:
        return VerifyResult(False, None, "quote too short")
    norm_pages = [normalize(p) for p in pages]
    if ev.page_hint is not None and 1 <= ev.page_hint <= len(pages):
        if q in norm_pages[ev.page_hint - 1]:
            return VerifyResult(True, ev.page_hint, "found on claimed page")
    for i, p in enumerate(norm_pages, start=1):
        if q in p:
            return VerifyResult(True, i, "found on different page than claimed" if ev.page_hint else "found")
    return VerifyResult(False, None, "quote not found in document")


def verify_finding(pages: list[str], evidence: list[Evidence], min_verified: int = 1) -> tuple[bool, list[VerifyResult]]:
    """A finding passes only if at least `min_verified` evidence quotes verify."""
    results = [verify_quote(pages, e) for e in evidence]
    return sum(r.ok for r in results) >= min_verified, results
