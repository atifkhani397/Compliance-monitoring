---
title: MACMS Failure Modes & Resiliency Analysis
date: 2026-08-17
version: 1.0.0
status: Approved
---

# MACMS Failure Modes & Resiliency Analysis

This document analyzes critical failure modes across the Multi-Agent Compliance Monitoring System (MACMS), establishing automated recovery, circuit breaking, failover, and data integrity protocols.

---

## 1. Failure Scenario Matrix

| Scenario ID | Failure Mode | Root Cause | Impact | Automated Recovery & Mitigation Strategy |
| :---: | :--- | :--- | :--- | :--- |
| **FM-01** | **Agent Offline** (TM Crash) | Memory leak or uncaught exception during peak trading hours. | Ingress trade surveillance paused for `agent-tm-001`. | Kafka consumer group automatically rebalances partitions to standby instances within 3 seconds. Unprocessed messages remain buffered in Kafka topic logs. |
| **FM-02** | **Message Broker Partition** | Network split or broker node hardware crash in Kafka cluster. | Kafka topic write timeouts or degraded throughput. | Producers switch to secondary brokers (in-sync replica list `min.insync.replicas=2`). Message buffer queue in agent memory holds up to 10,000 items. |
| **FM-03** | **Orchestrator Failure** | Primary orchestrator node crash or ZooKeeper session expiration. | Inter-agent coordination and state resolution stalled. | Standby orchestrator node detects leader heartbeats missing (> 5s) and acquires ZooKeeper lock, recovering active state from Kafka compaction topic `macms.orchestrator.state`. |
| **FM-04** | **Network Partition (Split-Brain)** | Network isolate between Mumbai and London availability zones. | Potential conflicting decisions or dual-leader scenario. | Enforces PACELC / CAP theorem principles: system prioritizes Consistency over Availability for P1 alerts. Quorum voting (majority > 50%) required before approving escalations. |
| **FM-05** | **Data Corruption** | Disk sector corruption or malformed message payload injection. | Pydantic validation failure or hash chain integrity failure. | Message schema validation drops malformed messages to Dead Letter Queue (DLQ). Cryptographic hash chain triggers `AuditIntegrityError` and replays log from last verified snapshot. |
| **FM-06** | **Cascading Agent Failure** | Downstream Report Generator (RG) agent bottleneck causing backpressure. | Queue congestion propagating upstream to TM and CS agents. | Circuit breaker pattern isolates `agent-rg-001`. Upstream agents switch to local disk-backed buffer queues. Rate limiters apply backpressure to non-critical feeds. |
| **FM-07** | **Orchestrator Process Crash** | Uncaught exception in Orchestrator event loop or host crash. | In-flight dispatches halt, agent registration state lost. | Backup Orchestrator process initializes from `config.yaml`, re-queries connected agents via `heartbeat` broadcast, and re-populates in-memory `AgentRegistry` and `AuditChain`. |
| **FM-08** | **Kafka Partition Loss** | Persistent hardware failure of all partition replicas for an agent topic. | Agent topic un-writeable (`KafkaConnectionError`). | KafkaProducer falls back to secondary fallback topic (`mcms.dead_letter`); Orchestrator emits `ESCALATION` to human operations tier. |

---

## 2. Circuit Breaker & Bulkhead Design

- **State Transitions**: `CLOSED` (Normal operations) -> `OPEN` (High error rate > 15% over 1 min) -> `HALF-OPEN` (Probe recovery with 5% traffic).
- **Bulkhead Isolation**: Each agent operates with independent worker thread pools and dedicated memory bounds to prevent resource exhaustion from spreading.
- **Registry & Orchestrator Recovery**: In-memory `AgentRegistry` uses `asyncio.Lock` for thread safety; agent re-registration on heartbeat auto-heals lost state following orchestrator restarts.

