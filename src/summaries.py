from __future__ import annotations

from collections import Counter, defaultdict

from .config import topics as taxonomy_topics


def topic_summary(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    total = len(rows)
    by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_topic[row["topic"]].append(row)

    taxonomy = taxonomy_topics()
    out = []
    for topic, items in sorted(by_topic.items(), key=lambda item: len(item[1]), reverse=True):
        call_counts = Counter(item["call_type"] for item in items)
        avg_sent = sum(float(item["sentiment_score"]) for item in items) / len(items)
        out.append(
            {
                "topic": topic,
                "count": len(items),
                "pct": round(len(items) / total, 3),
                "avg_sentiment": round(avg_sent, 3),
                "dominant_call_type": call_counts.most_common(1)[0][0],
                "example_transcript_ids": ", ".join(item["transcript_id"] for item in items[:3]),
                "why_this_category_matters": taxonomy.get(topic, {}).get("why", "Needs review."),
            }
        )
    return out


def sentiment_by_call_type(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    by_type: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_type[row["call_type"]].append(row)
    out = []
    for call_type, items in sorted(by_type.items()):
        labels = Counter(item["sentiment_label"] for item in items)
        out.append(
            {
                "call_type": call_type,
                "count": len(items),
                "avg_sentiment": round(sum(float(item["sentiment_score"]) for item in items) / len(items), 3),
                "positive_pct": round(labels["positive"] / len(items), 3),
                "mixed_pct": round(labels["mixed"] / len(items), 3),
                "negative_pct": round(labels["negative"] / len(items), 3),
            }
        )
    return out


def product_area_summary(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    by_area: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_area[row["product_area"]].append(row)
    out = []
    for area, items in sorted(by_area.items(), key=lambda item: len(item[1]), reverse=True):
        labels = Counter(item["sentiment_label"] for item in items)
        out.append(
            {
                "product_area": area,
                "count": len(items),
                "avg_sentiment": round(sum(float(item["sentiment_score"]) for item in items) / len(items), 3),
                "negative_count": labels["negative"],
                "dominant_call_type": Counter(item["call_type"] for item in items).most_common(1)[0][0],
                "example_transcript_ids": ", ".join(item["transcript_id"] for item in items[:4]),
            }
        )
    return out


def key_moment_summary(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    counts: dict[tuple[str, str], int] = Counter()
    for row in rows:
        for moment_type in [item.strip() for item in row.get("key_moment_types", "").split(";") if item.strip()]:
            counts[(moment_type, row["call_type"])] += 1
    out = []
    for moment_type in sorted({key[0] for key in counts}):
        total = sum(counts[(moment_type, call_type)] for call_type in ["support", "external", "internal"])
        out.append(
            {
                "key_moment_type": moment_type,
                "total": total,
                "support": counts[(moment_type, "support")],
                "external": counts[(moment_type, "external")],
                "internal": counts[(moment_type, "internal")],
            }
        )
    return sorted(out, key=lambda row: int(row["total"]), reverse=True)


def opportunities(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    churn = [row for row in rows if row["churn_risk_signal"] == "true" and row["sentiment_label"] != "positive"]
    reliability = [
        row
        for row in rows
        if row["product_area"] == "Detect / Threat Monitoring"
        and (row["sentiment_label"] == "negative" or row["escalation_signal"] == "true")
    ]
    feature_gaps = [row for row in rows if row["feature_gap_signal"] == "true"]
    negative_support = [row for row in rows if row["call_type"] == "support" and row["sentiment_label"] == "negative"]
    comply_positive = [row for row in rows if row["product_area"] == "Comply / Audit Reporting" and row["sentiment_label"] == "positive"]

    return [
        {
            "insight": "Revenue risk queue",
            "stakeholder": "Sales and Customer Success leaders",
            "finding": f"{len(churn)} non-positive meetings contain churn, renewal, competitive, or account-risk signals.",
            "why_it_matters": "The risk is often tied to reliability incidents, so renewal triage needs transcript evidence, not just CRM stage.",
            "suggested_next_step": "Create a weekly save-motion queue sorted by sentiment, churn signal, product area, and account owner.",
            "example_transcript_ids": ", ".join(row["transcript_id"] for row in churn[:5]),
        },
        {
            "insight": "Detect reliability command center",
            "stakeholder": "Engineering and Support leaders",
            "finding": f"{len(reliability)} Detect meetings are negative and/or contain escalation or incident language.",
            "why_it_matters": "Detect failures create the worst sentiment, support load, customer communication pressure, and churn risk.",
            "suggested_next_step": "Track incident-linked transcripts by customer, SLA impact, root cause, and follow-up completion.",
            "example_transcript_ids": ", ".join(row["transcript_id"] for row in reliability[:5]),
        },
        {
            "insight": "Roadmap evidence map",
            "stakeholder": "Product managers",
            "finding": f"{len(feature_gaps)} meetings contain feature-gap, roadmap, integration, API, or custom reporting language.",
            "why_it_matters": "Customer requests are spread across Comply, Identity, Detect, and Protect; leaders need evidence grouped by product area.",
            "suggested_next_step": "Attach example transcript IDs and account context to each roadmap theme before prioritization.",
            "example_transcript_ids": ", ".join(row["transcript_id"] for row in feature_gaps[:5]),
        },
        {
            "insight": "Support sentiment early warning",
            "stakeholder": "Support leadership",
            "finding": f"{len(negative_support)} support meetings are negative.",
            "why_it_matters": "Negative support sentiment clusters around Detect outages, Identity failures, and support response-time complaints.",
            "suggested_next_step": "Compare negative support calls against ticket backlog, incident history, and first-response SLA.",
            "example_transcript_ids": ", ".join(row["transcript_id"] for row in negative_support[:5]),
        },
        {
            "insight": "Compliance expansion lane",
            "stakeholder": "Product, Sales, and Customer Success leaders",
            "finding": f"{len(comply_positive)} Comply / Audit Reporting meetings are positive.",
            "why_it_matters": "Comply v2, audit readiness, and multi-framework reporting are the clearest positive growth motion in the dataset.",
            "suggested_next_step": "Package the strongest compliance transcripts into repeatable sales proof points and onboarding playbooks.",
            "example_transcript_ids": ", ".join(row["transcript_id"] for row in comply_positive[:5]),
        },
    ]


def classification_review_queue(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    queue = []
    for row in rows:
        if row["needs_review"] != "true":
            continue
        reason = "No clear taxonomy match"
        if row["topic"] != "Other":
            reason = "Low topic confidence"
            if int(row["topic_margin"]) <= 2:
                reason = "Low margin between primary and secondary topic"
        queue.append(
            {
                "transcript_id": row["transcript_id"],
                "call_type": row["call_type"],
                "topic": row["topic"],
                "secondary_topic": row["secondary_topic"],
                "topic_confidence": row["topic_confidence"],
                "topic_margin": row["topic_margin"],
                "review_reason": reason,
                "evidence_terms": row["evidence_terms"],
                "transcript_excerpt": row["transcript_text"][:220].replace("\n", " "),
            }
        )
    return queue
