from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
TAXONOMY_CONFIG = CONFIG_DIR / "taxonomy.json"
RAW_INPUT = ROOT / "data" / "raw" / "transcripts.csv"
SAMPLE_INPUT = ROOT / "data" / "sample" / "synthetic_transcripts.csv"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "figures"
REPORT = ROOT / "docs" / "executive_summary.md"

