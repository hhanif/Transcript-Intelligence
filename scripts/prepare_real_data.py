from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_DIR = Path("/Users/harishanif/Downloads/Rubrik/dataset")
OUT = ROOT / "data" / "raw" / "transcripts.csv"


def infer_call_type(title: str, emails: list[str]) -> str:
    lower = title.lower()
    domains = {email.split("@")[-1].lower() for email in emails if "@" in email}
    has_external_participant = any(domain != "aegiscloud.com" for domain in domains)
    if lower.startswith("support case") or lower.startswith("urgent:") or lower.startswith("escalation:"):
        return "support"
    if has_external_participant:
        return "external"
    return "internal"


def account_name(title: str) -> str:
    if " / " in title:
        customer_side = title.split(" / ", 1)[1]
        return re.split(r"\s+-\s+", customer_side, maxsplit=1)[0].strip()
    support_match = re.search(r"-\s+(.+?)\s+(?:Detect|Comply|Slow|Granular|LDAP|LogVault|Custom|Backup|SAML|Invoice|MFA|SCIM|API|SIEM|Group|Data|License|Alert|Recovery|Overage|Complete)", title)
    if support_match:
        return support_match.group(1).strip()
    urgent_match = re.search(r":\s+(.+?)\s+-", title)
    if urgent_match:
        return urgent_match.group(1).strip()
    return ""


def transcript_text(turns: list[dict[str, object]]) -> str:
    lines = []
    for turn in turns:
        speaker = str(turn.get("speaker_name") or f"Speaker {turn.get('speaker_id', '')}").strip()
        sentence = str(turn.get("sentence") or "").strip()
        if sentence:
            lines.append(f"{speaker}: {sentence}")
    return "\n".join(lines)


def load_meeting(meeting_dir: Path) -> dict[str, str]:
    meeting_info = json.loads((meeting_dir / "meeting-info.json").read_text(encoding="utf-8"))
    summary = json.loads((meeting_dir / "summary.json").read_text(encoding="utf-8"))
    transcript = json.loads((meeting_dir / "transcript.json").read_text(encoding="utf-8")).get("data", [])
    emails = meeting_info.get("allEmails", [])
    key_moments = summary.get("keyMoments", [])

    start_time = str(meeting_info.get("startTime", ""))
    return {
        "transcript_id": meeting_dir.name,
        "date": start_time[:10],
        "call_type": infer_call_type(str(meeting_info.get("title", "")), emails),
        "title": str(meeting_info.get("title", "")),
        "account_name": account_name(str(meeting_info.get("title", ""))),
        "duration_minutes": str(meeting_info.get("duration", "")),
        "participant_count": str(len(emails)),
        "external_participant_count": str(sum(1 for email in emails if not str(email).endswith("@aegiscloud.com"))),
        "participant_domains": "; ".join(sorted({email.split("@")[-1] for email in emails if "@" in email})),
        "provided_summary": str(summary.get("summary", "")),
        "provided_topics": "; ".join(str(topic) for topic in summary.get("topics", [])),
        "provided_sentiment_label": str(summary.get("overallSentiment", "")),
        "provided_sentiment_score": str(summary.get("sentimentScore", "")),
        "key_moment_types": "; ".join(str(moment.get("type", "")) for moment in key_moments),
        "key_moment_texts": " | ".join(str(moment.get("text", "")) for moment in key_moments),
        "action_items": " | ".join(str(item) for item in summary.get("actionItems", [])),
        "transcript_turn_count": str(len(transcript)),
        "transcript_text": transcript_text(transcript),
        "source": "provided_json_dataset",
    }


def main() -> None:
    dataset_dir = Path(os.environ.get("RUBRIK_DATASET_DIR", DEFAULT_DATASET_DIR))
    if not dataset_dir.exists():
        raise SystemExit(f"Dataset directory not found: {dataset_dir}")

    rows = []
    for meeting_dir in sorted(path for path in dataset_dir.iterdir() if path.is_dir()):
        required = ["meeting-info.json", "summary.json", "transcript.json"]
        missing = [name for name in required if not (meeting_dir / name).exists()]
        if missing:
            raise SystemExit(f"{meeting_dir} is missing: {', '.join(missing)}")
        rows.append(load_meeting(meeting_dir))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} provided transcript records to {OUT}")


if __name__ == "__main__":
    main()
