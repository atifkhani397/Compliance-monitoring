---
title: MACMS Security Architecture Specification
date: 2026-09-02
version: 2.0.0
status: Approved - Production Hardened
---

# MACMS Security Architecture Specification

This document defines the production-grade security architecture, cryptographic controls, identity management, access control frameworks, secrets infrastructure, and vulnerability management lifecycle for the Multi-Agent Compliance Monitoring System (MACMS) at Meridian Global Bank.

---

## 1. Authentication & Agent Identity Management

### 1.1 Mutual TLS (mTLS) & Certificate Hierarchy
Every node and agent within MACMS (`agent-tm-001`, `agent-cs-001`, `agent-ru-001`, `agent-rg-001`, and Orchestrator) requires mutual cryptographic authentication over mTLS.

- **Certificate Authority (CA) Hierarchy**:
  - **Root CA**: Meridian Global Enterprise Offline Root CA (2048-bit RSA / 384-bit ECDSA, offline cold storage).
  - **Intermediate CA**: Meridian MACMS Production Issuing CA.
  - **Leaf / Agent Certificates**: Issued exclusively for MACMS agent nodes with X.509 Subject `CN = <agent_id>`.
- **Certificate Lifecycle**:
  - **Agent Certificate Validity**: 90 days.
  - **Automated Renewal**: Auto-renewed 30 days prior to expiration via ACME / EST protocol.
  - **Certificate Binding**: Strict validation of Subject `CN` against registered `VALID_AGENT_IDS`. Connections with mismatched CNs are rejected immediately.
  - **Revocation Checking**: Mandatory CRL (Certificate Revocation List) caching and real-time OCSP (Online Certificate Status Protocol) stapling during TLS handshakes.

---

## 2. In-Transit & At-Rest Encryption Standards

### 2.1 Transport Layer Security (TLS 1.3)
All inter-agent, Kafka broker, schema registry, and REST API communications enforce TLS 1.3. Legacy protocol versions (TLS 1.0, 1.1, 1.2) are explicitly disabled.

- **Mandatory Cipher Suites**:
  - `TLS_AES_256_GCM_SHA384`
  - `TLS_CHACHA20_POLY1305_SHA256`
- **Perfect Forward Secrecy (PFS)**: Required using Ephemeral Elliptic-Curve Diffie-Hellman (ECDHE) key exchange with curve `secp384r1` or `x25519`.

### 2.2 Data at Rest Encryption
- **Symmetric Encryption**: AES-256-GCM for all persistent message payloads, Kafka log segments, state stores (RocksDB), and relational databases.
- **Key Derivation Function (KDF)**: PBKDF2 with SHA-256 and 100,000 iterations to derive symmetric encryption keys from master secrets.
- **Data Key Rotation**: Data encryption keys (DEKs) are rotated automatically every 90 days, with background re-encryption of stored audit segments.

---

## 3. Hardware Security Module (HSM) Integration

To guarantee that private keys and root signing materials are never exposed in software memory, MACMS integrates with FIPS 140-2 Level 3 validated Hardware Security Modules (HSMs).

- **Supported HSM Platforms**:
  - **Cloud Native**: AWS CloudHSM
  - **Enterprise On-Premises**: Thales Luna 7 HSM
  - **Edge / Appliance**: YubiHSM 2
- **Key Security Invariants**:
  - Master Signing Keys (MSK) and Root CA keys are generated inside the HSM hardware perimeter.
  - Private keys **never leave the HSM** under any operational scenario.
  - Cryptographic operations (HMAC-SHA256 signing, master key decryption) are executed within the HSM via PKCS#11 / KMIP APIs.

---

## 4. Role-Based Access Control (RBAC) & Just-in-Time Access

MACMS enforces strict Role-Based Access Control (RBAC) adhering to the Principle of Least Privilege across 5 core roles and 20+ granular operations.

