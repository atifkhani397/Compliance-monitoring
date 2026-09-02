---
scenario: CS-06
title: Wash Trading — Cross-Account Coordination
status: Implemented
synthetic_data: true
---

# CS-06: Wash Trading — Cross-Account Coordination

## Narrative

This synthetic scenario exercises the MACMS pipeline for a high compliance case. The participating agents are `agent-tm-001`. The expected alert disposition is **HIGH**. No real customer, account, or market data is used.

## Regulatory Context

Applicable regulations are: CEA Section 4c(a), SEC Rule 10b-5, FINRA Rule 5210.

## Initial Detection Signals

- **agent-tm-001**: confidence 0.87; evidence `wash_trade_034, circular_counterparty_002`; context `{'matching_trades': 34, 'price_tolerance_bps': 2, 'alternating_sides': True}`.

## Expected Outcome

The pipeline must validate each inter-agent message, preserve one trace correlation ID, apply the Phase 3 consensus path when applicable, route the case to Tier 2, and prepare the following draft report types: Exchange referral, Internal trading desk review. Reports are marked `DRAFT_REQUIRES_HUMAN_AUTHORIZATION`.

## Confidence Methodology

- TM: Pattern Detection 0.87 + Counterparty Analysis 0.82 = 0.85.
