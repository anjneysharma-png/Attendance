"""
Format absent employees list into a single string for WhatsApp.
"""
from typing import Any


def format_message(rows: list[dict[str, Any]]) -> str:
    """
    Turn list into a short message: total count and names only.
    Example: "Absent today: 16\n\n1. Prateek CubexO\n2. Disha Raghuwanshi ..."
    """
    if not rows:
        return "No absent employees today."

    lines = [f"Absent today: {len(rows)}", ""]
    for i, r in enumerate(rows, start=1):
        name = r.get("name", "").strip()
        if name:
            lines.append(f"{i}. {name}")
    return "\n".join(lines)


def split_message(text: str, max_len: int = 4000) -> list[str]:
    """
    Split long message into chunks under max_len (WhatsApp-friendly).
    Returns list of strings.
    """
    if len(text) <= max_len:
        return [text]
    chunks = []
    current = []
    current_len = 0
    for line in text.split("\n"):
        line_len = len(line) + 1
        if current_len + line_len > max_len and current:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += line_len
    if current:
        chunks.append("\n".join(current))
    return chunks
