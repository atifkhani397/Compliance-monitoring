---
scenario: CS-15
title: Best Execution Failure — Systematic Order Routing Bias
status: Implemented
synthetic_data: true
phase: 7
---

# CS-15: Best Execution Failure — Systematic Order Routing Bias

## Narrative

This synthetic Phase 7 trace-through exercises MACMS for a medium compliance case involving `agent-tm-001`. The expected disposition is **HIGH**. No real customer, account, communication, transaction, or regulatory-feed data is used.

## Regulatory Context

Applicable regulations and standards: SEC Rule 606, FINRA Rule 5310, MiFID II Best Execution.

## Initial Detection Signals

- **agent-tm-001**: confidence 0.84; evidence `routing_bias_078, venue_price_gap_015`; context `{'lookback_days': 90, 'single_venue_pct': 78, 'threshold_pct': 50, 'better_venues': 3, 'price_advantage_cents': '0.5-1.5'}`.

## Expected Outcome

The pipeline must validate all serialized messages, retain one trace correlation ID, apply the appropriate consensus or special handling path, route the case to Tier 2, and prepare: Best execution analysis, Venue comparison report, Routing policy review. Reports are draft-only with state `DRAFT_REQUIRES_HUMAN_AUTHORIZATION` unless the scenario is the CS-18 suppression record.

## Confidence Methodology

- TM: Cross-Market Surveillance 0.86 + Threshold Monitoring 0.81.


