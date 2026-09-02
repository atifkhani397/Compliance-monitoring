---
scenario: CS-12
title: Concentration Risk — Portfolio Limit Breach
status: Implemented
synthetic_data: true
phase: 7
---

# CS-12: Concentration Risk — Portfolio Limit Breach

## Narrative

This synthetic Phase 7 trace-through exercises MACMS for a low compliance case involving `agent-tm-001`. The expected disposition is **MEDIUM**. No real customer, account, communication, transaction, or regulatory-feed data is used.

## Regulatory Context

Applicable regulations and standards: Investment Company Act Section 13, SEC Form N-PORT, UCITS concentration limits.

## Initial Detection Signals

- **agent-tm-001**: confidence 0.75; evidence `sector_concentration_028, limit_025_001`; context `{'concentration_pct': 28, 'limit_pct': 25, 'persistent_trading_days': 5}`.

## Expected Outcome

The pipeline must validate all serialized messages, retain one trace correlation ID, apply the appropriate consensus or special handling path, route the case to Tier 1, and prepare: Prospectus deviation report, Portfolio rebalancing recommendation. Reports are draft-only with state `DRAFT_REQUIRES_HUMAN_AUTHORIZATION` unless the scenario is the CS-18 suppression record.

## Confidence Methodology

- TM: Threshold Monitoring 0.78 + Temporal Analysis 0.72.


