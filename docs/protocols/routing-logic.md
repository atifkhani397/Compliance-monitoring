---
title: MACMS Inter-Agent Message Routing Specification
date: 2026-08-17
version: 1.0.0
status: Approved
---

# MACMS Inter-Agent Message Routing Specification

This document establishes the formal routing logic, priority queue SLA metrics, agent-pair communication rules, failure recovery, protocol negotiation, and multicast behavior for MACMS.

---

## 1. Priority Classification & SLA Queues

All inter-agent messages are routed based on their designated `priority` field (integer 1 through 5):

| Priority Code | Priority Name | Target SLA | Queue Destination | Delivery Mechanics |
| :---: | :--- | :--- | :--- | :--- |
| **P1** | **CRITICAL** | **< 5 Minutes** | `macms.events.p1-critical` | Immediate push, pre-empts lower priority queues, in-memory bypass. |
| **P2** | **HIGH** | **< 15 Minutes** | `macms.events.p2-high` | Dedicated high-priority worker pool execution. |
| **P3** | **MEDIUM** | **< 1 Hour** | `macms.events.p3-medium` | Standard balanced queue processing. |
| **P4** | **LOW** | **< 4 Hours** | `macms.events.p4-low` | Batch worker queue execution. |
| **P5** | **INFORMATIONAL** | **< 24 Hours** | `macms.events.p5-info` | Best-effort execution during low-traffic periods. |

---

## 2. Agent-Pair Routing Matrix

The table below defines valid message exchange paths between agents:

| Sender Agent | Permitted Message Types | Allowed Recipient Agents | Purpose |
| :--- | :--- | :--- | :--- |
| `agent-tm-001` | `ALERT`, `QUERY`, `HEARTBEAT` | `agent-cs-001`, `agent-rg-001` | Broadcast market abuse alerts; query trader comms. |
| `agent-cs-001` | `ALERT`, `RESPONSE`, `HEARTBEAT` | `agent-tm-001`, `agent-rg-001` | Send NLP comms alerts; respond to TM queries. |
| `agent-ru-001` | `UPDATE`, `HEARTBEAT` | `[agent-tm-001, agent-cs-001, agent-rg-001]` | Multicast regulatory rule updates to all agents. |
| `agent-rg-001` | `ESCALATION`, `QUERY`, `HEARTBEAT` | `agent-tm-001`, `agent-cs-001`, `agent-ru-001` | Aggregate evidence; issue compliance escalations. |

---

## 3. Multicast & Array Recipient Rules

1. **Single Recipient**: When `recipient_agent_id` is a string (e.g. `"agent-cs-001"`), the message is delivered strictly to that agent's consumer group.
2. **Multicast Array**: When `recipient_agent_id` is an array (e.g. `["agent-tm-001", "agent-cs-001", "agent-rg-001"]`), the routing engine fans out the message to each designated agent queue with identical `trace_id` and `correlation_id`.

---

## 4. Error Handling & Resiliency

1. **Retry Mechanism**: Exponential backoff with full jitter:
   $$t_{\text{retry}} = \text{random}(0, \min(\text{max\_backoff}, \text{base} \times 2^{\text{retry\_count}}))$$
2. **Dead Letter Queue (DLQ)**: If `retry_count` reaches 3 without successful processing, the message is routed to `macms.dlq.unroutable` with error metadata attached.
3. **Circuit Breaker**: If an agent target fails health checks (> 15% error rate), its breaker moves to `OPEN` state, rejecting new non-P1 messages until recovery.

---

## 5. Protocol Versioning & Compatibility

- **Semver Pattern**: `protocol_version` adheres to `^\d+\.\d+\.\d+$` (e.g., `1.0.0`).
- **Backward Compatibility**: Agents supporting version `1.X.Y` MUST accept and process messages formatted with `1.A.B` (where `A <= X`).
- **Version Handshake**: During initial connection establishment, agents exchange `HEARTBEAT` messages confirming supported protocol version bounds.
