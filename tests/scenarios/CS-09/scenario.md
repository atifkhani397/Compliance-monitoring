---
scenario: CS-09
title: Sanctions Violation — Indirect Counterparty Exposure
status: Implemented
synthetic_data: true
---

# CS-09: Sanctions Violation — Indirect Counterparty Exposure

## Narrative

This synthetic scenario exercises the MACMS pipeline for a high compliance case. The participating agents are `agent-tm-001, agent-ru-001`. The expected alert disposition is **CRITICAL**. No real customer, account, or market data is used.

## Regulatory Context

Applicable regulations are: OFAC Regulations, 31 CFR Part 501, EU Sanctions Regulation.

## Initial Detection Signals

- **agent-tm-001**: confidence 0.94; evidence `wire_intermediary_chain_003, sdn_match_001`; context `{'intermediary_bank_count': 3, 'sdn_added_hours_ago': 48}`.
- **agent-ru-001**: confidence 0.98; evidence `ofac_update_048, enhanced_screening_001`; context `{'regulatory_update_confirmed': True, 'sdn_added_hours_ago': 48}`.

## Expected Outcome

The pipeline must validate each inter-agent message, preserve one trace correlation ID, apply the Phase 3 consensus path when applicable, route the case to Tier 4, and prepare the following draft report types: OFAC compliance report, Transaction hold documentation, Voluntary disclosure draft. Reports are marked `DRAFT_REQUIRES_HUMAN_AUTHORIZATION`.

## Confidence Methodology

- TM: Counterparty Analysis = 0.94.
- RU: Regulatory Feed Monitoring = 0.98.
