---
scenario: CS-13
title: Off-Channel Communication — Personal Device Usage
status: Implemented
synthetic_data: true
phase: 7
---

# CS-13: Off-Channel Communication — Personal Device Usage

## Narrative

This synthetic Phase 7 trace-through exercises MACMS for a medium compliance case involving `agent-cs-001`. The expected disposition is **HIGH**. No real customer, account, communication, transaction, or regulatory-feed data is used.

## Regulatory Context

Applicable regulations and standards: SEC Rule 17a-4, FINRA Rule 3110, FINRA Regulatory Notice 23-06.

## Initial Detection Signals

- **agent-cs-001**: confidence 0.90; evidence `whatsapp_reps_007, recordkeeping_gap_007`; context `{'personal_device': 'WhatsApp', 'representatives': 7, 'missing_official_channel_records': True, 'negative_signal': 'low_official_channel_volume'}`.

## Expected Outcome

The pipeline must validate all serialized messages, retain one trace correlation ID, apply the appropriate consensus or special handling path, route the case to Tier 2, and prepare: Record-keeping violation report, Remediation plan, Self-reporting recommendation. Reports are draft-only with state `DRAFT_REQUIRES_HUMAN_AUTHORIZATION` unless the scenario is the CS-18 suppression record.

## Confidence Methodology

- CS: Keyword Detection 0.92 + Record-Keeping 0.88.


