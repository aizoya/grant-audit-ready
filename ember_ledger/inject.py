"""Synthetic error injection with ground truth, plus scoring.

Operates on a list of page strings. Every injection returns the modified pages and a
GroundTruth record. Scoring counts a finding as a hit only if its VERIFIED evidence
quote overlaps the injected span (after normalization). Deterministic given a seed.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass

from .verifier import normalize

CATEGORIES = ("arithmetic", "award_id", "date", "threshold", "prior_finding_omitted")

_MONEY = re.compile(r"\$\s?\d{1,3}(?:,\d{3})+")
_DATE = re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}\b")
_ALN = re.compile(r"\b\d{2}\.\d{3}\b")  # Assistance Listing Number, e.g. 93.558


@dataclass(frozen=True)
class GroundTruth:
    category: str
    page: int  # 1-based
    original: str
    modified: str  # the text that now appears in the document ("" if removed)
    context: str  # normalized snippet around the change that a correct quote would overlap


def _replace_nth(text: str, span: tuple[int, int], new: str) -> str:
    return text[: span[0]] + new + text[span[1]:]


def _ctx(text: str, start: int, end: int, pad: int = 40) -> str:
    return normalize(text[max(0, start - pad): end + pad])


def _pick(pages: list[str], pattern: re.Pattern, rng: random.Random):
    cands = [(i, m) for i, p in enumerate(pages) for m in pattern.finditer(p)]
    return rng.choice(cands) if cands else None


def inject_arithmetic(pages, rng):
    hit = _pick(pages, _MONEY, rng)
    if not hit:
        return None
    i, m = hit
    val = int(re.sub(r"[^\d]", "", m.group()))
    delta = max(1000, int(val * rng.choice([0.03, 0.07, 0.11])))
    new = f"${val + delta:,}"
    p = _replace_nth(pages[i], m.span(), new)
    out = list(pages); out[i] = p
    return out, GroundTruth("arithmetic", i + 1, m.group(), new, _ctx(p, m.start(), m.start() + len(new)))


def inject_award_id(pages, rng):
    hit = _pick(pages, _ALN, rng)
    if not hit:
        return None
    i, m = hit
    prefix, suffix = m.group().split(".")
    new = f"{prefix}.{(int(suffix) + rng.randint(1, 9)) % 1000:03d}"
    if new == m.group():
        return None
    p = _replace_nth(pages[i], m.span(), new)
    out = list(pages); out[i] = p
    return out, GroundTruth("award_id", i + 1, m.group(), new, _ctx(p, m.start(), m.start() + len(new)))


def inject_date(pages, rng):
    hit = _pick(pages, _DATE, rng)
    if not hit:
        return None
    i, m = hit
    year = int(m.group()[-4:])
    new = m.group()[:-4] + str(year + rng.choice([-1, 1]))
    p = _replace_nth(pages[i], m.span(), new)
    out = list(pages); out[i] = p
    return out, GroundTruth("date", i + 1, m.group(), new, _ctx(p, m.start(), m.start() + len(new)))


def inject_threshold(pages, rng):
    """Flip a sentence about audit being required; needs the marker phrase in the document."""
    pat = re.compile(r"(?i)\b(audit (?:was|is) required|audit (?:was|is) not required)\b")
    hit = _pick(pages, pat, rng)
    if not hit:
        return None
    i, m = hit
    new = "audit was not required" if "not" not in m.group().lower() else "audit was required"
    p = _replace_nth(pages[i], m.span(), new)
    out = list(pages); out[i] = p
    return out, GroundTruth("threshold", i + 1, m.group(), new, _ctx(p, m.start(), m.start() + len(new)))


def inject_prior_finding_omitted(pages, rng):
    """Delete the sentence containing 'prior year finding'. Truth context = neighbor text that remains."""
    pat = re.compile(r"[^.\n]*\bprior[- ]year finding[^.\n]*\.", re.I)
    hit = _pick(pages, pat, rng)
    if not hit:
        return None
    i, m = hit
    removed = m.group()
    p = pages[i][: m.start()] + pages[i][m.end():]
    out = list(pages); out[i] = p
    return out, GroundTruth("prior_finding_omitted", i + 1, removed.strip(), "", normalize(p[max(0, m.start() - 60): m.start() + 60]))


_INJECTORS = {
    "arithmetic": inject_arithmetic,
    "award_id": inject_award_id,
    "date": inject_date,
    "threshold": inject_threshold,
    "prior_finding_omitted": inject_prior_finding_omitted,
}


def inject(pages: list[str], category: str, seed: int):
    """Returns (modified_pages, GroundTruth) or None if the document has no suitable site."""
    return _INJECTORS[category](pages, random.Random(seed))


@dataclass(frozen=True)
class Finding:
    category: str
    quote: str  # verified evidence quote
    page: int | None = None


def is_hit(truth: GroundTruth, finding: Finding) -> bool:
    """A finding hits if its (already verified) quote overlaps the injected context window.
    Overlap = the normalized quote and the context share a run of >= 12 characters."""
    q, c = normalize(finding.quote), truth.context
    if len(q) < 12:
        return False
    if q in c or c in q:
        return True
    # sliding run overlap
    for k in range(0, len(q) - 11):
        if q[k: k + 12] in c:
            return True
    return False


@dataclass
class Score:
    injected: int = 0
    detected: int = 0
    false_positive_flags: int = 0  # verified findings that match no injected truth (need human review)

    @property
    def recall(self) -> float | None:
        return None if self.injected == 0 else self.detected / self.injected


def score_document(truth: GroundTruth, findings: list[Finding]) -> Score:
    s = Score(injected=1)
    hit = False
    for f in findings:
        if is_hit(truth, f):
            hit = True
        else:
            s.false_positive_flags += 1
    s.detected = int(hit)
    return s
