# Meridian Global Bank - Multi-Agent Compliance Monitoring System (MACMS)

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)]()
[![Build Status](https://img.shields.io/badge/build-Phase%201%20Passing-brightgreen.svg)]()

## 1. Project Overview

The **Multi-Agent Compliance Monitoring System (MACMS)** is an enterprise-grade, asynchronous compliance monitoring platform designed specifically for **Meridian Global Bank**. The system operates across global trading desks, business communication streams, regulatory feeds, and automated reporting systems to ensure continuous adherence to international regulatory frameworks (including RBI, SEBI, FINRA, SEC, GDPR, and MiFID II).

MACMS uses a hierarchical multi-agent architecture with a central orchestrator. Four specialized primary agents collaborate asynchronously through cryptographically signed messages over a distributed Apache Kafka event backbone:

- **Transaction Monitor (TM)** (`agent-tm-001`): Continuous surveillance of financial transactions, trading desk activities, market order streams (FIX protocol), and anomaly detection.
- **Communication Scanner (CS)** (`agent-cs-001`): Natural Language Processing (NLP) and surveillance across email (IMAP/SMTP), chat, voice transcripts, and document attachments for policy violations.
- **Regulatory Update Tracker (RU)** (`agent-ru-001`): Real-time tracking of global regulatory updates (RSS/APIs, circulars), mapping changes to internal bank policies and controls.
- **Report Generator (RG)** (`agent-rg-001`): Automated compilation, cryptographic audit hashing, and distribution of compliance reports and regulatory filings.

---

## 2. System Architecture & Topology Summary

MACMS uses a hierarchical event-driven architecture structured around the C4 model specification:

```
                      +----------------------------------+
                      |   Central Orchestration Node    |
                      +----------------------------------+
                                       |
                +----------------------+----------------------+
                |                      |                      |
     +---------------------+ +--------------------+ +--------------------+
     | Transaction Monitor | | Comm. Scanner (CS) | | Reg. Tracker (RU)  |
     |     (TM-001)        | |     (CS-001)       | |     (RU-001)       |
     +---------------------+ +--------------------+ +--------------------+
                |                      |                      |
                +----------------------+----------------------+
                                       |
                      +----------------------------------+
                      |  Report Generator Agent (RG-001) |
                      +----------------------------------+
                                       |
                      +----------------------------------+
                      |  Apache Kafka Message Backbone   |
                      +----------------------------------+
```

Key Architectural Principles:
1. **Asynchronous Message-Based Backbone**: All inter-agent communication uses typed JSON messages dispatched over partitioned Kafka topics with correlation tracking.
2. **Cryptographic Identity & Non-Repudiation**: Every message payload contains an HMAC-SHA256 signature generated using agent-specific credentials and nonces.
3. **Priority-Driven SLA Routing**: Five priority queues (P1-CRITICAL through P5-INFORMATIONAL) ensure sub-5-minute SLAs for critical market abuse alerts.
4. **Immutable Audit Trail**: SHA-256 hash chaining ensures tamper-evident audit logging for all regulatory decisions and system events.

---

## 3. Repository Navigation Guide

The repository documentation is structured into modular domain areas under `docs/`:

| Directory | Purpose & Key Documents |
| :--- | :--- |
| [`docs/architecture/`](docs/architecture/) | Core system topology, agent registry, data flow pipelines, security architecture, and failure modes analysis. |
| ├── [`system-topology.md`](docs/architecture/system-topology.md) | Detailed C4 Level 1 & 2 diagrams, hierarchical routing topology, and event bus specs. |
| ├── [`agent-registry.md`](docs/architecture/agent-registry.md) | Specifications, capabilities, SLAs, resources, and endpoints for all 4 primary agents. |
| ├── [`data-flow.md`](docs/architecture/data-flow.md) | Data ingestion paths, data classification, and RBI India data residency compliance. |
| ├── [`security-architecture.md`](docs/architecture/security-architecture.md) | mTLS, X.509, RBAC policies, TLS 1.3/AES-256 encryption, and key rotation. |
| └── [`failure-modes.md`](docs/architecture/failure-modes.md) | Analysis of 6 critical failure scenarios (partitions, crashes, corruption) with mitigations. |
| [`docs/protocols/`](docs/protocols/) | Formal inter-agent communication specifications. |
| ├── [`message-schema.json`](docs/protocols/message-schema.json) | Draft-07 JSON Schema defining header requirements and 6 payload schemas. |
| └── [`routing-logic.md`](docs/protocols/routing-logic.md) | P1-P5 SLA queues, agent-pair matrix, retry backoff, circuit breakers, and multicast logic. |
| [`docs/conflict-resolution/`](docs/conflict-resolution/) | Consensus algorithms and taxonomy for resolving inter-agent analytical discrepancies. |
| [`docs/escalation/`](docs/escalation/) | Frameworks and decision trees for human-in-the-loop compliance officer escalation. |
| [`docs/decision-trees/`](docs/decision-trees/) | Decision logic specifications and capability matrix for agent execution paths. |
| [`docs/observability/`](docs/observability/) | Logging specifications, audit trail mechanics, dashboard designs, and retention policies. |
| └── [`logging-spec.md`](docs/observability/logging-spec.md) | Structured logging taxonomy across 8 log categories with trace correlation. |

---

## 4. Setup & Installation Instructions

### Prerequisites
- **Python**: Version 3.11 or higher
- **Git**: For version control
- **Pip**: Latest Python package manager

### Local Environment Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/atifkhani397/Compliance-monitoring.git
   cd Compliance-monitoring
   ```

2. **Create and Activate Virtual Environment**:
   ```bash
   python -m venv .venv
   # On Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables Configuration**:
   Create a `.env` file in the root directory (refer to `.env.example` if needed):
   ```env
   MACMS_ENV=development
   MACMS_LOG_LEVEL=INFO
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   AUDIT_CHAIN_SECRET_KEY=meridian-global-audit-secret-key-2026
   ```

---

## 5. Technology Stack Justification

| Technology | Selected Stack | Technical Justification |
| :--- | :--- | :--- |
| **Language** | Python 3.11+ | High performance with improved async event loops, rich data science/surveillance ecosystem, strong static typing support with Pydantic v2 and mypy. |
| **Data Validation** | Pydantic v2 | Rust-accelerated validation engine providing strict schema enforcement, high-speed JSON parsing, and native `model_json_schema()` generation. |
| **Message Broker** | Apache Kafka | Distributed partition-based log architecture guaranteeing high throughput, exact-once semantics, horizontal scaling, and event replay capabilities. |
| **Logging** | `structlog` | Context-aware structured JSON log rendering with zero-overhead contextual binding across asynchronous execution contexts. |
| **Cryptography** | `cryptography` | OpenSSL-backed cryptographic primitives supporting HMAC-SHA256 message signing and deterministic SHA-256 hash chaining. |
| **Testing** | `pytest` + `pytest-asyncio` | Production-standard testing framework enabling async unit testing, parameterization, and strict coverage reporting. |

---

## 6. Document Error Report

The table below is reserved for logging deliberately planted errors or discrepancy findings uncovered during Compliance Review Board audits.

| Error ID | Section / File | Description of Discrepancy | Severity | Corrective Action | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| *None* | *N/A* | *No errors reported in Phase 1 baseline.* | *N/A* | *N/A* | *Open* |

---

## 7. Compliance Review Board Evaluation Summary

Phase 1 establishes the foundational infrastructure adhering strictly to Meridian Global Bank's internal controls:

- **Verification Criteria**:
  1. Complete adherence to the 28-point self-assessment framework (see [`SELF-ASSESSMENT.md`](SELF-ASSESSMENT.md)).
  2. 100% strict type checking (`mypy --strict src/`) with zero warnings.
  3. Clean formatting and linting via `ruff`.
  4. Fully passing test suite (`pytest -v`) enforcing 100% core contract coverage.
  5. Cryptographic hash chain validation guaranteeing non-repudiation.

---

## 8. Links & Self-Assessment

- **Self-Assessment Document**: Please consult [`SELF-ASSESSMENT.md`](SELF-ASSESSMENT.md) for the full 28-item Phase 1 readiness evaluation.
