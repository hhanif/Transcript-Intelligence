from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from transcript_intelligence.io import (  # noqa: E402
    RAW_INPUT,
    SAMPLE_INPUT,
    TEXT_COLUMN_CANDIDATES,
    input_mapping,
    normalize_call_type,
)


def main() -> None:
    source = RAW_INPUT if RAW_INPUT.exists() else SAMPLE_INPUT
    if not source.exists():
        raise SystemExit("No input found. Add data/raw/transcripts.csv or run `make demo-data`.")

    with source.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise SystemExit(f"Input file is empty: {source}")

    columns = list(rows[0].keys())
    mapping = input_mapping(columns)
    text_column = mapping["transcript_text"]
    call_type_column = mapping["call_type"]

    print(f"Input: {source}")
    print(f"Rows: {len(rows)}")
    print(f"Columns: {', '.join(columns)}")
    print("Detected mapping:")
    for canonical, actual in mapping.items():
        print(f"  {canonical}: {actual or 'not found'}")

    if not text_column:
        print(f"Text column not found. Tried: {', '.join(TEXT_COLUMN_CANDIDATES)}")
        raise SystemExit(1)

    if call_type_column:
        counts = Counter(normalize_call_type(row.get(call_type_column, "")) for row in rows)
        print("Call types:")
        for call_type, count in counts.most_common():
            print(f"  {call_type}: {count}")
    else:
        print("Call types: no call type column found; pipeline will use `unknown`.")

    missing_text = sum(1 for row in rows if not row.get(text_column, "").strip())
    print(f"Missing transcript text rows: {missing_text}")

    excerpt = rows[0].get(text_column, "").replace("\n", " ")[:260]
    print(f"First transcript excerpt: {excerpt}")


if __name__ == "__main__":
    main()
