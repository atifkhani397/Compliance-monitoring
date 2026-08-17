---
title: MACMS Agent Registry Specification
date: 2026-08-17
version: 1.0.0
status: Approved
---

# MACMS Primary Agent Registry

This document defines the formal specifications, resource allocations, interface contracts, and SLA obligations for all primary agents operating in the Multi-Agent Compliance Monitoring System (MACMS).

---

## 1. Transaction Monitor Agent (TM)

- **Agent Identifier**: `agent-tm-001`
- **Agent Name**: Transaction Monitor Agent
- **Description**: Real-time surveillance of global equity, fixed income, FX, and derivative trading activities. Detects market abuse patterns including wash trading, spoofing, front-running, and insider dealing.
- **Version**: `1.0.0`

### 1.1 Specifications & Interfaces
- **Capabilities**:
  - High-frequency order book surveillance (FIX protocol)
  - Statistical anomaly detection on volume & price spreads
  - Cross-market transaction correlation
  - Threshold-based alert generation
- **Input Interfaces**: FIX 4.2/4.4 order feeds, Swift MT/MX financial messages, execution reports.
- **Output Interfaces**: P1/P2 `ALERT` messages sent to Orchestrator and CS agent; transaction anomaly logs.
- **Dependencies**: Kafka ingress topic `macms.ingress.transactions`, Market Data API.
- **Resource SLA & Requirements**:
  - **CPU**: 8 vCPU dedicated
  - **Memory**: 16 GB RAM
  - **Latency SLA**: < 500ms processing per transaction batch
  - **Queue SLA**: P1-CRITICAL (< 5m response time)
- **Health Check Endpoint**: `GET /health/agent-tm-001`
  - Expected Response: `{"status": "UP", "agent_id": "agent-tm-001", "queue_depth": 0, "last_processed_timestamp": "2026-08-17T12:00:00Z"}`

---

## 2. Communication Scanner Agent (CS)

- **Agent Identifier**: `agent-cs-001`
- **Agent Name**: Communication Scanner Agent
- **Description**: Continuous monitoring and NLP processing of business communication channels (email, Bloomberg Chat, MS Teams, recorded voice lines) for behavioral anomalies, collusion, and unauthorized data disclosure.
- **Version**: `1.0.0`

### 2.1 Specifications & Interfaces
- **Capabilities**:
  - Multilingual sentiment & lexicon analysis
  - Entity recognition (trader handles, account numbers, ticker symbols)
  - Audio transcript indexing and keyword detection
  - Cross-channel correlation with transaction timestamps
- **Input Interfaces**: IMAP/SMTP mail streams, chat export APIs, audio transcript JSON blobs.
- **Output Interfaces**: P2/P3 `ALERT` messages sent to Orchestrator and RG agent.
- **Dependencies**: Kafka ingress topic `macms.ingress.communications`, Voice Transcription Service.
- **Resource SLA & Requirements**:
  - **CPU**: 16 vCPU (GPU accelerated for NLP inference)
  - **Memory**: 32 GB RAM
  - **Latency SLA**: < 15s per email/chat log batch
  - **Queue SLA**: P2-HIGH (< 15m response time)
- **Health Check Endpoint**: `GET /health/agent-cs-001`

---

## 3. Regulatory Update Tracker Agent (RU)

- **Agent Identifier**: `agent-ru-001`
- **Agent Name**: Regulatory Update Tracker Agent
- **Description**: Ingests, parses, and analyzes updates from regulatory authorities (RBI, SEBI, SEC, FINRA, FCA, ESMA) to determine internal compliance policy updates and mapping shifts.
- **Version**: `1.0.0`

### 3.1 Specifications & Interfaces
- **Capabilities**:
  - Web scraping & RSS feed parsing of regulatory portals
  - Circular classification and rule change extractions
  - Mapping regulatory delta to internal policy IDs
  - Automated update broadcasts to all agents
- **Input Interfaces**: Regulatory portal RSS/API feeds, PDF circular downloads.
- **Output Interfaces**: P3/P4 `UPDATE` messages broadcasted to Orchestrator and all primary agents.
- **Dependencies**: Ingress web scrapers, Regulatory API gateways.
- **Resource SLA & Requirements**:
  - **CPU**: 4 vCPU
  - **Memory**: 8 GB RAM
  - **Latency SLA**: < 5m from regulatory publication
  - **Queue SLA**: P3-MEDIUM (< 1h response time)
- **Health Check Endpoint**: `GET /health/agent-ru-001`

---

## 4. Report Generator Agent (RG)

- **Agent Identifier**: `agent-rg-001`
- **Agent Name**: Report Generator Agent
- **Description**: Synthesizes multi-agent detection evidence, compiles Suspicious Activity Reports (SAR/STR), generates periodic regulatory filings, and maintains cryptographic audit chains.
- **Version**: `1.0.0`

### 4.1 Specifications & Interfaces
- **Capabilities**:
  - Cross-agent evidence package aggregation
  - Suspicious Activity Report (SAR) XML/JSON template compilation
  - Cryptographic hash signature verification and anchoring
  - Distribution to compliance officer dashboards and filing gateways
- **Input Interfaces**: `ALERT`, `QUERY`, and `RESPONSE` messages from TM, CS, and RU agents.
- **Output Interfaces**: Regulatory filing XML/PDF documents, P1/P2 `ESCALATION` packages.
- **Dependencies**: Audit Log Store, Compliance Reporting Database.
- **Resource SLA & Requirements**:
  - **CPU**: 8 vCPU
  - **Memory**: 16 GB RAM
  - **Latency SLA**: < 30s per report compilation
  - **Queue SLA**: P1-CRITICAL / P2-HIGH (< 15m response time)
- **Health Check Endpoint**: `GET /health/agent-rg-001`
