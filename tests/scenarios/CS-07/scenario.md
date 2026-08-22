---
scenario: CS-07
title: Regulatory Change Impact — New Margin Requirements
status: Implemented
synthetic_data: true
---

# CS-07: Regulatory Change Impact — New Margin Requirements

## Narrative

This synthetic scenario exercises the MACMS pipeline for a medium compliance case. The participating agents are `agent-ru-001`. The expected alert disposition is **MEDIUM**. No real customer, account, or market data is used.

## Regulatory Context

Applicable regulations are: SEC Swap Margin Rule, Basel III CRE54, EMIR Margin Rules.

## Initial Detection Signals

- **agent-ru-001**: confidence N/A; evidence `sec_final_rule_2026, margin_methodology_impact`; context `{'initial_margin_increase_pct': 25, 'effective_days': 120, 'notional_affected_usd': 2100000000, 'counterparties': 340, 'days_to_comply': 45}`.

## Expected Outcome

The pipeline must validate each inter-agent message, preserve one trace correlation ID, apply the Phase 3 consensus path when applicable, route the case to Tier 1, and prepare the following draft report types: Impact assessment report, Implementation timeline, Stakeholder notification. Reports are marked `DRAFT_REQUIRES_HUMAN_AUTHORIZATION`.

## Confidence Methodology

- RU: N/A because this is a regulatory update rather than a violation detection.
