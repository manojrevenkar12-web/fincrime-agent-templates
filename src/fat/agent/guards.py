"""Retrieved text is data. Instruction-like sentences are held back before a model reads it, and every value a
model reports must come with a quote that is in the text and contains the value."""

from __future__ import annotations

import re

SENTENCE = re.compile(r"(?<=[.!?\]])\s+")


class Sanitiser:
    def __init__(self, patterns: list[str]):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in patterns]

    def clean(self, text: str) -> tuple[str, list[str]]:
        kept, removed = [], []
        for s in SENTENCE.split(text):
            (removed if removed or any(p.search(s) for p in self.patterns) else kept).append(s)
        return " ".join(kept), removed


def quoted(text: str, quote: str | None, value: str | None = None) -> bool:
    """The quote is in the text, and the value (if any) is in the quote."""
    if not quote or quote not in text:
        return False
    return value is None or str(value).lower() in quote.lower()
