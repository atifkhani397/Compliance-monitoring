---
scenario: CS-20
title: COORDINATED SCENARIO — Complex Money Laundering through Trade Finance
status: Implemented
synthetic_data: true
phase: 7
---

# CS-20: COORDINATED SCENARIO — Complex Money Laundering through Trade Finance

## Narrative

This synthetic Phase 7 trace-through exercises MACMS for a very high compliance case involving `agent-tm-001, agent-cs-001, agent-ru-001, agent-rg-001`. The expected disposition is **CRITICAL**. No real customer, account, communication, transaction, or regulatory-feed data is used.

## Regulatory Context

Applicable regulations and standards: BSA/AML, OFAC, Trade-Based Money Laundering Red Flags, FATF Recommendations.

## Initial Detection Signals

- **agent-tm-001**: confidence 0.90; evidence `cs20_tm_evidence_01, cs20_tm_evidence_02, cs20_tm_evidence_03, cs20_tm_evidence_04, cs20_tm_evidence_05, cs20_tm_evidence_06`; context `{'trade_mispricing_pct': 300, 'intermediary_bank_count': 5, 'layering': True}`.
- **agent-cs-001**: confidence 0.91; evidence `cs20_cs_evidence_01, cs20_cs_evidence_02, cs20_cs_evidence_03, cs20_cs_evidence_04, cs20_cs_evidence_05, cs20_cs_evidence_06`; context `{'override_count': 2, 'pressure_phrases': ['expedite this for VIP client', 'override the hold'], 'rm_misconduct': True}`.
- **agent-ru-001**: confidence 0.93; evidence `cs20_ru_evidence_01, cs20_ru_evidence_02, cs20_ru_evidence_03, cs20_ru_evidence_04, cs20_ru_evidence_05, cs20_ru_evidence_06`; context `{'fatf_update_days_ago': 14, 'enhanced_due_diligence': True, 'regulatory_update_confirmed': True}`.
- **agent-rg-001**: confidence 0.95; evidence `cs20_rg_evidence_01, cs20_rg_evidence_02, cs20_rg_evidence_03, cs20_rg_evidence_04, cs20_rg_evidence_05, cs20_rg_evidence_06`; context `{'board_level_reporting': True, 'evidence_compilation': '20+ items'}`.

## Expected Outcome

The pipeline must validate all serialized messages, retain one trace correlation ID, apply the appropriate consensus or special handling path, route the case to Tier 4, and prepare: SAR filing (FinCEN), Trade finance review report, RM conduct investigation report, Sanctions screening report, Board-level executive summary. Reports are draft-only with state `DRAFT_REQUIRES_HUMAN_AUTHORIZATION` unless the scenario is the CS-18 suppression record.

## Confidence Methodology

- TM: Pattern Detection 0.91 + Counterparty Analysis 0.88.
- CS: Keyword Detection 0.93 + Sentiment Analysis 0.89.
- RU: Regulatory Feed 0.96 + Precedent Analysis 0.90.
- RG: Evidence compilation for board-level reporting; no independent violation confidence required.

This is the coordinated full-system scenario. TM, CS, RU, and RG all participate; 20+ evidence references are compiled, the case is routed to Tier 4, and every report remains draft-only pending human authorization.
