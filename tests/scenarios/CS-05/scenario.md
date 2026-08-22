---
scenario: CS-05
title: Chinese Wall Breach — Information Leakage
status: Implemented
synthetic_data: true
---

# CS-05: Chinese Wall Breach — Information Leakage

## Narrative

This synthetic scenario exercises the MACMS pipeline for a high compliance case. The participating agents are `agent-cs-001`. The expected alert disposition is **CRITICAL**. No real customer, account, or market data is used.

## Regulatory Context

Applicable regulations are: SEC Section 15(g), FINRA Rule 5280, MiFID II Article 16.

## Initial Detection Signals

- **agent-cs-001**: confidence 0.93; evidence `message_881, barrier_event_005`; context `{'message_phrase': "Don't cover TechCorp next week, trust me", 'report_delayed': True}`.

## Expected Outcome

The pipeline must validate each inter-agent message, preserve one trace correlation ID, apply the Phase 3 consensus path when applicable, route the case to Tier 3, and prepare the following draft report types: Internal investigation report, SEC notification, Deal team isolation protocol. Reports are marked `DRAFT_REQUIRES_HUMAN_AUTHORIZATION`.

## Confidence Methodology

- CS: Keyword Detection 0.93 + Information Barrier 0.88 = 0.91.
