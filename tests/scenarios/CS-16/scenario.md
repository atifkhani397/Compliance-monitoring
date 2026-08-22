---
scenario: CS-16
title: Conflict of Interest — Research Independence
status: Implemented
synthetic_data: true
phase: 7
---

# CS-16: Conflict of Interest — Research Independence

## Narrative

This synthetic Phase 7 trace-through exercises MACMS for a high compliance case involving `agent-cs-001, agent-tm-001`. The expected disposition is **CRITICAL**. No real customer, account, communication, transaction, or regulatory-feed data is used.

## Regulatory Context

Applicable regulations and standards: SEC Regulation AC, FINRA Rule 2241, Global Research Settlement.

## Initial Detection Signals

- **agent-cs-001**: confidence 0.89; evidence `research_rating_change_001, ib_meetings_002`; context `{'attributed_entity': 'analyst_with_ib_pressure', 'rating_change': 'sell_to_buy', 'days_before_offering': 3, 'ib_meetings': 2}`.
- **agent-tm-001**: confidence 0.83; evidence `pre_rating_volume_001, unusual_options_002`; context `{'attributed_entity': 'broader_conspiracy', 'volume_increase_days_before': 2, 'unusual_options_activity': True}`.

## Expected Outcome

The pipeline must validate all serialized messages, retain one trace correlation ID, apply the appropriate consensus or special handling path, route the case to Tier 3, and prepare: Research independence violation, Global Research Settlement compliance review. Reports are draft-only with state `DRAFT_REQUIRES_HUMAN_AUTHORIZATION` unless the scenario is the CS-18 suppression record.

## Confidence Methodology

- CS: Sentiment Analysis 0.91 + Information Barrier 0.87.
- TM: Pattern Detection 0.83.


