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
    """Not wired yet. Raises until approval + key + verified endpoint."""

    def __init__(self, ledger: Ledger):
        self.ledger = ledger
        self.key = os.environ.get("META_MODEL_API_KEY")
        if not self.key:
            raise RuntimeError("META_MODEL_API_KEY not set (Franklyn provides it via environment; never paste in chat)")

    def complete(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError("Live calls disabled until spend approval and endpoint verification")
