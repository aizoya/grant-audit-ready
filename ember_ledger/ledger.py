"""Cost ledger for Muse Ember (muse-ember-1.0).

Rates come from https://dev.meta.ai/docs/pricing-rate-limits (read 2026-11-24).
UNVERIFIED until the first live probe: whether reasoning tokens are included in
`output_tokens`. We conservatively bill all `output_tokens` at the output rate.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field

# USD per 1M tokens. Tier is chosen by TOTAL input tokens (cached included);
# if a request exceeds the threshold, the long rates apply to the WHOLE request.
LONG_CONTEXT_THRESHOLD = 200_000
RATES = {
    "short": {"cached": 0.004, "input": 0.10, "output": 0.50},
    "long": {"cached": 0.012, "input": 0.30, "output": 1.50},
}


class BudgetExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class Usage:
    input_tokens: int  # includes cached tokens (docs: cached is a subset of input)
    output_tokens: int
    cached_tokens: int = 0

    def __post_init__(self):
        if min(self.input_tokens, self.output_tokens, self.cached_tokens) < 0:
            raise ValueError("negative token count")
        if self.cached_tokens > self.input_tokens:
            raise ValueError("cached_tokens cannot exceed input_tokens")

    @classmethod
    def from_responses_api(cls, usage: dict) -> "Usage":
        details = usage.get("input_tokens_details") or {}
        return cls(
            input_tokens=int(usage["input_tokens"]),
            output_tokens=int(usage["output_tokens"]),
            cached_tokens=int(details.get("cached_tokens", 0)),
        )


def tier_for(input_tokens: int) -> str:
    return "long" if input_tokens > LONG_CONTEXT_THRESHOLD else "short"


def cost_usd(usage: Usage) -> float:
    r = RATES[tier_for(usage.input_tokens)]
    uncached = usage.input_tokens - usage.cached_tokens
    total = (
        usage.cached_tokens * r["cached"]
        + uncached * r["input"]
        + usage.output_tokens * r["output"]
    ) / 1_000_000
    return total


def worst_case_usd(input_tokens: int, max_output_tokens: int) -> float:
    """Upper bound before sending a request: nothing cached, full output used."""
    r = RATES[tier_for(input_tokens)]
    return (input_tokens * r["input"] + max_output_tokens * r["output"]) / 1_000_000


@dataclass
class Ledger:
    """Hard-stop budget meter. `hard_stop` < `budget` leaves a safety margin."""

    budget: float = 10.00
    hard_stop: float = 9.00
    spent: float = 0.0
    calls: int = 0
    by_label: dict = field(default_factory=dict)
    verified_results: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def preflight(self, input_tokens: int, max_output_tokens: int) -> float:
        worst = worst_case_usd(input_tokens, max_output_tokens)
        if self.spent + worst > self.hard_stop:
            raise BudgetExceeded(
                f"refused: spent ${self.spent:.4f} + worst case ${worst:.4f} "
                f"> hard stop ${self.hard_stop:.2f}"
            )
        return worst

    def record(self, label: str, usage: Usage) -> float:
        c = cost_usd(usage)
        with self._lock:
            self.spent += c
            self.calls += 1
            self.by_label[label] = self.by_label.get(label, 0.0) + c
        return c

    def mark_verified(self, n: int = 1) -> None:
        self.verified_results += n

    @property
    def cost_per_verified_result(self) -> float | None:
        if self.verified_results == 0:
            return None
        return self.spent / self.verified_results

    def remaining(self) -> float:
        return self.budget - self.spent
