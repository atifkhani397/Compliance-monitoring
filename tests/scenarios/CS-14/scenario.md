---
scenario: CS-14
title: Late Trading — Mutual Fund NAV Manipulation
status: Implemented
synthetic_data: true
phase: 7
---

# CS-14: Late Trading — Mutual Fund NAV Manipulation

## Narrative

This synthetic Phase 7 trace-through exercises MACMS for a medium compliance case involving `agent-tm-001`. The expected disposition is **CRITICAL**. No real customer, account, communication, transaction, or regulatory-feed data is used.

## Regulatory Context

Applicable regulations and standards: SEC Rule 22c-1, Investment Company Act Section 22(c).

## Initial Detection Signals

- **agent-tm-001**: confidence 0.90; evidence `nav_timestamp_014, late_entry_pattern_001`; context `{'orders': 14, 'official_cutoff': '16:00:00 ET', 'system_entry_window': '16:12-16:23 ET', 'same_day_pricing': True}`.

## Expected Outcome

The pipeline must validate all serialized messages, retain one trace correlation ID, apply the appropriate consensus or special handling path, route the case to Tier 3, and prepare: SEC referral, Fund board notification, Client restitution calculation. Reports are draft-only with state `DRAFT_REQUIRES_HUMAN_AUTHORIZATION` unless the scenario is the CS-18 suppression record.

## Confidence Methodology

- TM: Pattern Detection 0.93 + Temporal Analysis 0.87.


