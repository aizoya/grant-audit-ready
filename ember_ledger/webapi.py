"""Web layer for the hosted demo: JSON in, JSON out. Uploaded files are read in memory and never stored.

Public demo rules: synthetic documents only; every request runs under its own tiny cost cap;
the API key comes from the server environment and is never returned or logged."""
from __future__ import annotations

import base64
import binascii
import os
import time
from collections import defaultdict, deque

from .adapter import LiveAdapter
from .ingest import looks_scanned, pdf_pages_from_bytes
from .ledger import BudgetExceeded, Ledger
from .pipeline import run
from .scanned import ASSURANCE, read_all

SLOTS = ("sefa", "statements", "prior")
MAX_FILE_BYTES = 1_500_000
MAX_PAGES = 40
MAX_CHARS = 60_000
MAX_SCANNED_PAGES = 12          # per scanned document (page images cost more than text)
PER_REQUEST_BUDGET = 0.05      # USD; a real run costs about 0.0004
PER_REQUEST_HARD_STOP = 0.04
RATE_LIMIT = (12, 3600)        # requests per IP per window, best effort per server instance

_hits: dict[str, deque] = defaultdict(deque)


class UserError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def _rate_ok(ip: str, now: float | None = None) -> bool:
    now = time.time() if now is None else now
    n, window = RATE_LIMIT
    q = _hits[ip]
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= n:
        return False
    q.append(now)
    return True


def _pages(b64: str, slot: str):
    """Returns (pages, raw_bytes, is_scanned). Scanned PDFs return empty page text; the model reads them later."""
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise UserError(f"The {slot} file could not be read.")
    if not raw.startswith(b"%PDF"):
        raise UserError(f"The {slot} file is not a PDF.")
    if len(raw) > MAX_FILE_BYTES:
        raise UserError(f"The {slot} PDF is larger than {MAX_FILE_BYTES // 1_000_000:.1f} MB.", 413)
    try:
        pages = pdf_pages_from_bytes(raw)
    except Exception:
        raise UserError(f"The {slot} PDF could not be opened.")
    scanned = looks_scanned(pages)
    if len(pages) > (MAX_SCANNED_PAGES if scanned else MAX_PAGES):
        raise UserError(f"The {slot} PDF has more than {MAX_SCANNED_PAGES if scanned else MAX_PAGES} pages"
                        f"{' (scanned limit)' if scanned else ''}.", 413)
    if not scanned and sum(len(p) for p in pages) > MAX_CHARS:
        raise UserError(f"The {slot} PDF has too much text for the public demo.", 413)
    return pages, raw, scanned


def handle_check(payload: dict, env: dict | None = None, ip: str = "unknown", adapter_factory=None):
    """Returns (http_status, body_dict)."""
    env = os.environ if env is None else env
    if not isinstance(payload, dict) or not isinstance(payload.get("docs"), dict):
        return 400, {"ok": False, "error": "bad_request", "message": "Send {docs: {sefa, statements, prior}} as base64 PDFs."}
    if env.get("LIVE_DISABLED"):
        return 503, {"ok": False, "error": "live_unavailable",
                     "message": "The live model is switched off right now. The recorded sample runs still work."}
    if not _rate_ok(ip):
        return 429, {"ok": False, "error": "rate_limited", "message": "Too many checks from this address. Try again later."}
    try:
        missing = [s for s in SLOTS if not payload["docs"].get(s)]
        if missing:
            raise UserError("Missing: " + ", ".join(missing) + ".")
        loaded = {s: _pages(payload["docs"][s], s) for s in SLOTS}
    except UserError as e:
        return e.status, {"ok": False, "error": "invalid_upload", "message": str(e)}

    docs = {s: loaded[s][0] for s in SLOTS}
    scanned_slots = [s for s in SLOTS if loaded[s][2]]
    ledger = Ledger(budget=PER_REQUEST_BUDGET, hard_stop=PER_REQUEST_HARD_STOP)
    try:
        adapter = adapter_factory(ledger) if adapter_factory else LiveAdapter(ledger)
    except RuntimeError:
        return 503, {"ok": False, "error": "live_unavailable",
                     "message": "The live model is not available right now. The recorded sample runs still work."}
    confirm = None
    try:
        if scanned_slots:
            first, confirm = read_all(adapter, {s_: (loaded[s_][1], len(loaded[s_][0])) for s_ in scanned_slots})
            docs.update(first)
        report = run(adapter, ledger, docs, confirm=confirm)
    except BudgetExceeded:
        return 429, {"ok": False, "error": "budget", "message": "This pack is too large for the public demo cost cap."}
    except Exception:
        return 502, {"ok": False, "error": "model_error", "message": "The model call failed. Nothing was stored. Try again."}
    body = {"ok": True, "mode": "live", "model": "muse-ember-1.0", "calls": ledger.calls,
            "report": report.to_dict(), "docs": docs}
    if scanned_slots:
        body["scanned"] = scanned_slots
        body["assurance"] = ASSURANCE
    return 200, body
