---
scenario: CS-11
title: Data Privacy Violation — Cross-Border Transfer
status: Implemented
synthetic_data: true
phase: 7
---

# CS-11: Data Privacy Violation — Cross-Border Transfer

## Narrative

This synthetic Phase 7 trace-through exercises MACMS for a medium compliance case involving `agent-cs-001, agent-ru-001`. The expected disposition is **HIGH**. No real customer, account, communication, transaction, or regulatory-feed data is used.

## Regulatory Context

Applicable regulations and standards: GDPR Articles 44-49, Schrems II.

## Initial Detection Signals

- **agent-cs-001**: confidence 0.87; evidence `transfer_14000_eu_001, missing_scc_001`; context `{'transfer_to_non_adequate_jurisdiction': True, 'scc_documented': False, 'consent': False}`.
- **agent-ru-001**: confidence 0.95; evidence `schrems_ii_confirmation_001, gdpr_article_44_001`; context `{'regulatory_confirmation': 'GDPR Article 44 requires SCCs', 'privacy_shield_invalidated': True}`.

## Expected Outcome

The pipeline must validate all serialized messages, retain one trace correlation ID, apply the appropriate consensus or special handling path, route the case to Tier 2, and prepare: Data breach notification draft (GDPR Article 33), DPO assessment, Remediation plan. Reports are draft-only with state `DRAFT_REQUIRES_HUMAN_AUTHORIZATION` unless the scenario is the CS-18 suppression record.

## Confidence Methodology

- CS: Keyword Detection 0.89 + Record-Keeping 0.85.
- RU: Regulatory Feed Monitoring 0.95.


