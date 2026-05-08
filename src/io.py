from __future__ import annotations

import csv
import re
from pathlib import Path

from .paths import RAW_INPUT, SAMPLE_INPUT


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
ID_COLUMN_CANDIDATES = ("transcript_id", "id", "call_id", "meeting_id", "conversation_id")
DATE_COLUMN_CANDIDATES = ("date", "call_date", "created_at", "timestamp", "started_at")
CALL_TYPE_COLUMN_CANDIDATES = ("call_type", "type", "category", "source_type", "meeting_type")

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
        raise SystemExit("No input data found. Run `make demo-data` or add data/raw/transcripts.csv.")

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
    source_label = "provided" if source == RAW_INPUT else "synthetic_take_home_bootstrap"
    for i, row in enumerate(rows, 1):
        clean_row = {key: value for key, value in row.items() if key is not None}
        text = row.get(str(mapping["transcript_text"]), "")
        transcript_id = row.get(str(mapping["transcript_id"]), "").strip() if mapping["transcript_id"] else ""
        date = row.get(str(mapping["date"]), "").strip() if mapping["date"] else ""
        call_type = row.get(str(mapping["call_type"]), "").strip() if mapping["call_type"] else ""
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
        "unknown_call_type_count": sum(1 for row in normalized_rows if row["call_type"] == "unknown"),
    }
    return normalized_rows, profile


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows and not fieldnames:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames or list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
