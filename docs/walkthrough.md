# Transcript Intelligence Walkthrough

## 1. Load Data

The received dataset is a folder of 100 meeting-level JSON bundles. `scripts/prepare_real_data.py` converts those bundles into `data/raw/transcripts.csv` with:

- `transcript_id`
- `date`
- `call_type`
- `title`
- `provided_summary`
- `provided_topics`
- `provided_sentiment_score`
- `key_moment_types`
- `key_moment_texts`
- `transcript_text`

Call type is inferred because the JSON files do not include a normalized call-type column:

- `support`: title starts with `Support Case`, `URGENT:`, or `ESCALATION:`
- `external`: non-Aegis participant domain is present
- `internal`: all participants are from `aegiscloud.com`

Run:

```bash
make real-data
make profile
make all
```

`make profile` verifies the normalized CSV before the full report is generated. The pipeline stores the detected mapping in `data/processed/input_profile.json`.

## 2. Topic Classification

I chose a hybrid taxonomy-first approach because this is a small enterprise dataset and the panel should be able to inspect why a transcript received a label.

The classifier:

- Scores weighted phrases per topic.
- Adds small call-type priors.
- Keeps evidence terms on each output row.
- Emits a confidence score based on margin between the top two topics.
- Stores primary and secondary topic scores so ambiguous labels can be reviewed.

This is not meant to beat an LLM on nuance. It is meant to be a trustworthy baseline that can route ambiguous transcripts to an LLM or human review queue without hiding uncertainty.

```bash
make analyze
```

Primary outputs:

- `data/processed/input_profile.json`
- `data/processed/enriched_transcripts.csv`
- `data/processed/topic_summary.csv`
- `data/processed/product_area_summary.csv`
- `data/processed/key_moment_summary.csv`
- `data/processed/classification_review_queue.csv`
- `reports/figures/topic_distribution.svg`

## 3. Sentiment Analysis

Sentiment uses the provided meeting-level sentiment metadata when available. The 1-5 provided score is normalized to -1 to +1 for charting and comparison. If that field is missing, the pipeline falls back to a B2B-specific weighted lexicon.

The score is normalized from -1 to +1:

- `positive` >= 0.25
- `negative` <= -0.25
- otherwise `mixed`

Outputs:

- `data/processed/sentiment_by_call_type.csv`
- `reports/figures/sentiment_by_call_type.svg`

## 4. Additional Insight Signals

Implemented lightweight signals:

- `churn_risk_signal`
- `escalation_signal`
- `product_area`
- `suggested_owner`
- `needs_review`
- `feature_gap_signal`
- `technical_issue_signal`

These make the product more actionable. A stakeholder should not only see "topic = renewal risk"; they should see who owns it, why it matters, and example transcripts.

On the real dataset, the most important views are:

- Detect reliability risk: outage, SLA, alert latency, data gaps, and threat-monitoring visibility loss.
- Comply expansion: audit readiness, multi-framework reporting, and evidence packaging.
- Support early warning: negative support sentiment and technical issue signals.
- Roadmap evidence: feature gaps and integration asks grouped by product area.

## 5. Quality Control and LLM Escalation

The review queue is the answer to when I would use a heavier model. Records are flagged when the taxonomy produces no clear match, low confidence, or a narrow margin between the top two categories.

For production, I would send only those rows to an LLM adjudicator that returns:

- primary and secondary topic
- short rationale with transcript citations
- confidence
- recommended stakeholder owner
- whether human review is still needed

This keeps the deterministic taxonomy as the explainability baseline while using LLMs where nuance matters.

## 6. What I Would Improve With More Time

- Add 30-50 human-labeled examples and report precision/recall by topic.
- Add multi-label classification because many real calls include both product friction and renewal risk.
- Add LLM-generated call summaries and action items with citations to transcript snippets.
- Join CRM/ticketing/product telemetry so transcript themes can be prioritized by ARR, severity, and usage impact.
