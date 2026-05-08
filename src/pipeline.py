from __future__ import annotations

import csv
import html
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_INPUT = ROOT / "data" / "raw" / "transcripts.csv"
SAMPLE_INPUT = ROOT / "data" / "sample" / "synthetic_transcripts.csv"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "figures"

TEXT_COLUMN_CANDIDATES = (
    "transcript_text",
    "transcript",
    "text",
    "body",
    "content",
    "conversation",
    "call_transcript",
    "call_text",
)
ID_COLUMN_CANDIDATES = (
    "transcript_id",
    "id",
    "call_id",
    "meeting_id",
    "conversation_id",
)
DATE_COLUMN_CANDIDATES = ("date", "call_date", "created_at", "timestamp", "started_at")
CALL_TYPE_COLUMN_CANDIDATES = (
    "call_type",
    "type",
    "category",
    "source_type",
    "meeting_type",
)

CALL_TYPE_ALIASES = {
    "customer support": "support",
    "support call": "support",
    "support": "support",
    "ticket": "support",
    "customer": "external",
    "customer call": "external",
    "external": "external",
    "account": "external",
    "account management": "external",
    "sales": "external",
    "csm": "external",
    "internal": "internal",
    "engineering": "internal",
    "eng": "internal",
    "planning": "internal",
    "sync": "internal",
}


TOPICS = {
    "Detect Reliability / Incident Response": {
        "keywords": {
            "outage": 4,
            "platform outage": 5,
            "detect": 4,
            "threat monitoring": 5,
            "pipeline failure": 5,
            "event ingestion": 4,
            "dashboard down": 4,
            "alert latency": 4,
            "data gaps": 4,
            "false positives": 3,
            "latency": 3,
            "incident": 3,
            "sla": 3,
            "post-mortem": 3,
            "root cause": 3,
        },
        "call_type_boost": {"support": 2, "internal": 2, "external": 1},
        "why": "Captures the Detect outage, threat-monitoring visibility failures, incident response, and reliability debt that create customer and revenue risk.",
    },
    "Comply / Audit Readiness": {
        "keywords": {
            "comply": 5,
            "compliance": 1,
            "compliance reporting": 5,
            "soc 2": 5,
            "iso 27001": 5,
            "hipaa": 5,
            "pci dss": 5,
            "audit": 4,
            "evidence": 3,
            "multi-framework": 3,
            "report formatting": 3,
            "custom compliance": 3,
        },
        "call_type_boost": {"external": 2, "support": 1, "internal": 1},
        "why": "Shows where Aegis has strong demand and adoption around audit prep, compliance reporting, and Comply v2.",
    },
    "Identity / Access Management": {
        "keywords": {
            "identity": 5,
            "sso": 4,
            "saml": 4,
            "mfa": 4,
            "scim": 4,
            "ldap": 4,
            "provisioning": 4,
            "rbac": 3,
            "okta": 3,
            "access management": 4,
            "token": 2,
            "certificate": 2,
        },
        "call_type_boost": {"support": 2, "external": 1, "internal": 1},
        "why": "Identifies authentication, provisioning, and policy-management friction across customer support and roadmap discussions.",
    },
    "Protect / Backup Recovery": {
        "keywords": {
            "protect": 5,
            "backup": 5,
            "restore": 4,
            "recovery": 4,
            "disaster recovery": 5,
            "backup window": 4,
            "granular restore": 4,
            "data retention": 3,
            "s3": 3,
            "connector": 2,
            "logvault": 3,
        },
        "call_type_boost": {"support": 2, "external": 1, "internal": 1},
        "why": "Separates backup, restore, connector, and performance needs from Detect and Comply work.",
    },
    "Renewal / Commercial Risk": {
        "keywords": {
            "renewal": 5,
            "churn": 5,
            "competitive": 4,
            "competitor": 4,
            "vendor comparison": 4,
            "contract": 4,
            "pricing": 3,
            "billing": 3,
            "invoice": 3,
            "overage": 3,
            "license": 2,
            "budget": 3,
            "displacement": 4,
        },
        "call_type_boost": {"external": 3, "support": 1},
        "why": "Surfaces where reliability, pricing, or competitive pressure is affecting renewals and account health.",
    },
    "Product Roadmap / Feature Gaps": {
        "keywords": {
            "feature request": 5,
            "feature gap": 5,
            "roadmap": 4,
            "product roadmap": 5,
            "api": 4,
            "integration": 4,
            "custom report": 4,
            "template": 3,
            "rate limiting": 3,
            "pdf export": 3,
            "siem": 3,
            "alert tuning": 3,
        },
        "call_type_boost": {"external": 2, "support": 1, "internal": 1},
        "why": "Turns recurring customer asks and internal roadmap debates into product planning evidence.",
    },
    "Customer Onboarding / Expansion": {
        "keywords": {
            "onboarding": 5,
            "deployment": 4,
            "kickoff": 4,
            "demo": 3,
            "early access": 4,
            "expansion": 4,
            "adoption": 4,
            "cross-sell": 4,
            "workshop": 3,
            "business review": 3,
            "training": 3,
            "product feedback": 3,
        },
        "call_type_boost": {"external": 3, "support": 1},
        "why": "Highlights positive adoption paths, expansion motions, and feedback sessions that can become repeatable playbooks.",
    },
    "Internal Execution / Planning": {
        "keywords": {
            "standup": 5,
            "sprint": 5,
            "planning": 4,
            "retro": 4,
            "all hands": 4,
            "launch readiness": 4,
            "deployment plan": 4,
            "design review": 4,
            "war room": 5,
            "roadmap planning": 4,
            "quarterly planning": 4,
        },
        "call_type_boost": {"internal": 3},
        "why": "Captures internal operating meetings where engineering, product, and GTM teams coordinate launch, reliability, and roadmap work.",
    },
}

