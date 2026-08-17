---
title: MACMS System Topology Architecture
date: 2026-08-17
version: 1.0.0
status: Approved
---

# Multi-Agent Compliance Monitoring System (MACMS) - System Topology Architecture

## 1. Executive Summary

This document specifies the architectural topology of the Multi-Agent Compliance Monitoring System (MACMS) for Meridian Global Bank. MACMS employs a hierarchical, event-driven multi-agent pattern with a central Orchestrator node operating on a high-throughput Apache Kafka event bus backbone.

---

## 2. C4 Model Specifications

### 2.1 C4 Level 1: System Context Diagram

```
+-----------------------------------------------------------------------------------+
|                                Meridian Global Bank                               |
|                                                                                   |
|  +--------------------+   +---------------------+   +--------------------------+  |
|  | Trading Platforms  |   | Comm. Email/Chat    |   | Regulatory Feed Provider |  |
|  | (FIX Protocol)     |   | (IMAP/SMTP/Voice)   |   | (RSS/APIs/Circulars)     |  |
|  +--------------------+   +---------------------+   +--------------------------+  |
|            |                         |                           |                |
|            +-------------------------+---------------------------+                |
|                                      |                                            |
|                                      v                                            |
|  +-----------------------------------------------------------------------------+  |
|  | Multi-Agent Compliance Monitoring System (MACMS)                             |  |
|  | - Hierarchical Orchestrator Node                                            |  |
|  | - Transaction Monitor (TM), Comm Scanner (CS), Reg Tracker (RU), Report Gen |  |
|  | - Kafka Event Backbone, Cryptographic Audit Trail                            |  |
|  +-----------------------------------------------------------------------------+  |
|                                      |                                            |
|            +-------------------------+---------------------------+                |
|            v                                                     v                |
|  +--------------------+                             +--------------------------+  |
|  | Compliance Officers|                             | External Regulators      |  |
|  | (Dashboard / Alert)|                             | (SEC/FINRA/RBI/SEBI)     |  |
|  +--------------------+                             +--------------------------+  |
+-----------------------------------------------------------------------------------+
```

### 2.2 C4 Level 2: Container Diagram

```
+-----------------------------------------------------------------------------------+
| MACMS System Boundary                                                             |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Ingestion Containers (Kafka Connectors, Schema Registry)                     |  |
|  +-----------------------------------------------------------------------------+  |
|                                      |                                            |
|                                      v                                            |
|  +-----------------------------------------------------------------------------+  |
|  | Apache Kafka Event Bus (Topics: macms.alerts, macms.queries, macms.audit)   |  |
|  +-----------------------------------------------------------------------------+  |
|                     ^                    ^                    ^                   |
|                     |                    |                    |                   |
|                     v                    v                    v                   |
|         +-------------------+  +-------------------+  +-------------------+       |
|         | Transaction Mon.  |  | Comm Scanner      |  | Reg Tracker       |       |
|         | (agent-tm-001)    |  | (agent-cs-001)    |  | (agent-ru-001)    |       |
|         +-------------------+  +-------------------+  +-------------------+       |
|                     ^                    ^                    ^                   |
|                     +--------------------+--------------------+                   |
|                                          |                                        |
|                                          v                                        |
|                             +--------------------------+                          |
|                             | Central Orchestrator     |                          |
|                             | Node (State & Routing)   |                          |
|                             +--------------------------+                          |
|                                          |                                        |
|                                          v                                        |
|                             +--------------------------+                          |
|                             | Report Generator (RG)    |                          |
|                             | (agent-rg-001)           |                          |
|                             +--------------------------+                          |
|                                          |                                        |
|                                          v                                        |
|                             +--------------------------+                          |
|                             | Audit Storage & REST API |                          |
|                             +--------------------------+                          |
+-----------------------------------------------------------------------------------+
```

---

## 3. Hierarchical Topology & Agent Roles

1. **Central Orchestrator**: Root node managing inter-agent task allocation, conflict resolution routing, state tracking, and protocol handshake negotiations.
2. **Primary Execution Agents**:
   - **Transaction Monitor (TM)**: Sub-second surveillance of trade order flows, wash sales, front-running, and spoofing patterns.
   - **Communication Scanner (CS)**: Asynchronous analysis of emails, chat transcripts, voice feeds, and document attachments for collusion or insider trading signals.
   - **Regulatory Update Tracker (RU)**: Continuous polling of regulatory portals, parsing regulatory changes, and broadcasting rule updates.
   - **Report Generator (RG)**: Aggregation of cross-agent evidence, compiling SAR/STR filings, and generating cryptographically signed audit reports.

---

## 4. Communication Backbone Specification

- **Broker Stack**: Apache Kafka cluster (minimum 3 broker nodes for HA).
- **Partitioning Strategy**: Topics partitioned by `agent_id` and `tenant_id` to guarantee ordering per trading desk.
- **Topic Naming Convention**:
  - `mcms.{agent_id}.{message_type.lower()}` (Agent-specific topics, e.g., `mcms.agent-tm-001.alert`)
  - `mcms.escalation.human` (Human escalation queue topic)
  - `mcms.heartbeat` (System health monitoring topic)
  - `macms.events.p1-critical` through `p5-info` (Priority SLA topics)
  - `macms.audit.chain` (Cryptographic audit log topic)

---

## 5. Phase 2 Component Hardware & Resource Allocations

| Agent Node | Agent ID | vCPU | RAM | Storage | Primary Workload |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Central Orchestrator** | `orchestrator` | 16 | 32 GB | NVMe SSD | Message dispatch, health registry, audit chaining |
| **Transaction Monitor** | `agent-tm-001` | 32 | 128 GB | NVMe SSD | Real-time pattern detection, threshold & temporal analysis |
| **Communication Scanner** | `agent-cs-001` | 24 | 96 GB | SSD | NLP scanning, sentiment, Chinese wall & privilege detection |
| **Regulatory Tracker** | `agent-ru-001` | 8 | 32 GB | Persistent SSD | Feed scraping, impact assessment, precedent analysis |
| **Report Generator** | `agent-rg-001` | 16 | 64 GB | SSD | Template rendering, evidence packaging, filing preparation |

---

## 6. Redundancy & Fault Tolerance

- **Hot-Standby Orchestrator**: Primary-secondary orchestrator deployment using ZooKeeper/Raft leader election.
- **Consumer Group Failover**: Each agent runs as a Kafka consumer group with dynamic partition rebalancing.
- **State Store Persistence**: Agent internal state backed up using RocksDB/Kafka changelog topics.

