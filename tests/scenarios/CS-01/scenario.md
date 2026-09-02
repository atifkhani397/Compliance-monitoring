---
scenario: CS-01
title: Insider Trading — Pre-Announcement Accumulation
status: Implemented
synthetic_data: true
---

# CS-01: Insider Trading — Pre-Announcement Accumulation

## Narrative

This synthetic scenario exercises the MACMS pipeline for a high compliance case. The participating agents are `agent-tm-001, agent-cs-001`. The expected alert disposition is **CRITICAL**. No real customer, account, or market data is used.

## Regulatory Context

Applicable regulations are: SEC Rule 10b-5, FINRA Rule 2010, Insider Trading Sanctions Act.

## Initial Detection Signals

- **agent-tm-001**: confidence 0.79; evidence `trade_pattern_001, volume_anomaly_002`; context `{'position_above_90_day_average_pct': 340, 'buy_orders_clustered_before_close': True}`.
- **agent-cs-001**: confidence 0.90; evidence `email_4452, calendar_entry_892`; context `{'private_dinner': True, 'official_channel_follow_up': False}`.

## Expected Outcome

The pipeline must validate each inter-agent message, preserve one trace correlation ID, apply the Phase 3 consensus path when applicable, route the case to Tier 3, and prepare the following draft report types: SAR filing draft (FinCEN Form 111), Internal investigation report, Regulatory notification draft (SEC). Reports are marked `DRAFT_REQUIRES_HUMAN_AUTHORIZATION`.

## Confidence Methodology

- TM: Pattern Detection 0.82 + Temporal Analysis 0.75 = weighted 0.79.
- CS: Keyword Detection 0.88 + Information Barrier 0.91 = weighted 0.90.