POSITIVE = {
    "value": 2,
    "adoption": 2,
    "expansion": 3,
    "training": 1,
    "enablement": 1,
    "clear": 1,
    "aligned": 2,
    "agreed": 1,
    "recommendation": 1,
    "seeing value": 3,
}

NEGATIVE = {
    "outage": 4,
    "downtime": 4,
    "latency": 2,
    "slow": 2,
    "blocked": 3,
    "confusing": 2,
    "risk": 3,
    "cancel": 5,
    "competitor": 3,
    "budget": 2,
    "escalation": 2,
    "bug": 2,
    "disagreed": 2,
    "missing": 2,
    "at risk": 5,
}

PRODUCT_AREAS = {
    "Detect / Threat Monitoring": [
        "detect",
        "threat",
        "alert",
        "pipeline",
        "outage",
        "false positive",
        "monitoring",
        "latency",
    ],
    "Comply / Audit Reporting": [
        "comply",
        "compliance",
        "soc 2",
        "iso 27001",
        "hipaa",
        "pci",
        "audit",
        "evidence",
        "reporting",
    ],
    "Identity / Access": [
        "identity",
        "sso",
        "saml",
        "mfa",
        "scim",
        "ldap",
        "provisioning",
        "rbac",
        "okta",
        "access",
    ],
    "Protect / Backup Recovery": [
        "protect",
        "backup",
        "restore",
        "recovery",
        "s3",
        "data retention",
        "disaster recovery",
        "logvault",
    ],
    "Commercial / Billing": [
        "billing",
        "pricing",
        "invoice",
        "contract",
        "renewal",
        "overage",
        "license",
    ],
}


def normalize_column_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


def pick_column(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    normalized = {normalize_column_name(column): column for column in columns}
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]
    return None


def normalize_call_type(value: str) -> str:
    normalized = normalize_column_name(value).replace("_", " ")
    if normalized in CALL_TYPE_ALIASES:
        return CALL_TYPE_ALIASES[normalized]
    for phrase, call_type in CALL_TYPE_ALIASES.items():
        if phrase in normalized:
            return call_type
    return normalized or "unknown"


def input_mapping(columns: list[str]) -> dict[str, str | None]:
    return {
        "transcript_id": pick_column(columns, ID_COLUMN_CANDIDATES),
        "date": pick_column(columns, DATE_COLUMN_CANDIDATES),
        "call_type": pick_column(columns, CALL_TYPE_COLUMN_CANDIDATES),
        "transcript_text": pick_column(columns, TEXT_COLUMN_CANDIDATES),
    }


