---
title: Communication Scanner Agent Specification
agent_id: agent-cs-001
version: 2.0.0
date: 2026-08-17
status: Phase 2 Complete
---

# Communication Scanner Agent (agent-cs-001)

## 1. Overview

The Communication Scanner Agent monitors and analyzes all forms of regulated communications across Meridian Global Bank. It detects compliance-relevant keywords, analyzes sentiment and intent, monitors information barriers (Chinese walls), verifies record-keeping compliance, and identifies potentially privileged communications.

---

## 2. Capability Table

| Capability | Description | Scope | Input Data | Output Data | SLA |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Keyword & Phrase Detection** | Identify compliance-relevant keywords, codewords, euphemisms using configurable lexicons | Multi-language: English, Mandarin, Hindi, Spanish minimum | Email, IM, voice transcripts, social media | Keyword match alerts with context | P95 < 3s |
| **Sentiment & Intent Analysis** | Detect coercive language, misleading statements, unsuitable recommendations, pressure tactics | All customer-facing channels | Communication content, customer profile data | Sentiment anomaly alerts | P95 < 5s |
| **Information Barrier Monitoring** | Detect potential breaches of Chinese walls between public and private-side teams | Cross-departmental communication analysis | Department directory, deal calendar, communication metadata | Chinese wall breach alerts | P95 < 10s |
| **Record-Keeping Compliance** | Verify all regulated communications are captured and retained per regulatory requirements | SEC 17a-4, MiFID II, FCA SYSC | Communication metadata, retention policies | Record-keeping gap alerts | Batch: 1 hour |
| **Privilege Detection** | Identify potentially privileged communications requiring special handling | Attorney-client, work product, regulatory examination | Communication participants, legal matter database | Privilege flag alerts | P95 < 5s |

---

## 3. Constraints

- **No End-to-End Decryption**: Cannot decrypt end-to-end encrypted communications; analysis is limited to communications available in plaintext or through authorized decryption gateways.
- **Voice Analysis Limitation**: Voice analysis is limited to transcribed text; direct audio analysis, speaker identification, and tone analysis are not in scope for Phase 2.
- **Data Retention Boundaries**: Must respect data retention boundaries defined by regulatory and internal policies; cannot retain communication data beyond prescribed retention periods.
- **No Independent Privilege Determination**: Cannot independently determine legal privilege; privilege detection flags must be reviewed by legal counsel before any action is taken.
- **Privacy-Preserving Analysis**: Personal communications inadvertently captured must be handled through privacy-preserving analysis pipelines with automatic PII redaction.

---

## 4. Input Interfaces

| Protocol | Source | Data Format | Frequency |
| :--- | :--- | :--- | :--- |
| IMAP/SMTP | Email servers | RFC 5322 email messages (headers, body, attachments) | Near real-time (polling 30s) |
| Bloomberg/Symphony API | Instant message platforms | JSON (messages, metadata, participants) | Real-time streaming |
| Microsoft Teams API | Collaboration platform | JSON (messages, channels, participants) | Real-time webhook |
| Voice Transcription API | Telephony systems | JSON (transcribed text, speaker labels, timestamps) | Post-call batch |
| DMS API | Document management systems | JSON/XML (documents, metadata, access logs) | On-change |

---

## 5. Output Interfaces

| Message Type | Destination | Content | Routing |
| :--- | :--- | :--- | :--- |
| ALERT | Orchestrator | Communication compliance violations with keyword matches, sentiment scores, context excerpts | Via orchestrator dispatch |
| QUERY | Transaction Monitor (agent-tm-001) | Trade-communication correlation requests with communication timestamps, participants | Via orchestrator dispatch |
| UPDATE | Report Generator (agent-rg-001) | Communication monitoring statistics, coverage metrics, gap reports | Via orchestrator dispatch |
| HEARTBEAT | Orchestrator | Agent health status, scanning throughput, language model status | Direct to heartbeat topic |

---

## 6. Resource Requirements

| Resource | Specification | Notes |
| :--- | :--- | :--- |
| vCPU | 24 | NLP model inference and parallel scanning |
| Memory | 96 GB RAM | Multi-language NLP model loading and caching |
| Storage | SSD | Communication corpus and lexicon databases |
| Specialized Models | Multi-language NLP | English, Mandarin, Hindi, Spanish support minimum |
| PII Pipeline | Dedicated | Automatic PII redaction before storage |

---

## 7. Privacy Requirements

| Regulation | Requirement | Implementation |
| :--- | :--- | :--- |
| GDPR Article 25 | Data protection by design and default | PII redaction pipeline, data minimization in processing |
| CCPA | Consumer privacy rights | Communication content not retained beyond analysis window |
| Data Minimization | Process minimum necessary data | Only compliance-relevant content extracted and stored |
| Right to Erasure | Support data deletion requests | Communication analysis indices support targeted deletion |
| Aadhaar Act 2016 | Mandatory PII masking & eKYC audit | Mask 12-digit UIDs (only last 4 digits visible: `XXXX-XXXX-1234`), verify UIDAI consent audit tokens |

---

## 8. Health Check Endpoint

```json
{
  "agent_id": "agent-cs-001",
  "status": "HEALTHY | DEGRADED | UNHEALTHY",
  "uptime_seconds": 86400.0,
  "queue_depth": 45,
  "processed_count": 892340,
  "last_processed_timestamp": "2026-08-17T08:00:00+00:00",
  "capabilities_status": {
    "keyword_detection": "ACTIVE",
    "sentiment_analysis": "ACTIVE",
    "information_barrier_monitoring": "ACTIVE",
    "record_keeping_compliance": "ACTIVE",
    "privilege_detection": "ACTIVE"
  },
  "nlp_model_status": {
    "english": "LOADED",
    "mandarin": "LOADED",
    "hindi": "LOADED",
    "spanish": "LOADED"
  }
}
```
