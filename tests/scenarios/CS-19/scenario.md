---
scenario: CS-19
title: Multi-Jurisdiction Regulatory Conflict
status: Implemented
synthetic_data: true
phase: 7
---

# CS-19: Multi-Jurisdiction Regulatory Conflict

## Narrative

This synthetic Phase 7 trace-through exercises MACMS for a high compliance case involving `agent-ru-001`. The expected disposition is **HIGH**. No real customer, account, communication, transaction, or regulatory-feed data is used.

## Regulatory Context

Applicable regulations and standards: EMIR Reporting Obligation, MAS Securities and Futures Act.

## Initial Detection Signals

- **agent-ru-001**: confidence 0.50; evidence `emir_one_day_reporting_001, mas_cross_border_restriction_001`; context `{'confidence_methodology': 'N/A: regulatory conflict', 'affected_jurisdictions': ['EU', 'Singapore'], 'conflicting_regulations': ['EMIR', 'MAS_SFA'], 'legal_counsel_required': True}`.

## Expected Outcome

The pipeline must validate all serialized messages, retain one trace correlation ID, apply the appropriate consensus or special handling path, route the case to Tier 4, and prepare: Regulatory conflict analysis, Legal opinion request, Jurisdictional compliance strategy. Reports are draft-only with state `DRAFT_REQUIRES_HUMAN_AUTHORIZATION` unless the scenario is the CS-18 suppression record.

## Confidence Methodology

- RU: N/A because this is a regulatory conflict rather than a violation detection; legal counsel determines precedence.

Type E regulatory conflict handling is special: no consensus algorithm is applied. The RU alert goes directly to Tier 4 with mandatory legal-counsel engagement.
