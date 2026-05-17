"""Validate insert-chapter position and parse user clarifications."""
from __future__ import annotations

import re


def parse_insert_after(text: str) -> int | None:
    """Extract chapter number after which to insert (e.g. 4 → between ch 4 and 5)."""
    t = text.strip().lower()
    patterns = [
        r"between\s+chapter\s+(\d+)\s+and\s+(\d+)",
        r"between\s+(\d+)\s+and\s+(\d+)",
        r"after\s+chapter\s+(\d+)",
        r"after\s+(\d+)",
        r"chapter\s+(\d+)",
        r"^(\d+)$",
    ]
    for pat in patterns:
        m = re.search(pat, t)
        if m:
            return int(m.group(1))
    return None


def validate_insert_after(insert_after: int | None, total_chapters: int) -> tuple[bool, str]:
    if total_chapters < 2:
        return False, "This book has fewer than 2 chapters; cannot insert between chapters."
    if insert_after is None:
        return False, "missing"
    max_after = total_chapters - 1
    if insert_after < 1 or insert_after > max_after:
        return (
            False,
            f"Chapter number must be between **1** and **{max_after}** "
            f"(to insert between chapter {max_after} and {max_after + 1}).",
        )
    return True, ""


def clarification_prompt(total_chapters: int, source_run_id: str) -> str:
    max_after = max(1, total_chapters - 1)
    return (
        f"I need the insert position for book run `{source_run_id}` "
        f"({total_chapters} chapters).\n\n"
        f"**Which chapter should the new chapter follow?**\n"
        f"Reply with a number from **1** to **{max_after}** "
        f"(e.g. `4` inserts between Chapter 4 and Chapter 5)."
    )


def invalid_reply_prompt(total_chapters: int) -> str:
    max_after = max(1, total_chapters - 1)
    return (
        f"That wasn't a valid chapter number. "
        f"Please enter an integer from **1** to **{max_after}**."
    )
