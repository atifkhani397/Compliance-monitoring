---
scenario: CS-18
title: FALSE POSITIVE — Legitimate Block Trade
status: Implemented
synthetic_data: true
phase: 7
---

# CS-18: FALSE POSITIVE — Legitimate Block Trade

## Narrative

This synthetic Phase 7 trace-through exercises MACMS for a medium compliance case involving `agent-tm-001`. The expected disposition is **NO ALERT**. No real customer, account, communication, transaction, or regulatory-feed data is used.

## Regulatory Context

Applicable regulations and standards: N/A — negative test.

## Initial Detection Signals

- **agent-tm-001**: confidence 0.65; evidence `block_trade_initial_001`; context `{'block_trade_usd': 450000000, 'adv_pct': 8, 'initial_flag': True, 'pre_arranged': True, 'documentation_confirmed': True, 'disclosed_rebalancing': True, 'known_institutional_client': True, 'revised_confidence': 0.15}`.

## Expected Outcome

The pipeline must validate all serialized messages, retain one trace correlation ID, apply the appropriate consensus or special handling path, route the case to no human escalation, and prepare: No report generated — false-positive suppression record. Reports are draft-only with state `DRAFT_REQUIRES_HUMAN_AUTHORIZATION` unless the scenario is the CS-18 suppression record.

## Confidence Methodology

- TM initial confidence: 0.65 for the volume spike; verified confidence: 0.15 after block-trade documentation, pre-arrangement, disclosed rebalancing, and known-institutional-client checks.

This is the critical negative test. The initial volume flag is verified as a legitimate, pre-arranged $450M block trade. The runner emits `UPDATE` with `false_positive_suppressed`, revised confidence 0.15, and must generate no ALERT and no escalation.
