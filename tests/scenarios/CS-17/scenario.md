---
scenario: CS-17
title: Elder Financial Exploitation
status: Implemented
synthetic_data: true
phase: 7
---

# CS-17: Elder Financial Exploitation

## Narrative

This synthetic Phase 7 trace-through exercises MACMS for a high compliance case involving `agent-tm-001, agent-cs-001`. The expected disposition is **CRITICAL**. No real customer, account, communication, transaction, or regulatory-feed data is used.

## Regulatory Context

Applicable regulations and standards: FINRA Rules 2165 and 4512, SEC Senior Safe Act.

## Initial Detection Signals

- **agent-tm-001**: confidence 0.87; evidence `elder_trade_spike_047, poa_trade_instruction_001`; context `{'client_age': 84, 'trades_in_month': 47, 'historical_monthly_average': 2, 'account_decline_pct': 22, 'poa_filed_weeks_ago': 6}`.
- **agent-cs-001**: confidence 0.85; evidence `coercive_language_001, urgent_dont_tell_002`; context `{'coercive_language': True, 'urgency_tactics': True, 'isolation_tactics': True}`.

## Expected Outcome

The pipeline must validate all serialized messages, retain one trace correlation ID, apply the appropriate consensus or special handling path, route the case to Tier 3, and prepare: Elder exploitation SAR, Adult protective services notification, POA revocation recommendation. Reports are draft-only with state `DRAFT_REQUIRES_HUMAN_AUTHORIZATION` unless the scenario is the CS-18 suppression record.

## Confidence Methodology

- TM: Pattern Detection 0.89 + Counterparty Analysis 0.85.
- CS: Sentiment Analysis 0.87 + Keyword Detection 0.82.


