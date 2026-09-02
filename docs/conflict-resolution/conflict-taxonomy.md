---
title: MACMS Inter-Agent Conflict Taxonomy
date: 2026-08-22
version: 2.0.0
status: Implemented
---

# MACMS Inter-Agent Conflict Taxonomy

## 1. Purpose

This taxonomy defines the seven supported conflict classes for correlated compliance assessments. A conflict is evaluated only when assessments refer to the same `correlation_id` or `trace_id` and fall within the configured five-minute window. The conflict resolver records the classification and selected resolution method in the tamper-evident audit chain.

## 2. Classification Matrix

| Type | Name | Detection pattern | Example | Severity | Resolution strategy | Escalation criteria |
| --- | --- | --- | --- | --- | --- | --- |
| A | Detection Disagreement | One assessment supports a violation while another has confidence below 0.5, or violation types differ | TM detects spoofing while CS finds no supporting communication evidence | HIGH | Weight direct evidence, correlate timestamps, and fuse evidence using the hybrid protocol | Escalate when hybrid confidence is below 0.7 or convergence fails |
| B | Severity Disagreement | Agents identify the same violation but supply different severity values | TM rates a suspected manipulation CRITICAL while CS rates it HIGH | MEDIUM | Calibrate severity against historical outcomes and select the conservative supported severity | Escalate when confidence scores differ by less than 0.1 or evidence is materially incomplete |
| C | Attribution Disagreement | Agents identify different responsible traders, desks, accounts, or causal entities | TM attributes an event to an algorithmic desk while CS identifies a trader | HIGH | Fuse multi-source attribution evidence; preserve all dissenting attributions | Escalate when no attribution exceeds the decision threshold |
| D | False Positive Conflict | A violation alert is accompanied by explicit exculpatory evidence | TM flags a large trade while CS supplies pre-arranged block-trade documentation | CRITICAL | Exculpatory evidence overrides the suspected false positive and suppresses the alert | Do not escalate the false-positive alert; retain an audit record. Escalate only if the exculpatory evidence itself is disputed |
| E | Regulatory Conflict | Jurisdictional or regulatory evidence contains contradictory obligations | EU disclosure is required while Singapore restricts cross-border data sharing | CRITICAL | Apply the regulatory priority matrix and preserve jurisdictional provenance | Immediate legal-counsel escalation is mandatory |
| F | Temporal Conflict | Agents report materially different event timestamps or sequences | TM places the violation at 14:30 while communications evidence points to 14:45 | MEDIUM | Synchronize timestamps, sequence events, and retain the original timestamps | Escalate when sequencing changes the regulatory conclusion |
| G | Scope Conflict | Agents identify different affected entities or account sets | TM identifies three accounts while CS identifies five | LOW | Use the union of affected entities and the conservative scope | Escalate when the union crosses a reporting or materiality threshold |

## 3. Precedence and Safety Rules

Type E takes precedence over all other classifications because contradictory regulatory obligations require legal review. Type D suppresses a suspected false positive when exculpatory evidence is explicit and traceable. When three or more agents contribute, the resolver uses full multi-source Dempster–Shafer fusion rather than pairwise resolution. A Bayesian–Dempster–Shafer disagreement greater than 0.2 is a convergence failure and is escalated.

## 4. Evidence Requirements

Every classification must preserve the source agent, event timestamp, evidence type, evidence data, and chain of custody. The resolver must never discard dissenting evidence, even when a single consensus decision is emitted. A missing or malformed assessment is a `ConflictDetectionError` or `InvalidAssessmentError`, not an implicit agreement.

## 5. Audit and Escalation

The resolver emits one audit entry for every decision. The entry includes the participating message IDs, conflict type, resolution method, confidence, escalation state, and deterministic audit reference. Confidence below 0.7 triggers human review unless Type D suppression applies. Type E always produces an escalation addressed to legal counsel.
