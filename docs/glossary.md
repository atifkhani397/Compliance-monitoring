---
title: MACMS Regulatory & Compliance Monitoring Glossary
date: 2026-09-02
version: 1.0.0
status: Approved
---

# MACMS Regulatory & Compliance Monitoring Glossary

This document provides definitive definitions for all regulatory, financial, technical, and compliance terms referenced throughout the MACMS specification and implementation.

---

## A

* **Aadhaar Act 2016**: Indian legislation providing statutory backing to the 12-digit Aadhaar unique identification number. Governs eKYC and mandates PII masking.
* **Alert Payload**: A structured inter-agent message carrying violation details, severity, confidence scores, evidence references, and affected entity lists.
* **Algorithmic Trading**: Automated execution of trade orders using pre-programmed trading instructions driven by parameters such as timing, price, or quantity.
* **Audit Chain**: A tamper-evident, append-only log structure utilizing SHA-256 cryptographic hash chaining to record system state transitions.

## B

* **Backpressure**: System control mechanism activated when incoming message rates exceed downstream consumption capacity.
* **Bayesian Fusion**: Consensus method updating probability estimates as new evidence or agent outputs arrive.
* **Best Execution**: Regulatory duty under MiFID II and SEC rules requiring brokers to execute customer orders on terms most favorable to the client.

## C

* **C4 Model**: Architectural framework describing software systems across Context, Container, Component, and Code abstraction levels.
* **Chinese Wall (Information Barrier)**: Virtual or physical barrier preventing communication or information sharing between public and private departments.
* **Common Name (CN)**: The Subject attribute in an X.509 certificate representing the cryptographic identity (e.g. `agent-tm-001`).
* **Cryptographic Non-Repudiation**: Operational assurance that a signed message or transaction cannot be denied by the originating sender.

## D

* **Dead Letter Queue (DLQ)**: A dedicated Kafka topic or routing queue for messages that fail validation or exceed maximum retry limits.
* **Dempster-Shafer Theory**: Mathematical framework for combining evidence from multiple sources to compute degrees of belief under uncertainty.
* **Digital Personal Data Protection (DPDP) Act 2023**: Indian privacy law regulating digital processing of personal data.

## E

* **eKYC**: Electronic Know Your Customer process for digital customer identity verification.
* **Evidence Package**: A aggregated collection of trade data, communication transcripts, and regulatory citations supporting a compliance decision.
* **Explainable AI (XAI)**: Surveillance model output presenting interpretable feature importance scores (e.g. SHAP values).

## F

* **FATCA**: Foreign Account Tax Compliance Act enforcing reporting of foreign financial assets by US taxpayers.
* **FIU-IND**: Financial Intelligence Unit - India, the national agency responsible for receiving and analyzing financial intelligence regarding money laundering.
* **Front-Running**: Illegal practice of entering a trade with prior knowledge of a pending non-public customer order.

## G

* **GDPR**: General Data Protection Regulation (EU 2016/679) enforcing strict data privacy and protection controls.
* **Greenwashing**: Deceptive marketing suggesting an investment fund's holdings or practices are environmentally sustainable when they are not.

## H

* **HMAC-SHA256**: Keyed-hash message authentication code algorithm ensuring message integrity and origin authenticity.
* **Hardware Security Module (HSM)**: Dedicated physical computing device safeguarding and managing digital master keys.

## M

* **MACMS**: Multi-Agent Compliance Monitoring System.
* **MiFID II**: Markets in Financial Instruments Directive II, European regulation governing financial markets and trade transparency.
* **Mutual TLS (mTLS)**: Transport Layer Security protocol wherein both client and server present X.509 digital certificates to authenticate each other.

## P

* **PMLA**: Prevention of Money Laundering Act 2002 (India), establishing legal frameworks to prevent money laundering and confiscate property derived from money laundering.
* **PFS (Perfect Forward Secrecy)**: Feature of key-agreement protocols ensuring compromise of long-term keys does not compromise past session keys.

## R

* **RBI**: Reserve Bank of India, India's central bank and monetary authority regulating banks and payment systems.
* **RBAC**: Role-Based Access Control enforcing access permissions based on defined organizational roles.

## S

* **SAR / STR**: Suspicious Activity Report / Suspicious Transaction Report filed with regulatory bodies (FinCEN / FIU-IND).
* **SEBI**: Securities and Exchange Board of India, regulator of securities and commodity markets in India.
* **Spoofing**: Market manipulation tactic of submitting non-bona fide orders that are cancelled before execution.

## U

* **UPI (Unified Payments Interface)**: Real-time instant payment system developed by National Payments Corporation of India (NPCI).

## V

* **VASP**: Virtual Asset Service Provider conducting cryptocurrency transfers or custody operations.