def read_input() -> tuple[list[dict[str, str]], dict[str, object]]:
    source = RAW_INPUT if RAW_INPUT.exists() else SAMPLE_INPUT
    if not source.exists():
        raise SystemExit(
            "No input data found. Run `make demo-data` or add data/raw/transcripts.csv."
        )

    with source.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise SystemExit(f"Input file is empty: {source}")

    original_columns = list(rows[0].keys())
    mapping = input_mapping(original_columns)
    if not mapping["transcript_text"]:
        raise SystemExit(
            "Could not find a transcript text column. "
            f"Tried: {', '.join(TEXT_COLUMN_CANDIDATES)}. "
            f"Available columns: {', '.join(original_columns)}"
        )

    normalized_rows = []
    source_label = (
        "provided" if source == RAW_INPUT else "synthetic_take_home_bootstrap"
    )
    for i, row in enumerate(rows, 1):
        clean_row = {key: value for key, value in row.items() if key is not None}
        text = row.get(str(mapping["transcript_text"]), "")
        transcript_id = (
            row.get(str(mapping["transcript_id"]), "").strip()
            if mapping["transcript_id"]
            else ""
        )
        date = row.get(str(mapping["date"]), "").strip() if mapping["date"] else ""
        call_type = (
            row.get(str(mapping["call_type"]), "").strip()
            if mapping["call_type"]
            else ""
        )
        normalized_rows.append(
            {
                **clean_row,
                "transcript_id": transcript_id or f"ROW-{i:03d}",
                "date": date,
                "call_type": normalize_call_type(call_type) if call_type else "unknown",
                "transcript_text": text,
                "source": clean_row.get("source", source_label),
            }
        )

    profile = {
        "input_path": str(source),
        "row_count": len(normalized_rows),
        "original_columns": original_columns,
        "column_mapping": mapping,
        "missing_date_count": sum(1 for row in normalized_rows if not row["date"]),
        "unknown_call_type_count": sum(
            1 for row in normalized_rows if row["call_type"] == "unknown"
        ),
    }

    return normalized_rows, profile


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


def classify_topic(
    row: dict[str, str],
) -> tuple[str, float, list[str], int, str, int, int]:
    text = classification_text(row).lower()
    scores: dict[str, int] = {}
    evidence: dict[str, list[str]] = defaultdict(list)
    for topic, config in TOPICS.items():
        score = int(config["call_type_boost"].get(row["call_type"].lower(), 0))
        for phrase, weight in config["keywords"].items():
            count = phrase_count(text, phrase)
            if count:
                score += count * weight
                evidence[topic].append(phrase)
        scores[topic] = score

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    topic, top_score = ranked[0]
    second_topic, second_score = ranked[1] if len(ranked) > 1 else ("None", 0)
    margin = top_score - second_score
    confidence = (
        0.0
        if top_score == 0
        else min(0.99, (top_score - second_score + 3) / (top_score + 3))
    )
    return (
        topic if top_score else "Other",
        round(confidence, 2),
        evidence[topic][:5],
        top_score,
        second_topic,
        second_score,
        margin,
    )


def sentiment_score(row: dict[str, str]) -> tuple[float, str]:
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

    text = analysis_text(row)
    lower = text.lower()
    pos = sum(
        phrase_count(lower, phrase) * weight for phrase, weight in POSITIVE.items()
    )
    neg = sum(
        phrase_count(lower, phrase) * weight for phrase, weight in NEGATIVE.items()
    )
    score = 0.0 if pos + neg == 0 else (pos - neg) / (pos + neg)
    if score >= 0.25:
        label = "positive"
    elif score <= -0.25:
        label = "negative"
    else:
        label = "mixed"
    return round(score, 3), label


def detect_product_area(text: str) -> str:
    lower = text.lower()
    counts = {
        area: sum(phrase_count(lower, term) for term in terms)
        for area, terms in PRODUCT_AREAS.items()
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
        (
            topic,
            confidence,
            evidence_terms,
            topic_score,
            secondary_topic,
            secondary_score,
            topic_margin,
        ) = classify_topic(row)
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
                    or any(
                        term in lower
                        for term in [
                            "renewal",
                            "churn",
                            "competitor",
                            "competitive",
                            "vendor comparison",
                            "budget",
                            "displacement",
                        ]
                    )
                ).lower(),
                "escalation_signal": str(
                    any(
                        term in lower
                        for term in [
                            "escalation",
                            "urgent",
                            "root cause",
                            "incident",
                            "sla",
                            "p1",
                            "war room",
                        ]
                    )
                ).lower(),
                "feature_gap_signal": str(
                    "feature_gap" in lower
                    or any(
                        term in lower
                        for term in [
                            "feature request",
                            "feature gap",
                            "roadmap",
                            "custom report",
                            "integration",
                            "api",
                        ]
                    )
                ).lower(),
                "technical_issue_signal": str(
                    "technical_issue" in lower
                    or any(
                        term in lower
                        for term in [
                            "bug",
                            "failure",
                            "timeout",
                            "latency",
                            "outage",
                            "error",
                            "regression",
                        ]
                    )
                ).lower(),
            }
        )
    return enriched


