"""PDF -> list of page strings. Text-layer PDFs only (scanned pages need the model's PDF input; later)."""
from __future__ import annotations

from pathlib import Path


def pdf_pages(path: str | Path) -> list[str]:
    from pypdf import PdfReader  # local import keeps core importable without pypdf
    reader = PdfReader(str(path))
    return [(p.extract_text() or "") for p in reader.pages]


def looks_scanned(pages: list[str], min_chars: int = 40) -> bool:
    """True if most pages carry almost no text (likely image-only)."""
    if not pages:
        return True
    empty = sum(len(p.strip()) < min_chars for p in pages)
    return empty / len(pages) > 0.5


def pdf_pages_from_bytes(raw: bytes) -> list[str]:
    """Same as pdf_pages for an in-memory upload. Nothing is written to disk."""
    import io
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(raw))
    return [(p.extract_text() or "") for p in reader.pages]
