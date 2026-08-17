---
title: Agent Capability Matrix & Boundary Definitions
version: 2.0.0
date: 2026-08-17
status: Phase 2 Complete
---

# Agent Capability Matrix & Boundary Definitions

## 1. Overview

This document specifies the comprehensive capability ownership matrix across all four primary agents in the Multi-Agent Compliance Monitoring System (MACMS):
- **TM**: Transaction Monitor (`agent-tm-001`)
- **CS**: Communication Scanner (`agent-cs-001`)
- **RU**: Regulatory Update Tracker (`agent-ru-001`)
- **RG**: Report Generator (`agent-rg-001`)

It establishes clear boundary contracts for all agent pairs to govern data exchanges and shared responsibilities, and provides a gap analysis identifying compliance functions outside the current agent scope along with mitigation strategies.

---

## 2. Cross-Agent Capability Matrix

### Classification Legend
- **PRIMARY**: The agent owns, executes, and holds primary responsibility for this capability.
- **SECONDARY**: The agent supports this capability with secondary data processing or validation.
- **SHARED**: Multiple agents collaborate directly to execute this capability.
- **NONE**: The agent does not participate in this capability.

| # | Capability Name | TM (`agent-tm-001`) | CS (`agent-cs-001`) | RU (`agent-ru-001`) | RG (`agent-rg-001`) |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | **Pattern Detection** | **PRIMARY** | NONE | NONE | NONE |
| 2 | **Threshold Monitoring** | **PRIMARY** | NONE | SECONDARY | NONE |
| 3 | **Temporal Analysis** | **PRIMARY** | SECONDARY | NONE | NONE |
| 4 | **Counterparty Analysis** | **PRIMARY** | SECONDARY | NONE | NONE |
| 5 | **Cross-Market Surveillance** | **PRIMARY** | NONE | NONE | NONE |
| 6 | **Keyword & Phrase Detection** | NONE | **PRIMARY** | NONE | NONE |
| 7 | **Sentiment & Intent Analysis** | NONE | **PRIMARY** | NONE | NONE |
| 8 | **Information Barrier Monitoring** | SECONDARY | **PRIMARY** | NONE | NONE |
| 9 | **Record-Keeping Compliance** | NONE | **PRIMARY** | SECONDARY | NONE |
| 10 | **Privilege Detection** | NONE | **PRIMARY** | NONE | SECONDARY |
| 11 | **Regulatory Feed Monitoring** | NONE | NONE | **PRIMARY** | NONE |
| 12 | **Impact Assessment** | SECONDARY | SECONDARY | **PRIMARY** | NONE |
| 13 | **Timeline Extraction** | NONE | NONE | **PRIMARY** | SECONDARY |
| 14 | **Cross-Regulation Conflict** | NONE | NONE | **PRIMARY** | NONE |
| 15 | **Precedent Analysis** | SECONDARY | NONE | **PRIMARY** | NONE |
| 16 | **Scheduled Reports** | NONE | NONE | NONE | **PRIMARY** |
| 17 | **Event-Triggered Reporting** | SECONDARY | SECONDARY | NONE | **PRIMARY** |
| 18 | **Multi-Audience Adaptation** | NONE | NONE | NONE | **PRIMARY** |
| 19 | **Evidence Compilation** | SECONDARY | SECONDARY | SECONDARY | **PRIMARY** |
| 20 | **Regulatory Filing Preparation** | NONE | NONE | SECONDARY | **PRIMARY** |

---

## 3. Boundary Contract Definitions

Inter-agent communication is mediated exclusively by the central Orchestrator (`src/mcms/core/orchestrator.py`). Direct agent-to-agent coupling is prohibited. Below are the pair-wise boundary contracts governing data inputs, outputs, and shared responsibilities.

