---
scenario: CS-10
title: Front-Running — Client Order Anticipation
status: Implemented
synthetic_data: true
---

# CS-10: Front-Running — Client Order Anticipation

## Narrative

This synthetic scenario exercises the MACMS pipeline for a medium compliance case. The participating agents are `agent-tm-001`. The expected alert disposition is **CRITICAL**. No real customer, account, or market data is used.

## Regulatory Context

Applicable regulations are: SEC Section 17(j), Investment Company Act Section 17(j), FINRA Rule 5270.

## Initial Detection Signals

- **agent-tm-001**: confidence 0.90; evidence `personal_trade_lead_089, client_order_timing_010`; context `{'profitable_trade_pct': 89, 'average_return_pct': 2.3, 'lead_time_minutes': '10-30'}`.

## Expected Outcome

The pipeline must validate each inter-agent message, preserve one trace correlation ID, apply the Phase 3 consensus path when applicable, route the case to Tier 3, and prepare the following draft report types: Internal disciplinary report, Client notification, Regulatory referral. Reports are marked `DRAFT_REQUIRES_HUMAN_AUTHORIZATION`.

## Confidence Methodology

- TM: Pattern Detection 0.90 + Temporal Analysis 0.85 = 0.88.
