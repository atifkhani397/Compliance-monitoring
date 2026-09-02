---
scenario: CS-04
title: AML — Structuring Deposits
status: Implemented
synthetic_data: true
---

# CS-04: AML — Structuring Deposits

## Narrative

This synthetic scenario exercises the MACMS pipeline for a medium compliance case. The participating agents are `agent-tm-001`. The expected alert disposition is **CRITICAL**. No real customer, account, or market data is used.

## Regulatory Context

Applicable regulations are: Bank Secrecy Act, 31 CFR 1020.320, FinCEN SAR.

## Initial Detection Signals

- **agent-tm-001**: confidence 0.95; evidence `structuring_pattern_023, branch_spread_007`; context `{'deposit_count': 23, 'branch_count': 7, 'total_usd': 214000, 'amount_range_usd': '8500-9900'}`.

## Expected Outcome

The pipeline must validate each inter-agent message, preserve one trace correlation ID, apply the Phase 3 consensus path when applicable, route the case to Tier 3, and prepare the following draft report types: SAR draft (FinCEN Form 111), Branch alert notification. Reports are marked `DRAFT_REQUIRES_HUMAN_AUTHORIZATION`.

## Confidence Methodology

- TM: Pattern Detection 0.95 + Counterparty Analysis 0.90 = 0.93.
