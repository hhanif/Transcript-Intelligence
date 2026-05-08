from __future__ import annotations

import re


def phrase_count(text: str, phrase: str) -> int:
    return len(re.findall(rf"\b{re.escape(phrase.lower())}\b", text.lower()))


def analysis_text(row: dict[str, str]) -> str:
    return " ".join(
        str(row.get(field, ""))
        for field in [
            "title",
            "provided_topics",
            "provided_summary",
            "key_moment_texts",
            "action_items",
            "transcript_text",
        ]
    )


def classification_text(row: dict[str, str]) -> str:
    return " ".join(
        str(row.get(field, ""))
        for field in [
            "title",
            "provided_topics",
            "provided_topics",
            "provided_summary",
            "key_moment_texts",
        ]
    )

