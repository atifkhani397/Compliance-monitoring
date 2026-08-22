---
scenario: CS-02
title: Market Manipulation — Spoofing in Futures Markets
status: Implemented
synthetic_data: true
---

# CS-02: Market Manipulation — Spoofing in Futures Markets

## Narrative

This synthetic scenario exercises the MACMS pipeline for a medium compliance case. The participating agents are `agent-tm-001`. The expected alert disposition is **HIGH**. No real customer, account, or market data is used.

## Regulatory Context

Applicable regulations are: Dodd-Frank Act Section 747, CEA Section 4c(a)(5), CME Rule 575.

## Initial Detection Signals

- **agent-tm-001**: confidence 0.88; evidence `spoofing_signature_001, cancel_burst_047`; context `{'repetitions': 47, 'cancel_latency_ms': '200-500', 'opposite_side_execution': True}`.

## Expected Outcome

The pipeline must validate each inter-agent message, preserve one trace correlation ID, apply the Phase 3 consensus path when applicable, route the case to Tier 2, and prepare the following draft report types: CFTC referral draft, Internal surveillance report. Reports are marked `DRAFT_REQUIRES_HUMAN_AUTHORIZATION`.

## Confidence Methodology

- TM: Pattern Detection 0.91 + Temporal Analysis 0.85 = 0.88.
