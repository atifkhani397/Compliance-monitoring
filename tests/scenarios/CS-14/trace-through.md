---
scenario: CS-14
trace_type: full_pipeline
status: Implemented
phase: 7
---

# CS-14 Trace-Through

| Step | Pipeline stage | Expected evidence |
| ---: | --- | --- |
| 1 | Detection | Rule-based synthetic stubs produce the specified signals and confidence methodology. |
| 2 | Messaging | Every ALERT or UPDATE validates against the Phase 1 message contract and carries one trace ID. |
| 3 | Correlation | The orchestrator groups related messages and preserves sender/evidence provenance. |
| 4 | Consensus or special handling | Deterministic consensus across participating agents. |
| 5 | Escalation | Tier 3 with Phase 4 SLA and decision-support package. |
| 6 | Reporting | SEC referral, Fund board notification, Client restitution calculation with authorization state preserved. |
| 7 | Audit | Complete chain is serialized and verified. |

## Step 1 — Synthetic Detection

The scenario runner records each agent’s predetermined signal, evidence references, affected entities, and confidence methodology. The implementation deliberately uses rule-based stubs only; ML, NLP, and live regulatory-feed parsing remain outside Phase 7 scope.

## Step 2 — Message Construction and Validation

Messages include UUID v4 identifiers, protocol version, UTC timestamp, sender and recipient IDs, message type, priority, correlation/trace IDs, payload schema, confidence where applicable, TTL, retry count, audit classification, signature-compatible placeholder, and nonce. The test re-validates every in-memory message from its serialized model form.

## Step 3 — Correlation and Consensus

Ordinary multi-agent scenarios use the existing Phase 3 consensus engine. CS-16 deliberately produces Type C attribution evidence (`analyst_with_ib_pressure` versus `broader_conspiracy`); CS-19 uses Type E regulatory-conflict special handling without consensus; CS-18 uses UPDATE suppression; and CS-20 demonstrates four-agent coordinated confirmation with full evidence compilation.

## Step 4 — Escalation

Where required, the Phase 4 service creates an escalation record with the required tier, SLA deadline, decision-support package, and audit entry. CS-18 is asserted to have no escalation. CS-19 is asserted to require Tier 4 legal-counsel handling.

## Step 5 — Report Generation

The report-generator stage is represented by a validated UPDATE listing the prompt-defined report types. All ordinary reports are explicitly marked `DRAFT_REQUIRES_HUMAN_AUTHORIZATION`; actual XBRL, PDF, SAR submission, and external filing integrations remain out of scope.

## Step 6 — Audit Verification

The scenario serializes all synthetic pipeline events to `audit-trail.json` and verifies the complete append-only hash chain. Each scenario requires at least eight audit entries; CS-20 requires at least 30 entries because it covers all four agents, consensus, escalation, reporting, and trace checkpoints.

## Acceptance Assertions

The matching `test_scenario.py` executes the full pipeline and asserts detection/update disposition, schema validity, trace correlation, consensus or special handling, escalation tier and report types, and audit integrity. CS-18 additionally asserts no ALERT and no escalation; CS-20 additionally asserts participation by all four required agents.
