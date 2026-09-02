---
scenario: CS-08
title: Misleading Marketing — Performance Claims
status: Implemented
synthetic_data: true
---

# CS-08: Misleading Marketing — Performance Claims

## Narrative

This synthetic scenario exercises the MACMS pipeline for a low-medium compliance case. The participating agents are `agent-cs-001`. The expected alert disposition is **CRITICAL**. No real customer, account, or market data is used.

## Regulatory Context

Applicable regulations are: SEC Rule 206(4)-1, FINRA Rule 2210, FCA COBS 4.

## Initial Detection Signals

- **agent-cs-001**: confidence 0.96; evidence `marketing_claim_001, stress_loss_analysis_001`; context `{'claimed_return_pct': 12, 'capital_loss_stress_pct': 40, 'guaranteed_claim': True}`.

## Expected Outcome

The pipeline must validate each inter-agent message, preserve one trace correlation ID, apply the Phase 3 consensus path when applicable, route the case to Tier 3, and prepare the following draft report types: Marketing withdrawal order, Client correction notice, Regulatory notification. Reports are marked `DRAFT_REQUIRES_HUMAN_AUTHORIZATION`.

## Confidence Methodology

- CS: Keyword Detection 0.96 + Sentiment Analysis 0.91 = 0.94.
