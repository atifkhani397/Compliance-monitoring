---
title: MACMS Human-in-the-Loop Escalation Framework
date: 2026-08-22
version: 2.0.0
status: Implemented
---

# MACMS Human-in-the-Loop Escalation Framework

## 1. Purpose and Scope

This framework provides the regulated human-oversight layer for automated MACMS decisions. Escalations are stored in memory for Phase 4, assigned through `HumanAssignmentEngine`, supported by evidence packages, and written to the append-only audit chain. External email, SMS, paging, HR, persistent storage, and a human dashboard remain outside this phase.

## 2. Tier Structure and SLAs

| Tier | Role | Primary cases | SLA to first human action | Auto-re-escalation |
| --- | --- | --- | ---: | --- |
| 1 | Compliance Analyst | LOW and MEDIUM alerts | 4 hours | At 2 hours, move to Tier 2 |
| 2 | Senior Compliance Analyst | HIGH and complex MEDIUM alerts | 2 hours | At 1 hour, move to Tier 3 |
| 3 | Compliance Manager | CRITICAL alerts and regulatory conflicts | 1 hour | At 30 minutes, move to Tier 4 |
| 4 | Director / Chief Compliance Officer | MRIAs, board-level reporting, and senior-management cases | 30 minutes | Final tier; record SLA violation and page CCO in the simulation |

SLA timers begin when the `EscalationRecord` is created. The service returns records that reach 50 percent of their SLA as actionable for auto-escalation. Tier 3 and Tier 4 use the on-call pool after hours; Tier 4 is restricted to the CCO profile.

## 3. Escalation Triggers

The service escalates when post-consensus confidence is below 0.7, conflict Type E is present, Type D lacks sufficient exculpatory evidence, an agent is degraded or stopped during processing, or a cross-jurisdictional violation is detected. It also recognizes sanctions indicators such as OFAC, EU, or MAS exposure; insider-trading suspicion under SEC Rule 10b-5; three or more violations by the same entity within 30 days; senior-management involvement; and system-generated anomalies not represented in training data.

Type E is routed to Tier 3 or higher immediately. MRIAs, board-level cases, and C-level, MD, or Director involvement route to Tier 4. CRITICAL cases without those additional triggers route to Tier 3.

## 4. Decision-Support Package

Every escalation includes an auditable package containing the alert summary, cross-agent evidence with source attribution, historical violations for affected entities, applicable regulatory context and recent enforcement references, the consensus-based recommended action, financial/reputational/regulatory risk assessment, similar cases, and agent disagreement details when conflict resolution was used.

## 5. Human Assignment and Independence

`HumanAssignmentEngine` is the single source of truth for assignment. It selects an available human at or above the requested tier, matches required skills, chooses the least-loaded eligible profile, and excludes conflict-of-interest flags matching affected entities. After-hours Tier 3 cases use the on-call rotation. Tier 4 cases route directly to the configured CCO profile. Assignments increment workload; resolution releases workload.

## 6. Human Decisions and Overrides

Human decisions are one of `approve`, `reject`, `override`, or `request_more_info`. Each decision includes the reviewer, timestamp, justification, and confidence after review. The override authority matrix is: Analyst for LOW, Senior Analyst for MEDIUM, Manager for HIGH, and Director/CCO for CRITICAL. An override requires a justification of at least 50 characters. A CRITICAL override additionally requires an independent secondary approver. The same reviewer cannot override the same violation type within one hour. Before/after state, justification, requester, secondary approver, and decision are written to the audit chain.

## 7. Feedback Loop

Each human decision becomes a labeled `FeedbackRecord` containing decision ID, escalation ID, alert ID, agent identity, violation type, human decision, confidence before and after, correctness placeholder, justification, reviewer, and timestamp. Weekly rule-based updates raise a detection threshold by 0.1 after three or more rejections of the same pattern, lower it by 0.05 when a low-confidence alert is approved, and reduce an agent consensus weight by 0.05 when its false-positive rate exceeds 15 percent. Threshold changes are scheduled behind a 24-hour review period and can be exported as JSONL.

## 8. State and Audit Transitions

The supported statuses are `open`, `in_review`, `resolved`, `auto_escalated`, and `overridden`. Creation, assignment, SLA warning, auto-escalation, human decisions, overrides, and closure are all audit events. Records are held in memory only; no update/delete persistence layer is introduced in Phase 4.

## 9. Phase 4 Boundaries

This phase intentionally does not implement actual email, SMS, paging, scenario-specific escalation logic, persistent storage, external HR integrations, a UI, or machine-learning threshold optimization. Those concerns are reserved for later phases or explicit integrations.
