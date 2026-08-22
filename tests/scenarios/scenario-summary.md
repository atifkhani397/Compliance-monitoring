---
title: MACMS Compliance Scenario Summary Index
date: 2026-08-22
version: 3.0.0
status: Phase 7 Implemented
---

# MACMS Compliance Scenario Summary Index

Phases 6 and 7 implement all twenty synthetic, deterministic compliance trace-throughs. Each scenario contains `scenario.md`, `trace-through.md`, `messages.json`, `audit-trail.json`, and `test_scenario.py`. Every scenario has five executable tests covering detection, schema-valid messaging, consensus or special handling, escalation/reporting, and audit verification.

| Scenario | Agents | Complexity | Expected Alert | Status | Test Count |
| --- | --- | --- | --- | --- | ---: |
| CS-01 | TM + CS | High | CRITICAL | Implemented Phase 6 | 5 |
| CS-02 | TM | Medium | HIGH | Implemented Phase 6 | 5 |
| CS-03 | CS + TM | High | HIGH | Implemented Phase 6 | 5 |
| CS-04 | TM | Medium | CRITICAL | Implemented Phase 6 | 5 |
| CS-05 | CS | High | CRITICAL | Implemented Phase 6 | 5 |
| CS-06 | TM | High | HIGH | Implemented Phase 6 | 5 |
| CS-07 | RU | Medium | MEDIUM | Implemented Phase 6 | 5 |
| CS-08 | CS | Low-Medium | CRITICAL | Implemented Phase 6 | 5 |
| CS-09 | TM + RU | High | CRITICAL | Implemented Phase 6 | 5 |
| CS-10 | TM | Medium | CRITICAL | Implemented Phase 6 | 5 |
| CS-11 | CS + RU | Medium | HIGH | Implemented Phase 7 | 5 |
| CS-12 | TM | Low | MEDIUM | Implemented Phase 7 | 5 |
| CS-13 | CS | Medium | HIGH | Implemented Phase 7 | 5 |
| CS-14 | TM | Medium | CRITICAL | Implemented Phase 7 | 5 |
| CS-15 | TM | Medium | HIGH | Implemented Phase 7 | 5 |
| CS-16 | CS + TM | High | CRITICAL | Implemented Phase 7 | 5 |
| CS-17 | TM + CS | High | CRITICAL | Implemented Phase 7 | 5 |
| CS-18 | TM | Medium | NO ALERT | Implemented Phase 7 | 5 |
| CS-19 | RU | High | HIGH | Implemented Phase 7 | 5 |
| CS-20 | ALL FOUR | Very High | CRITICAL | Implemented Phase 7 | 5 |

## Phase 7 Coverage Notes

CS-11 demonstrates GDPR cross-border data-transfer detection and Tier 2 escalation. CS-12 demonstrates a persistent concentration-limit breach. CS-13 demonstrates off-channel communications and negative-signal record-keeping analysis. CS-14 demonstrates systematic late trading and NAV timing discrepancies. CS-15 demonstrates systematic best-execution routing bias. CS-16 demonstrates Type C attribution disagreement and refined research-independence attribution. CS-17 demonstrates elder financial exploitation and immediate-freeze consideration. CS-18 is the critical negative test: a legitimate block trade is verified and suppressed with no ALERT and no escalation. CS-19 demonstrates Type E multi-jurisdiction regulatory conflict with direct Tier 4 legal-counsel escalation. CS-20 demonstrates TM, CS, RU, and RG coordination, 20+ evidence references, full consensus, Tier 4 escalation, and board-level draft reporting.

All scenario records are synthetic. No real ML/NLP models, regulatory-feed parsers, customer data, external filing integrations, persistent storage, India-specific logic, or Phase 8 security hardening is introduced by Phase 7.
