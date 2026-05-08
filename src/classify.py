from __future__ import annotations

from collections import defaultdict

from .config import topics
from .text import classification_text, phrase_count


def classify_topic(row: dict[str, str]) -> tuple[str, float, list[str], int, str, int, int]:
    """Classify one transcript with a transparent weighted taxonomy."""
    text = classification_text(row).lower()
    taxonomy = topics()
    scores: dict[str, int] = {}
    evidence: dict[str, list[str]] = defaultdict(list)

    for topic, config in taxonomy.items():
        score = int(config["call_type_boost"].get(row["call_type"].lower(), 0))
        for phrase, weight in config["keywords"].items():
            count = phrase_count(text, phrase)
            if count:
                score += count * int(weight)
                evidence[topic].append(phrase)
        scores[topic] = score

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    topic, top_score = ranked[0]
    second_topic, second_score = ranked[1] if len(ranked) > 1 else ("None", 0)
    margin = top_score - second_score
    confidence = 0.0 if top_score == 0 else min(0.99, (top_score - second_score + 3) / (top_score + 3))
    return topic if top_score else "Other", round(confidence, 2), evidence[topic][:5], top_score, second_topic, second_score, margin

