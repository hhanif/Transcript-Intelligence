from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from charts import svg_bar_chart, svg_heatmap, svg_sentiment
from io import read_input, write_csv
from paths import FIGURES, PROCESSED, REPORT
from reporting import write_report
from signals import enrich
from summaries import (
    classification_review_queue,
    key_moment_summary,
    opportunities,
    product_area_summary,
    sentiment_by_call_type,
    topic_summary,
)


REVIEW_QUEUE_FIELDS = [
    "transcript_id",
    "call_type",
    "topic",
    "secondary_topic",
    "topic_confidence",
    "topic_margin",
    "review_reason",
    "evidence_terms",
    "transcript_excerpt",
]


def build_outputs() -> dict[str, object]:
    rows, input_profile = read_input()
    enriched = enrich(rows)
    topics = topic_summary(enriched)
    sentiments = sentiment_by_call_type(enriched)
    product_areas = product_area_summary(enriched)
    key_moments = key_moment_summary(enriched)
    opps = opportunities(enriched)
    review_queue = classification_review_queue(enriched)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    write_csv(PROCESSED / "enriched_transcripts.csv", enriched)
    write_csv(PROCESSED / "topic_summary.csv", topics)
    write_csv(PROCESSED / "sentiment_by_call_type.csv", sentiments)
    write_csv(PROCESSED / "product_area_summary.csv", product_areas)
    write_csv(PROCESSED / "key_moment_summary.csv", key_moments)
    write_csv(PROCESSED / "insight_opportunities.csv", opps)
    write_csv(PROCESSED / "classification_review_queue.csv", review_queue, REVIEW_QUEUE_FIELDS)

    summary = {
        "transcript_count": len(enriched),
        "input_profile": input_profile,
        "call_type_counts": Counter(row["call_type"] for row in enriched),
        "topic_count": len(topics),
        "top_topic": topics[0] if topics else None,
        "lowest_sentiment_call_type": min(sentiments, key=lambda row: float(row["avg_sentiment"])) if sentiments else None,
        "top_product_area": product_areas[0] if product_areas else None,
        "classification_review_count": len(review_queue),
    }
    (PROCESSED / "input_profile.json").write_text(json.dumps(input_profile, indent=2), encoding="utf-8")
    (PROCESSED / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    svg_bar_chart(FIGURES / "topic_distribution.svg", "Transcript volume by topic", [(str(row["topic"]), int(row["count"])) for row in topics])
    svg_bar_chart(
        FIGURES / "product_area_distribution.svg",
        "Transcript volume by product area",
        [(str(row["product_area"]), int(row["count"])) for row in product_areas],
    )
    svg_sentiment(FIGURES / "sentiment_by_call_type.svg", sentiments)
    svg_heatmap(FIGURES / "call_type_topic_heatmap.svg", enriched)
    write_report(enriched, topics, sentiments, product_areas, key_moments, opps, review_queue)
    return summary


def main() -> None:
    summary = build_outputs()
    print(f"Analyzed {summary['transcript_count']} transcripts")
    print(f"Wrote outputs to {PROCESSED}")
    print(f"Wrote report to {REPORT}")


if __name__ == "__main__":
    main()
