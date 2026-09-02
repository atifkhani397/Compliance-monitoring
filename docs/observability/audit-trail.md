---
title: MACMS Cryptographic Audit Trail Specification
date: 2026-08-22
version: 2.0.0
status: Implemented
---

# MACMS Cryptographic Audit Trail Specification

## 1. Regulatory Properties

The MACMS audit trail is append-only during the retention period. Audit entries are immutable Pydantic records and there are no update or delete operations. Every significant action is recorded with enough context to reconstruct the decision chain: message send and receive, agent state change, escalation trigger, human decision, threshold update, and consensus resolution.

Each entry is authenticated with HMAC-SHA256 using an agent- or human-specific key. The current implementation keeps the key map in configuration; the Phase 8 upgrade path is ECDSA P-256. Timestamps are UTC ISO 8601 values sourced from the host NTP-synchronized clock, with an operational clock-skew tolerance target below 100 ms.

## 2. Hash-Chain Mechanics

For entry `n`, MACMS computes:

```text
previous_hash_0 = SHA256("MERIDIAN_GENESIS_BLOCK")
current_hash_n = SHA256(previous_hash_n || timestamp_n || agent_id_n || canonical_data_n || canonical_metadata_n)
```

Canonical JSON uses sorted keys and compact separators. Metadata includes the trace ID, action type, action data, HMAC signature, and nonce. Any mutation of an entry or its position breaks `AuditChain.verify_chain()` and causes `AuditIntegrityError`.

## 3. Entry Schema

| Field | Meaning |
| --- | --- |
| `timestamp` | UTC event time. |
| `trace_id` | Inter-agent distributed-trace correlation identifier. |
| `agent_id` | Agent or human identity creating the event. |
| `action_type` | Significant action category. |
| `action_data` | Structured event context. |
| `previous_hash` | Hash of the preceding entry. |
| `current_hash` | Hash of the current entry. |
| `signature` | Base64 HMAC-SHA256 signature. |
| `nonce` | Per-entry uniqueness value. |

The legacy `index` and `data` fields remain available for Phase 1–4 compatibility. The structured log itself is stored in `data` and duplicated into `action_data` where appropriate.

## 4. Verification, Query, and Export

Every historical query first verifies the complete chain and signatures, then applies trace, agent, and UTC date filters. JSONL and CSV exports use the same verified entries. Authorized retrieval is exposed through the API-key-protected dashboard API; the target historical query latency is below 30 seconds.

## 5. Reproducibility and Retention

A decision is reproducible when the same input messages, deterministic algorithm configuration, agent weights, evidence references, and preceding audit trail are supplied. Retention categories and jurisdictional overrides are defined in `retention-policy.md`; no entry may be deleted during its applicable retention period.
