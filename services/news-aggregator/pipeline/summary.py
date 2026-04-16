"""Truncate or extract a 5-line summary from raw text."""
import re


MAX_LINES = 5
MAX_CHARS = 400


def make_summary(text: str) -> str:
    """Return a clean summary of at most 5 sentences / 400 chars."""
    if not text:
        return ""

    # Split into sentences
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    # Take up to 5 sentences
    summary = " ".join(sentences[:MAX_LINES])

    # Hard cap on characters
    if len(summary) > MAX_CHARS:
        summary = summary[:MAX_CHARS].rsplit(" ", 1)[0] + "…"

    return summary
