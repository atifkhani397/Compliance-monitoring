---
title: MACMS Security Architecture Specification
date: 2026-08-17
version: 1.0.0
status: Approved
---

# MACMS Security Architecture Specification

This document defines the security model, cryptographic protocols, identity management, access control frameworks, and key management lifecycle for the Multi-Agent Compliance Monitoring System (MACMS).

---

## 1. Authentication & Agent Identity

1. **Cryptographic Identity**: Every agent instance (`agent-tm-001`, `agent-cs-001`, `agent-ru-001`, `agent-rg-001`) is provisioned with a unique cryptographic X.509 digital certificate issued by Meridian Global Bank's Internal Certificate Authority (ICA).
   - `agent-tm-001` → Certificate Subject: `CN=agent-tm-001.macms.meridianbank.internal`
   - `agent-cs-001` → Certificate Subject: `CN=agent-cs-001.macms.meridianbank.internal`
   - `agent-ru-001` → Certificate Subject: `CN=agent-ru-001.macms.meridianbank.internal`
   - `agent-rg-001` → Certificate Subject: `CN=agent-rg-001.macms.meridianbank.internal`
2. **Mutual TLS (mTLS)**: All network connections between agents, Kafka brokers, schema registries, and orchestrator nodes enforce mandatory mTLS over TLS 1.3 with strict SAN (Subject Alternative Name) validation.
3. **Message-Level Signatures**: In addition to transport-layer security, every inter-agent message payload contains a cryptographic signature (`sender_signature`) calculated via HMAC-SHA256 over a canonical message string format (`message_id|protocol_version|timestamp|sender|recipient|type|priority|trace_id|schema|payload|nonce`). Nonces and timestamps prevent replay attacks.

---

## 2. Authorization & Role-Based Access Control (RBAC)

MACMS enforces least-privilege RBAC policies mapped directly to agent responsibilities:

| Agent Identifier | Allowed Capabilities | Kafka Topic Publish Permissions | Kafka Topic Read Permissions |
| :--- | :--- | :--- | :--- |
| `agent-tm-001` | `pattern_detection`, `threshold_monitoring`, `temporal_analysis`, `counterparty_analysis`, `cross_market_surveillance` | `mcms.agent-tm-001.*`, `mcms.heartbeat` | `mcms.ingress.transactions`, `mcms.agent-tm-001.*` |
| `agent-cs-001` | `keyword_detection`, `sentiment_analysis`, `information_barrier_monitoring`, `record_keeping_compliance`, `privilege_detection` | `mcms.agent-cs-001.*`, `mcms.heartbeat` | `mcms.ingress.communications`, `mcms.agent-cs-001.*` |
| `agent-ru-001` | `regulatory_feed_monitoring`, `impact_assessment`, `timeline_extraction`, `cross_regulation_conflict`, `precedent_analysis` | `mcms.agent-ru-001.*`, `mcms.heartbeat` | `mcms.ingress.regulatory`, `mcms.agent-ru-001.*` |
| `agent-rg-001` | `scheduled_reports`, `event_triggered_reporting`, `multi_audience_adaptation`, `evidence_compilation`, `regulatory_filing_preparation` | `mcms.agent-rg-001.*`, `mcms.heartbeat`, `mcms.escalation.human` | `mcms.agent-rg-001.*`, `mcms.escalation.human` |

---

## 3. Cryptography & Encryption Standards

1. **Data in Transit**: Enforced TLS 1.3 using cipher suites `TLS_AES_256_GCM_SHA384` and `TLS_CHACHA20_POLY1305_SHA256`. Older protocol versions (TLS 1.0, 1.1, 1.2) are explicitly disabled.
2. **Data at Rest**: Storage volumes, database partitions, and Kafka log segments are encrypted using AES-256-GCM. Sensitive fields (PII, voice transcripts) utilize envelope encryption with master keys stored in a Hardware Security Module (HSM).
3. **Audit Trail Hashing**: SHA-256 cryptographic hash chaining guarantees tamper-evident logging across all system state transitions.

---

## 4. Hardware Security Module (HSM) & Key Lifecycle

- **HSM Provider**: PKCS#11 compliant Hardware Security Module.
- **Key Rotation Policy**:
  - **Transport Certificates (X.509)**: Rotated automatically every 90 days.
  - **HMAC / Agent Signing Keys**: Rotated every 30 days.
  - **Master Encryption Keys (MEK)**: Rotated annually with automatic key versioning for historic decryption.
- **Revocation**: CRL (Certificate Revocation List) and OCSP stapling checked continuously by all agents during handshake execution.
