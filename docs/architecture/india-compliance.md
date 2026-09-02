---
title: MACMS India Jurisdiction Regulatory Compliance Architecture
date: 2026-09-02
version: 1.0.0
status: Approved
---

# MACMS India Jurisdiction Regulatory Compliance Architecture

## 1. Executive Summary

This document specifies the regulatory compliance framework, architectural constraints, data sovereignty enforcement, and reporting schemas for **Meridian Global Bank** operations within the Indian financial jurisdiction. MACMS implements multi-regulator compliance across SEBI, RBI, IRDAI, PFRDA, and MCA.

---

## 2. Multi-Regulator Ecosystem Structure

| Regulatory Body | Jurisdiction & Oversight Scope | Key Acts & Circulars | MACMS Agent Responsibility |
| :--- | :--- | :--- | :--- |
| **SEBI** (Securities and Exchange Board of India) | Capital markets, stock exchanges, insider trading, algorithmic trading, mutual funds. | Prohibition of Insider Trading (PIT) Regulations 2015, SEBI AI/ML Circular 2024, SEBI LODR 2015. | `agent-tm-001`, `agent-cs-001`, `agent-ru-001` |
| **RBI** (Reserve Bank of India) | Commercial banking, payment systems, foreign exchange (FEMA), digital lending. | RBI Data Localisation Directive 2018, Digital Lending Guidelines 2022, Master Direction on Fraud 2016. | `agent-tm-001`, `agent-ru-001`, `agent-rg-001` |
| **FIU-IND** (Financial Intelligence Unit - India) | Anti-Money Laundering (AML) and Countering Financing of Terrorism (CFT). | Prevention of Money Laundering Act (PMLA) 2002, PML Rules 2005. | `agent-rg-001` |
| **UIDAI / MeitY** | Aadhaar identification, eKYC, digital privacy, IT Act 2000. | Aadhaar Act 2016, Digital Personal Data Protection (DPDP) Act 2023. | `agent-cs-001` |
| **MCA** (Ministry of Corporate Affairs) | Corporate governance, connected entities, director disclosures. | Companies Act 2013, Significant Beneficial Ownership (SBO) Rules. | `agent-tm-001` |

---

## 3. Data Sovereignty & RBI Data Localisation (2018 Circular)

In strict adherence to RBI Circular `DPSS.CO.OD.No.2785/06.08.005/2017-18`:

1. **Primary Data Storage**: All end-to-end transaction data, trade logs, payment instructions, message payloads, and customer financial records originating in India are stored **exclusively on servers physically located inside India** (Mumbai / Hyderabad primary data centers).
2. **Cross-Border Processing Restriction**: Foreign trade legs processed abroad for international routing must return the full transaction log to India storage within **24 hours**. No primary payment or trade details may remain outside India beyond operational routing requirements.
3. **Geographic Partitioning**: Kafka topics dedicated to Indian trading desks (`mcms.in.*`) are pinned to India-only Kafka broker clusters with geo-fencing network controls.

---

## 4. Aadhaar Act 2016 & PII Masking Standards

In compliance with the Aadhaar Act 2016 and DPDP Act 2023:

1. **Log Redaction & Masking**: Any Aadhaar number (12-digit UID) detected in structured or unstructured communication feeds (emails, chats, voice transcripts) is automatically redacted before persistence.
   - **Pattern**: `\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b`
   - **Masked Output**: `XXXX-XXXX-1234` (only last 4 digits visible).
2. **UIDAI Consent Audit Trail**: Any eKYC or Aadhaar verification query logged by MACMS includes an immutable consent token reference (`uidai_consent_ref`) verifying explicitly logged user consent.

---

## 5. Prevention of Money Laundering Act (PMLA 2002) & FIU-IND STR Filings

1. **Suspicious Transaction Reporting (STR)**:
   - Suspicious trades, wash sales, or structured deposits exceeding ₹10,000,000 (INR 1 Crore) automatically trigger P1-CRITICAL alerts.
   - `agent-rg-001` automatically compiles FIU-IND compliant XML/JSON STR packages containing suspect profiles, trade timestamps, connected entities, and evidence hashes.
2. **Mandatory Audit Retention**: All transaction monitoring audit chains are archived for **10 years** as mandated under Section 12 of PMLA 2002.

---

## 6. SEBI AI/ML Surveillance Framework (2024 Circular)

Under the 2024 SEBI Circular on AI/ML applications in securities surveillance:

1. **Explainable AI (XAI)**: All machine learning detection models (e.g. wash sale classifiers, NLP sentiment engines) must emit human-understandable feature attribution scores (SHAP / LIME values) accompanying every alert payload.
2. **Independent Model Validation**: Surveillance algorithms must undergo independent annual validation covering bias, false-positive drift, and edge-case behavior.
3. **Quarterly Reporting**: `agent-rg-001` produces quarterly AI/ML usage reports for submission to SEBI detailing model versions, alert volumes, precision/recall metrics, and human override statistics.
