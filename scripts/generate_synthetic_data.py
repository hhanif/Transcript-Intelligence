from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "sample" / "synthetic_transcripts.csv"


SCENARIOS = [
    {
        "topic": "Reliability and incident pain",
        "call_type": "support",
        "sentiment": "negative",
        "terms": ["outage", "latency", "SLA", "ticket", "downtime", "escalation"],
        "customer": "The dashboard was slow during month-end close and our team opened three tickets.",
        "agent": "Support confirmed the incident, linked the SLA report, and promised a postmortem.",
    },
    {
        "topic": "Workflow configuration friction",
        "call_type": "support",
        "sentiment": "mixed",
        "terms": ["permissions", "setup", "configuration", "workflow", "export", "blocked"],
        "customer": "The approval workflow is powerful, but permissions are confusing for regional admins.",
        "agent": "Support walked through the configuration and tagged the product team on the export issue.",
    },
    {
        "topic": "Renewal and churn risk",
        "call_type": "external",
        "sentiment": "negative",
        "terms": ["renewal", "budget", "competitor", "cancel", "adoption", "risk"],
        "customer": "The renewal is at risk because budget is tight and a competitor promised faster onboarding.",
        "agent": "The account manager proposed an executive review and success plan before procurement starts.",
    },
    {
        "topic": "Expansion and adoption",
        "call_type": "external",
        "sentiment": "positive",
        "terms": ["adoption", "training", "expansion", "use case", "champion", "value"],
        "customer": "The analytics team is seeing value and wants training for two more business units.",
        "agent": "The CSM documented the expansion path and offered a champion enablement session.",
    },
    {
        "topic": "Feature request and roadmap fit",
        "call_type": "external",
        "sentiment": "mixed",
        "terms": ["feature request", "integration", "roadmap", "API", "dashboard", "priority"],
        "customer": "The product works, but the missing API integration limits adoption in finance.",
        "agent": "The account team captured the feature request and asked product to validate roadmap fit.",
    },
    {
        "topic": "Cross-team escalation",
        "call_type": "internal",
        "sentiment": "negative",
        "terms": ["handoff", "escalation", "root cause", "ownership", "bug", "incident"],
        "customer": "Internal teams disagreed on ownership while a high-priority customer escalation aged.",
        "agent": "Engineering, support, and product aligned on the root cause and named a single owner.",
    },
    {
        "topic": "Planning and prioritization",
        "call_type": "internal",
        "sentiment": "mixed",
        "terms": ["planning", "prioritization", "tradeoff", "roadmap", "capacity", "deadline"],
        "customer": "The planning discussion centered on tradeoffs between roadmap commitments and reliability work.",
        "agent": "Leads agreed to reserve capacity for customer-impacting issues and publish the decision log.",
    },
    {
        "topic": "Voice of customer synthesis",
        "call_type": "internal",
        "sentiment": "positive",
        "terms": ["feedback", "customer evidence", "trend", "product area", "recommendation", "insight"],
        "customer": "Product managers reviewed recurring feedback and found repeated friction in onboarding.",
        "agent": "The team grouped customer evidence by product area and created recommendations for the next sprint.",
    },
]


SEGMENTS = ["Enterprise", "Mid-Market", "Strategic", "Commercial"]
NAMES = ["Avery", "Jordan", "Morgan", "Riley", "Casey", "Taylor", "Sam", "Devon"]


def build_transcript(i: int, scenario: dict[str, str]) -> str:
    speaker_a = random.choice(NAMES)
    speaker_b = random.choice([n for n in NAMES if n != speaker_a])
    terms = ", ".join(random.sample(scenario["terms"], k=3))
    return "\n".join(
        [
            f"{speaker_a}: Thanks for joining. I want to focus on {terms}.",
            f"{speaker_b}: {scenario['customer']}",
            f"{speaker_a}: {scenario['agent']}",
            f"{speaker_b}: The most important next step is clear ownership and a timeline.",
            f"{speaker_a}: I will summarize actions, owners, and risks in the follow-up note.",
        ]
    )


def main() -> None:
    random.seed(42)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    start = date(2026, 1, 5)
    rows = []
    for i in range(100):
        scenario = random.choices(
            SCENARIOS,
            weights=[15, 12, 13, 13, 14, 12, 11, 10],
            k=1,
        )[0]
        rows.append(
            {
                "transcript_id": f"SYN-{i + 1:03d}",
                "date": (start + timedelta(days=i % 90)).isoformat(),
                "call_type": scenario["call_type"],
                "account_segment": random.choice(SEGMENTS),
                "source": "synthetic_take_home_bootstrap",
                "transcript_text": build_transcript(i, scenario),
            }
        )

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} synthetic transcripts to {OUT}")


if __name__ == "__main__":
    main()
