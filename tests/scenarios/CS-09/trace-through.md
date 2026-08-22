---
scenario: CS-09
trace_type: full_pipeline
status: Implemented
---

# CS-09 Trace-Through

| Step | Pipeline stage | Expected evidence |
| ---: | --- | --- |
| 1 | Synthetic detection | agent-tm-001, agent-ru-001 emit predetermined rule-based results. |
| 2 | Message validation | ALERT/UPDATE payloads validate against the Phase 1 message schema and share one trace ID. |
| 3 | Correlation | The orchestrator groups messages by trace/correlation ID. |
| 4 | Consensus or special handling | Deterministic consensus or documented special UPDATE flow. |
| 5 | Escalation | Tier 4 human review with SLA. |
| 6 | Report generation | OFAC compliance report, Transaction hold documentation, Voluntary disclosure draft; draft-only authorization state. |
| 7 | Audit verification | Detection, messaging, consensus/special handling, escalation, report, and checkpoints form a verifiable chain. |

## Step 1 — Detection

The scenario runner records the specified synthetic signal and confidence methodology for each participating agent. Detection methods are deterministic stubs; this phase does not introduce ML, NLP, or external regulatory-feed parsing.

## Step 2 — Inter-Agent Messaging

Each emitted message is fully populated with UUID v4 identifiers, protocol version, timestamp, sender, recipient, priority, trace ID, payload schema, confidence where required, TTL, signature placeholder, and nonce. `Message.model_validate()` is run again during test execution.

## Step 3 — Consensus and Conflict Handling

The runner invokes the Phase 3 deterministic consensus engine for ordinary alerts. CS-03 additionally routes its severity disagreement through `ConflictResolver`; CS-07 uses a regulatory UPDATE; CS-18 uses the verified false-positive suppression UPDATE. The expected disposition is recorded in the audit trail.

## Step 4 — Escalation

When required, the Phase 4 escalation service creates an in-memory record with the required tier, decision-support package, SLA deadline, and audit events. CS-18 intentionally creates no escalation.

## Step 5 — Reporting

Report Generator is represented by a validated UPDATE containing the scenario’s draft report types and the state `DRAFT_REQUIRES_HUMAN_AUTHORIZATION`. Actual XBRL/PDF filing generation remains out of scope.

## Step 6 — Audit and Acceptance

The scenario writes `messages.json` and `audit-trail.json`, verifies the complete hash chain, and requires at least 15 audit entries for CS-01, and at least 8 for other scenarios.

## Confidence Methodology

- TM: Counterparty Analysis = 0.94.
- RU: Regulatory Feed Monitoring = 0.98.
