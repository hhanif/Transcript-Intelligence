# Transcript Intelligence

This repository is a compact, reviewable solution for Transcript Intelligence. It includes:

- A transcript processing pipeline that categorizes transcripts by topic/theme.
- Sentiment analysis across support, external, and internal call types.
- Additional stakeholder insight ideas, implemented lightweight signals, and a classification review queue.

This repo includes a preparation step that converts the provided dataset of 100 meeting-level JSON bundles into `data/raw/transcripts.csv` with transcript text, title, summary topics, key moments, participant metadata, inferred call type, and provided sentiment metadata.

## Quick Start

```bash
make all
```

That command prepares the real JSON dataset, runs the analysis, and renders the presentation deck svg's. If the JSON dataset is unavailable, the project can still generate transparent synthetic demo data with `make demo-data`.

Open:

- `docs/executive_summary.md` for the written findings.
- `data/processed/enriched_transcripts.csv` for transcript-level labels and scores.
- `data/processed/product_area_summary.csv` and `data/processed/key_moment_summary.csv` for the real-data product and operating signal views.
- `data/processed/classification_review_queue.csv` for low-confidence labels that should route to human or LLM adjudication.
- `docs/walkthrough.md` for the technical walkthrough.

## Input Handling

The primary input is the provided JSON folder. Run:

```bash
make real-data
```

That command writes `data/raw/transcripts.csv`. The downstream pipeline also accepts CSV directly at `data/raw/transcripts.csv` and auto-detects common variants of these columns:

| Column | Required | Notes |
| --- | --- | --- |
| `transcript_id` | no | Stable ID for traceability. If missing, the pipeline generates row IDs. |
| `date` | no | ISO date preferred when available. |
| `call_type` | no | `support`, `external`, or `internal`; aliases are normalized when possible. |
| `transcript_text` | yes | Full transcript text. Common names such as `transcript`, `text`, `content`, and `call_transcript` are detected. |
| `account_segment` | no | Optional segmentation field. |
| `source` | no | Use `original` or `synthetic` for transparency. |

Call type is inferred because the JSON dataset does not include a normalized call-type field:

- `support`: title starts with `Support Case`, `URGENT:`, or `ESCALATION:`
- `external`: non-Aegis participant domain is present
- `internal`: all participants are from `aegiscloud.com`

## Approach

The pipeline intentionally uses a hybrid, auditable approach:

- Topic categorization uses a seed taxonomy with weighted phrases and call-type priors. This is easy to inspect in Q&A and works well on small datasets.
- Sentiment uses the provided meeting-level sentiment metadata when available, normalized to a -1 to +1 score, with a weighted B2B lexicon fallback.
- Additional insight signals identify churn risk, feature gaps, technical issues, escalation loops, product area, owner recommendations, and classification uncertainty.

For a production version, I would add an LLM-assisted classifier only for the review queue first, calibrated against human-labeled examples, while keeping this rule-based layer as an explainability baseline.

## Main Commands

```bash
make profile
make real-data
make demo-data
make analyze
make deck
make clean
```

## Repository Layout

```text
data/
  raw/                  # Put original transcripts here
    transcripts.csv     # Generated from provided JSON bundles
  sample/               # Synthetic demo transcripts
  processed/            # Generated analysis outputs
    input_profile.json
    classification_review_queue.csv
    product_area_summary.csv
    key_moment_summary.csv
figures/              # Generated SVG charts
docs/
  walkthrough.md
  executive_summary.md  # Generated written findings
scripts/
  profile_input.py
  prepare_real_data.py
  generate_synthetic_data.py
src/
  pipeline.py
```