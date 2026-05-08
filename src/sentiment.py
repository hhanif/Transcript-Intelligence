from __future__ import annotations

from .config import sentiment_lexicons
from .text import analysis_text, phrase_count


def sentiment_score(row: dict[str, str]) -> tuple[float, str]:
    """Return normalized score and label, preferring provided metadata when present."""
    provided_score = str(row.get("provided_sentiment_score", "")).strip()
    if provided_score:
        try:
            raw_score = float(provided_score)
            normalized = max(-1.0, min(1.0, (raw_score - 3.0) / 2.0))
            if raw_score >= 4.0:
                label = "positive"
            elif raw_score <= 2.6:
                label = "negative"
            else:
                label = "mixed"
            return round(normalized, 3), label
        except ValueError:
            pass

    positive, negative = sentiment_lexicons()
    lower = analysis_text(row).lower()
    pos = sum(phrase_count(lower, phrase) * weight for phrase, weight in positive.items())
    neg = sum(phrase_count(lower, phrase) * weight for phrase, weight in negative.items())
    score = 0.0 if pos + neg == 0 else (pos - neg) / (pos + neg)
    if score >= 0.25:
        label = "positive"
    elif score <= -0.25:
        label = "negative"
    else:
        label = "mixed"
    return round(score, 3), label

