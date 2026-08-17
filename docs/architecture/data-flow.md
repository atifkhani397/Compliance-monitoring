---
title: MACMS Data Flow Architecture Specification
date: 2026-08-17
version: 1.0.0
status: Approved
---

# MACMS Data Flow & Pipeline Architecture

This document specifies the end-to-end data lifecycle, ingestion pipelines, processing stages, storage classifications, and data residency governance for the Multi-Agent Compliance Monitoring System (MACMS).

---

## 1. Data Ingestion Architecture

```
+-----------------------------------------------------------------------------------+
| Source Systems                                                                    |
|  - FIX Protocol (Trading Platforms)                                               |
|  - IMAP/SMTP (Email Servers)                                                      |
|  - RSS / API Feeds (Regulatory Circulars)                                         |
|  - Voice Transcription (Audio Feeds)                                              |
|  - Document Management Systems (DMS)                                              |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| Ingestion & Streaming Layer                                                       |
|  - Kafka Connect Connectors (Debezium / Custom Sinks)                             |
|  - Confluent Schema Registry (Avro / JSON Schema Validation)                      |
|  - Cryptographic Nonce & Signature Verification                                   |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| Processing & Analytics Layer                                                      |
|  - TM Consumer Group (Market Abuse Detection)                                     |
|  - CS Consumer Group (Communication Surveillance)                                 |
|  - RU Consumer Group (Regulatory Change Extraction)                               |
|  - RG Consumer Group (Report Generation & Hash Chaining)                          |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| Output & Storage Layer                                                            |
|  - Immutable Audit Chain Log (JSONL / WORM Storage)                               |
|  - Regulatory Filing Gateways (SEC / FINRA / RBI / SEBI APIs)                     |
|  - Compliance Officer Web Dashboard                                               |
+-----------------------------------------------------------------------------------+
```

---

## 2. Ingestion & Processing Pipeline Details

1. **Transaction Data Stream**:
   - Source: FIX 4.2 / 4.4 engines.
   - Flow: Ingested via Kafka FIX Connector into `macms.ingress.transactions`.
   - Consumer: `agent-tm-001` performs real-time windowed aggregations.

2. **Communication Stream**:
   - Source: Microsoft Exchange (IMAP/Graph API), Bloomberg Chat exports.
   - Flow: Pushed to `macms.ingress.communications` with payload encryption.
   - Consumer: `agent-cs-001` runs NLP entity extraction and sentiment analysis.

3. **Regulatory Feed Stream**:
   - Source: Polled web scrapers for RBI, SEBI, SEC, and FCA circulars.
   - Flow: Pushed to `macms.ingress.regulatory`.
   - Consumer: `agent-ru-001` classifies regulatory updates and triggers policy recalculations.

4. **Orchestrator Dispatch & Inter-Agent Payload Schema**:
   - Central Dispatch: All inter-agent communications pass through `Orchestrator.dispatch(message)`.
   - Message Payload Envelopes:
     - `ALERT`: `AlertPayload` (`violation_type`, `severity`, `detected_at`, `evidence_refs`, `affected_entities`)
     - `QUERY`: `QueryPayload` (`query_type`, `parameters`, `response_schema_required`)
     - `RESPONSE`: `ResponsePayload` (`query_id`, `status`, `result_data`, `errors`)
     - `UPDATE`: `UpdatePayload` (`update_type`, `entity_id`, `changed_fields`, `previous_values`)
     - `HEARTBEAT`: `HeartbeatPayload` (`agent_status`, `queue_depth`, `last_processed_timestamp`)
     - `ESCALATION`: `EscalationPayload` (`escalation_reason`, `recommended_tier`, `decision_support_package_ref`, `human_assignee_role`)

---

## 3. Data Classification & Security Handling

All data elements flowing through MACMS are tagged according to Meridian Global Bank's 4-tier data classification policy:

| Classification | Sensitivity Level | Sample Data Fields | Encryption Standard | Access Restriction |
| :--- | :--- | :--- | :--- | :--- |
| **Public** | Low | Public regulatory circulars, market indices | None (Integrity checked) | Open Read |
| **Internal** | Medium | System telemetry, heartbeat logs, agent IDs | TLS 1.3 in transit | Authenticated Agents |
| **Confidential** | High | Trader IDs, trade execution parameters, timestamps | TLS 1.3 + AES-256 at rest | RBAC Enforcement |
| **Restricted** | Critical | PII, audio transcripts, account numbers, SAR filings | Envelope Encryption (HSM) | Strictly Audit-Logged |

---

## 4. India Data Residency Governance (RBI Mandate)

In compliance with the **Reserve Bank of India (RBI) Directive on Storage of Payment System Data** and SEBI cybersecurity guidelines:

1. **Primary Data Residency**: All raw transaction records, communication logs, audio transcripts, and audit logs originating from Meridian Global Bank's India operations must be stored exclusively on primary servers located within the physical borders of India.
2. **Cross-Border Processing Controls**: No PII or plaintext trading communications may leave the domestic cloud availability zones. Remote processing by agents requires anonymization and local cryptographic key wrapping.
3. **Audit Trail Verification**: Audit chain hashes for Indian domestic entities must be mirrored to local Write-Once-Read-Many (WORM) storage appliances in Mumbai/Hyderabad datacenters.