### 4.1 RBAC Roles
1. **System Administrator**: Infrastructure management, service lifecycle control, and system configuration.
2. **Compliance Officer**: Alert triage, case review, escalation management, and decision override.
3. **Auditor**: Read-only verification of cryptographic audit trails, reports, and system telemetry.
4. **Agent Service Account**: Machine-to-machine inter-agent execution, event publishing, and state synchronization.
5. **Read-Only Analyst**: Surveillance log view-only access without PII payload decryption rights.

### 4.2 Permissions Matrix (5 Roles x 20 Operations)

| Operation / Capability | System Admin | Compliance Officer | Auditor | Agent Service Account | Read-Only Analyst |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `agent.register` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `agent.unregister` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `agent.process_message` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `message.publish_alert` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `message.publish_query` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `message.publish_response` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `alert.triage` | ❌ | ✅ | ❌ | ❌ | ❌ |
| `alert.escalate` | ❌ | ✅ | ❌ | ✅ | ❌ |
| `audit.view_chain` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `audit.verify_integrity` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `audit.export_jsonl` | ✅ | ❌ | ✅ | ❌ | ❌ |
| `pii.decrypt_unmasked` | ❌ | ✅ (JIT) | ❌ | ❌ | ❌ |
| `report.generate_sar` | ❌ | ✅ | ❌ | ✅ | ❌ |
| `report.view_dashboard` | ✅ | ✅ | ✅ | ❌ | ✅ |
| `config.update_rules` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `security.rotate_keys` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `security.revoke_cert` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `hsm.manage_keys` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `dlq.reprocess_message` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `system.shutdown` | ✅ | ❌ | ❌ | ❌ | ❌ |

### 4.3 Just-in-Time (JIT) Access Control
Unmasked PII or raw communication transcript viewing requires temporary, time-bounded elevated privileges requested via the JIT portal. JIT approvals expire after 60 minutes and generate mandatory audit events logged to `macms.audit.chain`.

---

## 5. Secrets Management & Vault Infrastructure

MACMS integrates with **HashiCorp Vault KV v2** for centralized, secure management of operational secrets.

- **Secrets Storage**: All database passwords, API keys, Kafka SASL credentials, and HMAC signing salts are stored in HashiCorp Vault.
- **Dynamic Database Credentials**: Database access utilizes Vault dynamic secret engines, issuing short-lived DB credentials (TTL 4 hours).
- **Automatic Secret Rotation**: Vault automated rotators update database and API credentials every 30 days without system downtime.

---

## 6. Vulnerability & Threat Management Schedule

| Scanning / Audit Type | Tooling | Execution Frequency | Remediation SLA |
| :--- | :--- | :--- | :--- |
| **Dependency Vulnerability Scanning** | Snyk, OWASP Dependency-Check | Continuous (CI/CD Pipeline) | High/Critical: < 48 hours |
| **Container Image Scanning** | Trivy, Clair | Daily & Pre-Deployment | High/Critical: < 24 hours |
| **Static Application Security Testing (SAST)** | Bandit, Semgrep | Every Commit / PR | Block Build on High/Critical |
| **Dynamic Application Security Testing (DAST)** | OWASP ZAP | Weekly Automated Run | High/Critical: < 7 days |
| **Penetration Testing** | Independent 3rd-Party CREST Team | Semi-Annually | Immediate Remediation Plan |

---

## 7. Cryptographic Non-Repudiation & Canonical Hash Chaining

1. **Inter-Agent Message Non-Repudiation**:
   - Signature formula: `HMAC-SHA256(canonical_representation, signing_key)`
   - Canonical format: `message_id|protocol_version|timestamp|sender|recipient|type|priority|trace_id|payload_schema|payload_json|nonce`
2. **Tamper-Evident Audit Logging**:
   - `AuditEntry` contains `entry_id`, `timestamp`, `event_type`, `agent_id`, `data`, `previous_hash`, and `hash`.
   - `hash` calculation: `SHA256(entry_id|timestamp|event_type|agent_id|data_json|previous_hash)`
   - `AuditChain.verify_chain()` programmatically verifies chain continuity from genesis to tip.
