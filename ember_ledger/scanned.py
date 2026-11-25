"""Scanned-document mode. A page with no text layer is read by the model (native PDF input) TWICE with
different instructions. The first read becomes the page text the rest of the pipeline quotes from.
A finding survives only if its quote is found in read 1 AND every number in the quote also appears on the
same page in read 2. This is weaker than a real text layer, so the report says so."""
from __future__ import annotations

import re

_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")

ASSURANCE = ("Scanned pages were read by the model twice. A finding is kept only if its quote and every number in it "
             "match on both reads. This is not the same as checking a text layer: review the page image yourself.")


def numbers(text: str) -> set[str]:
    return {n.replace(",", "").rstrip(".") for n in _NUM.findall(text)}


def confirmed(quote: str, page_text_b: str) -> bool:
    """Every number in the quote must appear on the same page in the second read."""
    need = numbers(quote)
    return need <= numbers(page_text_b)


def read_two_ways(adapter, raw: bytes, n_pages: int, label: str) -> tuple[list[str], list[str]]:
    a = adapter.read_pdf(f"read_{label}_a", raw, n_pages, "a")
    b = adapter.read_pdf(f"read_{label}_b", raw, n_pages, "b")
    return a, b


def read_all(adapter, jobs: dict[str, tuple[bytes, int]]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """jobs: slot -> (raw pdf bytes, page count). Runs every read (two per slot) at the same time."""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max(1, 2 * len(jobs))) as ex:
        futs = {(slot, v): ex.submit(adapter.read_pdf, f"read_{slot}_{v}", raw, n, v)
                for slot, (raw, n) in jobs.items() for v in ("a", "b")}
        a = {slot: futs[(slot, "a")].result() for slot in jobs}
        b = {slot: futs[(slot, "b")].result() for slot in jobs}
    return a, b