def write_csv(
    path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows and not fieldnames:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames or list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def topic_summary(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    total = len(rows)
    by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_topic[row["topic"]].append(row)
    out = []
    for topic, items in sorted(
        by_topic.items(), key=lambda item: len(item[1]), reverse=True
    ):
        call_counts = Counter(item["call_type"] for item in items)
        avg_sent = sum(float(item["sentiment_score"]) for item in items) / len(items)
        out.append(
            {
                "topic": topic,
                "count": len(items),
                "pct": round(len(items) / total, 3),
                "avg_sentiment": round(avg_sent, 3),
                "dominant_call_type": call_counts.most_common(1)[0][0],
                "example_transcript_ids": ", ".join(
                    item["transcript_id"] for item in items[:3]
                ),
                "why_this_category_matters": TOPICS.get(topic, {}).get(
                    "why", "Needs review."
                ),
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
                "avg_sentiment": round(
                    sum(float(item["sentiment_score"]) for item in items) / len(items),
                    3,
                ),
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
    for area, items in sorted(
        by_area.items(), key=lambda item: len(item[1]), reverse=True
    ):
        labels = Counter(item["sentiment_label"] for item in items)
        out.append(
            {
                "product_area": area,
                "count": len(items),
                "avg_sentiment": round(
                    sum(float(item["sentiment_score"]) for item in items) / len(items),
                    3,
                ),
                "negative_count": labels["negative"],
                "dominant_call_type": Counter(
                    item["call_type"] for item in items
                ).most_common(1)[0][0],
                "example_transcript_ids": ", ".join(
                    item["transcript_id"] for item in items[:4]
                ),
            }
        )
    return out


def key_moment_summary(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    counts: dict[tuple[str, str], int] = Counter()
    for row in rows:
        for moment_type in [
            item.strip()
            for item in row.get("key_moment_types", "").split(";")
            if item.strip()
        ]:
            counts[(moment_type, row["call_type"])] += 1
    out = []
    for moment_type in sorted({key[0] for key in counts}):
        total = sum(
            counts[(moment_type, call_type)]
            for call_type in ["support", "external", "internal"]
        )
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
    churn = [
        row
        for row in rows
        if row["churn_risk_signal"] == "true" and row["sentiment_label"] != "positive"
    ]
    reliability = [
        row
        for row in rows
        if row["product_area"] == "Detect / Threat Monitoring"
        and (row["sentiment_label"] == "negative" or row["escalation_signal"] == "true")
    ]
    feature_gaps = [row for row in rows if row["feature_gap_signal"] == "true"]
    negative_support = [
        row
        for row in rows
        if row["call_type"] == "support" and row["sentiment_label"] == "negative"
    ]
    comply_positive = [
        row
        for row in rows
        if row["product_area"] == "Comply / Audit Reporting"
        and row["sentiment_label"] == "positive"
    ]

    return [
        {
            "insight": "Revenue risk queue",
            "stakeholder": "Sales and Customer Success leaders",
            "finding": f"{len(churn)} non-positive meetings contain churn, renewal, competitive, or account-risk signals.",
            "why_it_matters": "The risk is often tied to reliability incidents, so renewal triage needs transcript evidence, not just CRM stage.",
            "suggested_next_step": "Create a weekly save-motion queue sorted by sentiment, churn signal, product area, and account owner.",
            "example_transcript_ids": ", ".join(
                row["transcript_id"] for row in churn[:5]
            ),
        },
        {
            "insight": "Detect reliability command center",
            "stakeholder": "Engineering and Support leaders",
            "finding": f"{len(reliability)} Detect meetings are negative and/or contain escalation or incident language.",
            "why_it_matters": "Detect failures create the worst sentiment, support load, customer communication pressure, and churn risk.",
            "suggested_next_step": "Track incident-linked transcripts by customer, SLA impact, root cause, and follow-up completion.",
            "example_transcript_ids": ", ".join(
                row["transcript_id"] for row in reliability[:5]
            ),
        },
        {
            "insight": "Roadmap evidence map",
            "stakeholder": "Product managers",
            "finding": f"{len(feature_gaps)} meetings contain feature-gap, roadmap, integration, API, or custom reporting language.",
            "why_it_matters": "Customer requests are spread across Comply, Identity, Detect, and Protect; leaders need evidence grouped by product area.",
            "suggested_next_step": "Attach example transcript IDs and account context to each roadmap theme before prioritization.",
            "example_transcript_ids": ", ".join(
                row["transcript_id"] for row in feature_gaps[:5]
            ),
        },
        {
            "insight": "Support sentiment early warning",
            "stakeholder": "Support leadership",
            "finding": f"{len(negative_support)} support meetings are negative.",
            "why_it_matters": "Negative support sentiment clusters around Detect outages, Identity failures, and support response-time complaints.",
            "suggested_next_step": "Compare negative support calls against ticket backlog, incident history, and first-response SLA.",
            "example_transcript_ids": ", ".join(
                row["transcript_id"] for row in negative_support[:5]
            ),
        },
        {
            "insight": "Compliance expansion lane",
            "stakeholder": "Product, Sales, and Customer Success leaders",
            "finding": f"{len(comply_positive)} Comply / Audit Reporting meetings are positive.",
            "why_it_matters": "Comply v2, audit readiness, and multi-framework reporting are the clearest positive growth motion in the dataset.",
            "suggested_next_step": "Package the strongest compliance transcripts into repeatable sales proof points and onboarding playbooks.",
            "example_transcript_ids": ", ".join(
                row["transcript_id"] for row in comply_positive[:5]
            ),
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


def svg_bar_chart(
    path: Path, title: str, values: list[tuple[str, float]], x_label: str = "Count"
) -> None:
    width, height = 900, 520
    left, top, bar_h, gap = 260, 70, 34, 18
    max_value = max((value for _, value in values), default=1)
    rows = []
    for i, (label, value) in enumerate(values):
        y = top + i * (bar_h + gap)
        bar_w = 560 * value / max_value if max_value else 0
        rows.append(
            f'<text x="24" y="{y + 23}" class="label">{html.escape(label)}</text>'
        )
        rows.append(
            f'<rect x="{left}" y="{y}" width="{bar_w:.1f}" height="{bar_h}" rx="4" fill="#2f6f73"/>'
        )
        rows.append(
            f'<text x="{left + bar_w + 10}" y="{y + 23}" class="value">{value:g}</text>'
        )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>.title{{font:700 26px Arial;fill:#172426}}.label{{font:14px Arial;fill:#27383a}}.value{{font:700 14px Arial;fill:#172426}}.axis{{font:12px Arial;fill:#5e7073}}</style>
<rect width="100%" height="100%" fill="#f7f4ef"/>
<text x="24" y="38" class="title">{html.escape(title)}</text>
<text x="{left}" y="{height - 28}" class="axis">{html.escape(x_label)}</text>
{"".join(rows)}
</svg>'''
    path.write_text(svg, encoding="utf-8")


def svg_sentiment(path: Path, rows: list[dict[str, object]]) -> None:
    values = [
        (str(row["call_type"]).title(), float(row["avg_sentiment"])) for row in rows
    ]
    width, height = 900, 420
    mid = 470
    rows_svg = []
    for i, (label, value) in enumerate(values):
        y = 95 + i * 80
        bar_w = abs(value) * 330
        x = mid if value >= 0 else mid - bar_w
        fill = "#3a7d44" if value >= 0 else "#ad3f32"
        rows_svg.append(
            f'<text x="60" y="{y + 24}" class="label">{html.escape(label)}</text>'
        )
        rows_svg.append(
            f'<rect x="{x:.1f}" y="{y}" width="{bar_w:.1f}" height="34" rx="4" fill="{fill}"/>'
        )
        rows_svg.append(
            f'<text x="{mid + 350}" y="{y + 24}" class="value">{value:.2f}</text>'
        )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>.title{{font:700 26px Arial;fill:#172426}}.label{{font:15px Arial;fill:#27383a}}.value{{font:700 15px Arial;fill:#172426}}.axis{{font:12px Arial;fill:#5e7073}}</style>
<rect width="100%" height="100%" fill="#f7f4ef"/>
<text x="24" y="38" class="title">Average sentiment by call type</text>
<line x1="{mid}" x2="{mid}" y1="72" y2="340" stroke="#87979a" stroke-width="2"/>
<text x="{mid - 330}" y="365" class="axis">Negative</text><text x="{mid + 285}" y="365" class="axis">Positive</text>
{"".join(rows_svg)}
</svg>'''
    path.write_text(svg, encoding="utf-8")


def svg_heatmap(path: Path, rows: list[dict[str, str]]) -> None:
    topics = list(TOPICS.keys())
    call_types = sorted(set(row["call_type"] for row in rows))
    counts = Counter((row["topic"], row["call_type"]) for row in rows)
    max_count = max(counts.values(), default=1)
    cell_w, cell_h = 150, 42
    width, height = 1120, 520
    cells = []
    for i, topic in enumerate(topics):
        y = 80 + i * cell_h
        cells.append(
            f'<text x="24" y="{y + 26}" class="label">{html.escape(topic)}</text>'
        )
        for j, call_type in enumerate(call_types):
            x = 430 + j * cell_w
            count = counts[(topic, call_type)]
            opacity = 0.12 + 0.88 * (count / max_count if max_count else 0)
            cells.append(
                f'<rect x="{x}" y="{y}" width="{cell_w - 8}" height="{cell_h - 7}" rx="4" fill="#2f6f73" opacity="{opacity:.2f}"/>'
            )
            cells.append(
                f'<text x="{x + 62}" y="{y + 24}" class="value">{count}</text>'
            )
    headers = "".join(
        f'<text x="{430 + j * cell_w + 34}" y="64" class="header">{html.escape(ct.title())}</text>'
        for j, ct in enumerate(call_types)
    )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>.title{{font:700 26px Arial;fill:#172426}}.label{{font:14px Arial;fill:#27383a}}.header{{font:700 14px Arial;fill:#172426}}.value{{font:700 13px Arial;fill:#172426;text-anchor:middle}}</style>
<rect width="100%" height="100%" fill="#f7f4ef"/>
<text x="24" y="38" class="title">Topic mix by call type</text>
{headers}{"".join(cells)}
</svg>'''
    path.write_text(svg, encoding="utf-8")


def main() -> None:
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
    write_csv(
        PROCESSED / "classification_review_queue.csv",
        review_queue,
        [
            "transcript_id",
            "call_type",
            "topic",
            "secondary_topic",
            "topic_confidence",
            "topic_margin",
            "review_reason",
            "evidence_terms",
            "transcript_excerpt",
        ],
    )
    (PROCESSED / "input_profile.json").write_text(
        json.dumps(input_profile, indent=2), encoding="utf-8"
    )
    (PROCESSED / "summary.json").write_text(
        json.dumps(
            {
                "transcript_count": len(enriched),
                "input_profile": input_profile,
                "call_type_counts": Counter(row["call_type"] for row in enriched),
                "topic_count": len(topics),
                "top_topic": topics[0] if topics else None,
                "lowest_sentiment_call_type": min(
                    sentiments, key=lambda row: float(row["avg_sentiment"])
                )
                if sentiments
                else None,
                "top_product_area": product_areas[0] if product_areas else None,
                "classification_review_count": len(review_queue),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    svg_bar_chart(
        FIGURES / "topic_distribution.svg",
        "Transcript volume by topic",
        [(str(row["topic"]), int(row["count"])) for row in topics],
    )
    svg_bar_chart(
        FIGURES / "product_area_distribution.svg",
        "Transcript volume by product area",
        [(str(row["product_area"]), int(row["count"])) for row in product_areas],
    )
    svg_sentiment(FIGURES / "sentiment_by_call_type.svg", sentiments)
    svg_heatmap(FIGURES / "call_type_topic_heatmap.svg", enriched)

    print(f"Analyzed {len(enriched)} transcripts")
    print(f"Wrote outputs to {PROCESSED}")


if __name__ == "__main__":
    main()
