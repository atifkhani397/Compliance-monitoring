---
scenario: CS-03
title: Unsuitable Investment Recommendation
status: Implemented
synthetic_data: true
---

# CS-03: Unsuitable Investment Recommendation

## Narrative

This synthetic scenario exercises the MACMS pipeline for a high compliance case. The participating agents are `agent-cs-001, agent-tm-001`. The expected alert disposition is **HIGH**. No real customer, account, or market data is used.

## Regulatory Context

Applicable regulations are: FINRA Rule 2111, SEC Regulation Best Interest.

## Initial Detection Signals

- **agent-cs-001**: confidence 0.89; evidence `advisor_message_001, ips_violation_012`; context `{'retirement_clients': 12, 'client_age_range': '68-82', 'leveraged_etf': True}`.
- **agent-tm-001**: confidence 0.75; evidence `trade_confirmations_012, aum_risk_002`; context `{'aum_at_risk_usd': 2300000, 'clients_executed': 12}`.

## Expected Outcome

The pipeline must validate each inter-agent message, preserve one trace correlation ID, apply the Phase 3 consensus path when applicable, route the case to Tier 2, and prepare the following draft report types: FINRA referral, Client remediation plan, Advisor disciplinary report. Reports are marked `DRAFT_REQUIRES_HUMAN_AUTHORIZATION`.

## Confidence Methodology

- CS: Sentiment Analysis 0.89 + Keyword Detection 0.85 = 0.87.
- TM: Threshold Monitoring = 0.75.
