from __future__ import annotations

from .classify import classify_topic
from .config import product_areas
from .sentiment import sentiment_score
from .text import analysis_text, phrase_count


def detect_product_area(text: str) -> str:
    lower = text.lower()
    counts = {
        area: sum(phrase_count(lower, term) for term in terms)
        for area, terms in product_areas().items()
    }
    area, count = max(counts.items(), key=lambda item: item[1])
    return area if count else "Unclear"


def detect_owner(topic: str) -> str:
    if topic == "Detect Reliability / Incident Response":
        return "Engineering + Support"
    if topic in {
        "Comply / Audit Readiness",
        "Product Roadmap / Feature Gaps",
        "Identity / Access Management",
        "Protect / Backup Recovery",
    }:
        return "Product + Customer Success"
    if topic in {"Renewal / Commercial Risk", "Customer Onboarding / Expansion"}:
        return "Sales / Customer Success"
    return "Product / Engineering Leadership"


def enrich(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    enriched = []
    for row in rows:
        topic, confidence, evidence_terms, topic_score, secondary_topic, secondary_score, topic_margin = classify_topic(row)
        score, label = sentiment_score(row)
        context = analysis_text(row)
        lower = context.lower()
        needs_review = topic == "Other" or confidence < 0.35 or topic_margin <= 1
        product_area = detect_product_area(lower)
        enriched.append(
            {
                **row,
                "topic": topic,
                "topic_confidence": f"{confidence:.2f}",
                "topic_score": str(topic_score),
                "secondary_topic": secondary_topic,
                "secondary_topic_score": str(secondary_score),
                "topic_margin": str(topic_margin),
                "needs_review": str(needs_review).lower(),
                "evidence_terms": "; ".join(evidence_terms),
                "sentiment_score": f"{score:.3f}",
                "sentiment_label": label,
                "product_area": product_area,
                "suggested_owner": detect_owner(topic),
                "churn_risk_signal": str(
                    "churn_signal" in lower
                    or any(term in lower for term in ["renewal", "churn", "competitor", "competitive", "vendor comparison", "budget", "displacement"])
                ).lower(),
                "escalation_signal": str(any(term in lower for term in ["escalation", "urgent", "root cause", "incident", "sla", "p1", "war room"])).lower(),
                "feature_gap_signal": str(
                    "feature_gap" in lower
                    or any(term in lower for term in ["feature request", "feature gap", "roadmap", "custom report", "integration", "api"])
                ).lower(),
                "technical_issue_signal": str(
                    "technical_issue" in lower
                    or any(term in lower for term in ["bug", "failure", "timeout", "latency", "outage", "error", "regression"])
                ).lower(),
            }
        )
    return enriched

