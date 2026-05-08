from __future__ import annotations

from .paths import REPORT


def write_report(
    enriched: list[dict[str, str]],
    topics: list[dict[str, object]],
    sentiments: list[dict[str, object]],
    product_areas: list[dict[str, object]],
    key_moments: list[dict[str, object]],
    opps: list[dict[str, object]],
    review_queue: list[dict[str, object]],
) -> None:
    """Write the dataset-specific executive narrative from reusable summary tables."""
    top_topic = topics[0]
    lowest_sentiment = min(sentiments, key=lambda row: float(row["avg_sentiment"]))
    top_area = product_areas[0]
    lowest_area = min(product_areas, key=lambda row: float(row["avg_sentiment"]))
    source_note = "synthetic demo data" if enriched and enriched[0].get("source", "").startswith("synthetic") else "the provided JSON transcript dataset"
    lines = [
        "# Executive Summary",
        "",
        f"Analyzed {len(enriched)} transcripts from {source_note}.",
        "",
        "## What Stood Out",
        "",
        f"- The largest theme is **{top_topic['topic']}** ({top_topic['count']} transcripts, {top_topic['pct']:.0%} of the dataset).",
        f"- **{lowest_sentiment['call_type']}** calls have the lowest average sentiment ({lowest_sentiment['avg_sentiment']}).",
        f"- The largest product area is **{top_area['product_area']}** ({top_area['count']} transcripts); the lowest-sentiment product area is **{lowest_area['product_area']}** ({lowest_area['avg_sentiment']}).",
        "- The strongest operating opportunity is not just classification; it is routing transcript evidence to the right owner with a recommended next action.",
        f"- {len(review_queue)} transcripts are flagged for classification review because the taxonomy match is ambiguous.",
        "- Call type is inferred from meeting title patterns and participant domains because the dataset does not include a normalized call-type field.",
        "",
        "## Topic Categories",
        "",
    ]
    for row in topics:
        lines.append(f"- **{row['topic']}**: {row['count']} transcripts; examples: {row['example_transcript_ids']}. {row['why_this_category_matters']}")
    lines.extend(["", "## Sentiment Trends", ""])
    for row in sentiments:
        lines.append(
            f"- **{row['call_type']}**: avg sentiment {row['avg_sentiment']}; "
            f"{row['negative_pct']:.0%} negative, {row['mixed_pct']:.0%} mixed, {row['positive_pct']:.0%} positive."
        )
    lines.extend(["", "## Product Area Trends", ""])
    for row in product_areas:
        lines.append(
            f"- **{row['product_area']}**: {row['count']} transcripts; avg sentiment {row['avg_sentiment']}; "
            f"{row['negative_count']} negative; examples: {row['example_transcript_ids']}."
        )
    lines.extend(["", "## Key Moment Signals", ""])
    for row in key_moments[:6]:
        lines.append(
            f"- **{row['key_moment_type']}**: {row['total']} total "
            f"(support {row['support']}, external {row['external']}, internal {row['internal']})."
        )
    lines.extend(["", "## Additional Insight Ideas", ""])
    for row in opps:
        lines.append(f"- **{row['insight']}** ({row['stakeholder']}): {row['finding']} {row['why_it_matters']}")
    lines.extend(
        [
            "",
            "## Quality Controls",
            "",
            f"- **Classification review queue**: {len(review_queue)} transcripts should be reviewed by a human or LLM adjudicator before using the label in executive reporting.",
            "- **Why this matters**: confidence and margin expose where a simple taxonomy is useful versus where it should defer to a richer model or human judgment.",
            "- **LLM decision**: I would add LLM-assisted classification only for low-confidence or multi-topic calls first, keeping the deterministic taxonomy as the explainability baseline.",
        ]
    )
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            "Ship the first version as an evidence router, not a generic transcript search tool. Start with auditable labels, sentiment, key moments, risk signals, and transcript examples. Add LLM summarization once the taxonomy and owner workflows are trusted.",
        ]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

