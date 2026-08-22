---
title: MACMS Compliance Scenario Summary Index
date: 2026-08-22
version: 2.0.0
status: Phase 6 Implemented
---

# MACMS Compliance Scenario Summary Index

Phase 6 implements the first ten synthetic, deterministic trace-throughs. Each implemented scenario contains `scenario.md`, `trace-through.md`, `messages.json`, `audit-trail.json`, and `test_scenario.py`. Every scenario has five executable tests covering detection, schema-valid messaging, consensus or special handling, escalation/reporting, and audit verification.

| Scenario | Agents | Complexity | Expected Alert | Status | Test Count |
| --- | --- | --- | --- | --- | ---: |
| CS-01 | TM + CS | High | CRITICAL | Implemented | 5 |
| CS-02 | TM | Medium | HIGH | Implemented | 5 |
| CS-03 | CS + TM | High | HIGH | Implemented | 5 |
| CS-04 | TM | Medium | CRITICAL | Implemented | 5 |
| CS-05 | CS | High | CRITICAL | Implemented | 5 |
| CS-06 | TM | High | HIGH | Implemented | 5 |
| CS-07 | RU | Medium | MEDIUM | Implemented | 5 |
| CS-08 | CS | Low-Medium | CRITICAL | Implemented | 5 |
| CS-09 | TM + RU | High | CRITICAL | Implemented | 5 |
| CS-10 | TM | Medium | CRITICAL | Implemented | 5 |
| CS-11 | CS + RU | Medium | HIGH | Pending Phase 7 | 0 |
| CS-12 | TM | Low | MEDIUM | Pending Phase 7 | 0 |
| CS-13 | CS | Medium | HIGH | Pending Phase 7 | 0 |
| CS-14 | TM | Medium | CRITICAL | Pending Phase 7 | 0 |
| CS-15 | TM | Medium | HIGH | Pending Phase 7 | 0 |
| CS-16 | CS + TM | High | CRITICAL | Pending Phase 7 | 0 |
| CS-17 | TM + CS | High | CRITICAL | Pending Phase 7 | 0 |
| CS-18 | TM | Medium | NO ALERT | Pending Phase 7 | 0 |
| CS-19 | RU | High | HIGH | Pending Phase 7 | 0 |
| CS-20 | ALL FOUR | Very High | CRITICAL | Pending Phase 7 | 0 |

## Phase 6 Coverage Notes

CS-01 demonstrates TM and CS coordination for pre-announcement accumulation and Tier 3 escalation. CS-02 demonstrates single-agent spoofing detection. CS-03 demonstrates a Type B severity disagreement. CS-04 demonstrates CRITICAL AML structuring. CS-05 demonstrates communication-only Chinese Wall detection. CS-06 demonstrates cross-account wash trading. CS-07 demonstrates RU-only regulatory-change UPDATE handling. CS-08 demonstrates mass misleading-marketing detection. CS-09 demonstrates TM and RU sanctions coordination and Tier 4 escalation. CS-10 demonstrates temporal front-running detection.

All scenario records are synthetic. No real ML/NLP models, regulatory-feed parsers, customer data, external filing integrations, or persistent storage are introduced in Phase 6.