### 3.1 TM-CS Boundary (Transaction Monitor ↔ Communication Scanner)
- **TM Provides**: Transaction IDs, timestamps, asset class, trade volume, price anomalies, counterparty identifiers.
- **CS Provides**: Communication content excerpts, participant IDs, channel metadata, sentiment flags, keyword matches.
- **Shared Responsibility**: Trade-Communication Correlation (detecting insider trading, front-running, and spoofing where communications coincide with anomalous trades).
- **Processing Isolation**: TM has no access to raw communication text; CS has no access to raw order book data.

### 3.2 TM-RU Boundary (Transaction Monitor ↔ Regulatory Tracker)
- **TM Provides**: Detection threshold effectiveness metrics, false positive rates, volume breach statistics.
- **RU Provides**: Threshold calibration updates, regulatory rule changes (e.g., SEBI/SEC position limit updates), new prohibited trading patterns.
- **Shared Responsibility**: Regulatory Threshold Alignment (ensuring automated surveillance rules strictly reflect current multi-jurisdictional mandates).
- **Processing Isolation**: TM cannot update its own threshold configurations; RU cannot directly inspect trading queues.

### 3.3 TM-RG Boundary (Transaction Monitor ↔ Report Generator)
- **TM Provides**: Alert payloads (`AlertPayload`), anomaly confidence scores, transaction evidence references, trade data extracts.
- **RG Provides**: Formatted compliance reports, SAR/STR draft sections, execution metrics dashboards.
- **Shared Responsibility**: No shared processing. Strict producer-consumer relationship (TM produces alerts, RG formats reports).

### 3.4 CS-RU Boundary (Communication Scanner ↔ Regulatory Tracker)
- **CS Provides**: Communication pattern statistics, lexicon match rates, Chinese wall breach occurrences, record-keeping gap data.
- **RU Provides**: Regulatory communication requirements (e.g., SEC 17a-4, MiFID II SYSC retention rules, mandatory disclosure disclaimers).
- **Shared Responsibility**: Record-Keeping Rule Updates (aligning communication archiving lexicons and retention periods with shifting legal standards).
- **Processing Isolation**: CS cannot interpret ambiguous statutory text; RU cannot inspect active communication streams.

### 3.5 CS-RG Boundary (Communication Scanner ↔ Report Generator)
- **CS Provides**: Communication excerpts, participant lists, privilege risk flags, evidence references.
- **RG Provides**: PII redaction verification, privilege review packages, formatted evidence binders.
- **Shared Responsibility**: Privilege Review & Redaction Workflow (ensuring attorney-client privileged items are flagged and redacted prior to external report generation).

### 3.6 RU-RG Boundary (Regulatory Tracker ↔ Report Generator)
- **RU Provides**: Regulatory filing requirements, submission deadlines, filing taxonomies (XBRL/XML specifications), regulatory contact points.
- **RG Provides**: Filing status updates, completion confirmations, submission audit trail entries.
- **Shared Responsibility**: Compliance Calendar Management (tracking statutory filing schedules against completion milestones).

---

## 4. Gap Analysis & Mitigation Strategies

While the four primary agents cover core transaction monitoring, communication scanning, regulatory tracking, and reporting, certain specialized compliance functions fall outside their direct scope.

| Gap Area | Description | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **KYC / AML Identity Verification** | Customer onboarding identity verification, beneficial ownership lookup, sanction screening. | High | Ingestion layer integrates with external Bank AML Engine; TM consumes clean counterparty risk scores via Counterparty Analysis capability. |
| **Physical Security & Access Control** | Physical trading floor access, badge scans, facility security monitoring. | Medium | Event logs from Physical Security Information Management (PSIM) ingested into Kafka; CS correlates physical access with Chinese wall breaches. |
| **HR / Employee Risk Profiling** | Personal trading clearance, outside business activities (OBA), disciplinary history. | Medium | HR compliance metrics ingested into Orchestrator context; CS uses participant roles to contextualize sentiment and privilege flags. |
| **Model Risk Management (MRM)** | Independent validation and drift monitoring of deep learning surveillance models. | High | Periodic model performance summaries published via `UPDATE` messages to MRM audit queues; RU monitors enforcement actions to trigger recalibration. |
