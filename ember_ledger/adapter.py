"""Model adapter. The stub lets us develop and test with ZERO spend.
The live adapter is intentionally not enabled until Franklyn approves spending
and credits exist; the key must come from the environment, never from code or chat."""
from __future__ import annotations

import json
import os
from typing import Protocol

from .ledger import Ledger, Usage

MODEL_ID = "muse-ember-1.0"
# Endpoint per third-party guide (typingmind): https://api.meta.ai/v1/responses
# UNVERIFIED against dev.meta.ai/docs/quickstart - confirm before first live call.
RESPONSES_URL = "https://api.meta.ai/v1/responses"


class ModelAdapter(Protocol):
    def complete(self, label: str, prefix: str, document: str, schema: dict, effort: str, max_output_tokens: int) -> dict: ...


def rough_tokens(text: str) -> int:
    """Crude estimate (~4 chars/token) used ONLY for preflight; real accounting uses usage fields."""
    return max(1, len(text) // 4)



def strictify(schema):
    """Strict structured output needs every property listed in required (verified live)."""
    if isinstance(schema, dict):
        out = {k: strictify(v) for k, v in schema.items()}
        if out.get("type") == "object" and "properties" in out:
            out["required"] = list(out["properties"].keys())
            out["additionalProperties"] = False
        return out
    if isinstance(schema, list):
        return [strictify(v) for v in schema]
    return schema


class StubAdapter:
    """Deterministic fake: returns a canned JSON answer and plausible usage."""

    def __init__(self, ledger: Ledger, canned: dict):
        self.ledger = ledger
        self.canned = canned
        self.seen_prefixes: set[str] = set()

    def complete(self, label, prefix, document, schema, effort="low", max_output_tokens=4000):
        in_tok = rough_tokens(prefix) + rough_tokens(document)
        self.ledger.preflight(in_tok, max_output_tokens)
        cached = rough_tokens(prefix) if prefix in self.seen_prefixes else 0
        self.seen_prefixes.add(prefix)
        out_tok = rough_tokens(json.dumps(self.canned))
        self.ledger.record(label, Usage(in_tok, out_tok, cached))
        return self.canned


class LiveAdapter:
    """Responses API adapter (base URL confirmed on dev.meta.ai quickstart: https://api.meta.ai/v1).
    Request shape follows the quickstart + docs; the structured-output field (text.format) and usage
    fields are checked by probe.py on the first live call. Key comes only from the environment."""

    BASE = "https://api.meta.ai/v1"

    def __init__(self, ledger: Ledger):
        self.ledger = ledger
        self.key = os.environ.get("META_MODEL_API_KEY") or os.environ.get("MODEL_API_KEY")
        if not self.key:
            raise RuntimeError("META_MODEL_API_KEY not set (provided via environment, never in chat or git)")

    def complete(self, label, prefix, document, schema, effort="minimal", max_output_tokens=2000):
        import urllib.request

        in_est = rough_tokens(prefix) + rough_tokens(document)
        self.ledger.preflight(in_est, max_output_tokens)  # worst-case check before spending
        body = {
            "model": MODEL_ID,
            "input": [{"role": "system", "content": prefix}, {"role": "user", "content": document}],
            "reasoning": {"effort": effort},
            "max_output_tokens": max_output_tokens,
            "text": {"format": {"type": "json_schema", "name": label, "schema": strictify(schema), "strict": True}},
            "temperature": 0,
            "prompt_cache_retention": "24h",
        }
        req = urllib.request.Request(f"{self.BASE}/responses", data=json.dumps(body).encode(),
                                     headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read())
        self.ledger.record(label, Usage.from_responses_api(resp["usage"]))
        text = "".join(c.get("text", "") for o in resp.get("output", []) if o.get("type") == "message" for c in o.get("content", []))
        return json.loads(text)


READ_SCHEMA = {
    "type": "object",
    "properties": {"pages": {"type": "array", "items": {"type": "object", "properties": {
        "page": {"type": "integer", "description": "1-based page number"},
        "text": {"type": "string", "description": "Everything printed on that page, in reading order"}},
        "required": ["page", "text"], "additionalProperties": False}}},
    "required": ["pages"], "additionalProperties": False,
}

READ_PROMPTS = {
    "a": ("Transcribe every page of this scanned document exactly as printed, in reading order. "
          "Keep every number, symbol and punctuation mark exactly as shown. Do not correct, translate, "
          "summarize or infer anything. If text is unreadable write [unreadable]. Return JSON only."),
    "b": ("Read this scanned document page by page. For each page return all text line by line, "
          "writing each table row on its own line with columns separated by ' | '. Copy numbers digit "
          "for digit. Never fix or guess a value. If text is unreadable write [unreadable]. Return JSON only."),
}
EST_TOKENS_PER_PAGE = 2500  # conservative preflight guess for page image + text; real usage is recorded after the call


def _read_pdf(self, label, raw, n_pages, variant="a", effort="minimal"):
    """Native PDF input: the model reads the page images and returns a transcript per page.
    Preflight uses a worst-case estimate; the ledger records real usage from the response."""
    import base64 as _b64
    import urllib.request

    max_out = 900 * n_pages + 400
    self.ledger.preflight(EST_TOKENS_PER_PAGE * n_pages + 400, max_out)
    data = "data:application/pdf;base64," + _b64.b64encode(raw).decode()
    body = {
        "model": MODEL_ID,
        "input": [{"type": "message", "role": "user", "content": [
            {"type": "input_text", "text": READ_PROMPTS[variant]},
            {"type": "input_file", "filename": "document.pdf", "file_data": data}]}],
        "reasoning": {"effort": effort},
        "max_output_tokens": max_out,
        "text": {"format": {"type": "json_schema", "name": label, "schema": strictify(READ_SCHEMA), "strict": True}},
        "temperature": 0,
    }
    req = urllib.request.Request(f"{self.BASE}/responses", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.loads(r.read())
    self.ledger.record(label, Usage.from_responses_api(resp["usage"]))
    text = "".join(c.get("text", "") for o in resp.get("output", []) if o.get("type") == "message" for c in o.get("content", []))
    pages = json.loads(text)["pages"]
    out = [""] * n_pages
    for pg in pages:
        i = int(pg["page"]) - 1
        if 0 <= i < n_pages:
            out[i] = pg["text"]
    return out


LiveAdapter.read_pdf = _read_pdf
