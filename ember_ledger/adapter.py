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
