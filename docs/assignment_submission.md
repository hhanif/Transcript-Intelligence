# Assignment Submission

## Required Task 1: Topic or Theme Categorization

- Code: `src/pipeline.py`, `src/classify.py`, `config/taxonomy.json`
- Output: `data/processed/enriched_transcripts.csv`
- Summary: `data/processed/topic_summary.csv`
- Visualization: `figures/topic_distribution.svg`

The approach is a hybrid taxonomy baseline: weighted real-dataset phrases, small call-type priors, evidence terms, primary/secondary scores, and a confidence margin. The taxonomy is tuned to the actual dataset but lives in `config/taxonomy.json`, so a reviewer can adjust themes without editing pipeline code.

## Required Task 2: Sentiment by Call Type

- Code: `src/pipeline.py`, `src/sentiment.py`
- Output: `data/processed/sentiment_by_call_type.csv`
- Visualization: `figures/sentiment_by_call_type.svg`
- Written interpretation: `docs/executive_summary.md`

The sentiment score uses the provided meeting-level sentiment metadata when available and normalizes it to -1 to +1. The pipeline has a domain-specific lexicon fallback for records without provided sentiment.

## Required Task 3: Additional Insight Ideas

- Output: `data/processed/insight_opportunities.csv`
- Written interpretation: `docs/executive_summary.md`

## Deliverables

- Code repository / notebook-style walkthrough: `README.md` and `docs/walkthrough.md`

## Data Note

The received dataset is a folder of 100 meeting-level JSON bundles. `scripts/prepare_real_data.py` converts those bundles into `data/raw/transcripts.csv` before analysis. A different source folder can be passed with `RUBRIK_DATASET_DIR=/path/to/dataset`.

The source JSON has no normalized call-type field, so call type is inferred from title patterns and participant domains. The inferred rule is documented in `README.md` and the pipeline output keeps source metadata for review.

## LLM Decision

I would not start with an LLM-only classifier. The first version should preserve auditable evidence and confidence. The right place for LLM assistance is `data/processed/classification_review_queue.csv`, where low-confidence or close-margin transcript labels can be adjudicated with transcript citations.
