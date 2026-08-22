---
title: MACMS Data and Log Retention Policy
date: 2026-08-22
version: 2.0.0
status: Implemented
---

# MACMS Data and Log Retention Policy

## 1. Category Retention Matrix

| Category | Minimum retention | Special rule |
| --- | ---: | --- |
| Agent Lifecycle | 7 years | Preserve start, stop, heartbeat, and state changes. |
| Detection Events | 7 years | SAR-related detection events: 10 years. |
| Communication Events | 5 years | Preserve message and trace correlation. |
| Escalation Events | 7 years | Include assignment and SLA transitions. |
| Human Decision Events | 10 years | Include approvals, rejections, overrides, and justifications. |
| Report Generation | 7 years | Extend when a governing regulation requires it. |
| System Performance | 1 year rolling | Operational telemetry may roll after one year. |
| Security Events | 7 years | Preserve authentication, signature, and access events. |

## 2. Jurisdictional Overrides

The effective retention period is the maximum of the category requirement and jurisdictional requirement. SEC Rule 17a-4(f) requires seven years for applicable records, MiFID II requires five years, and the Phase 5 policy applies eight years for RBI-governed records. Payment data governed by RBI must remain on India-based servers. SAR-related evidence takes precedence at ten years.

## 3. Storage Lifecycle

Records remain in hot SSD storage for 90 days for low-latency examination. They move to warm SAS storage for the remainder of the first year and to cold tape or cloud storage for the remaining retention period. Logs older than 90 days use gzip compression; cold records use Zstandard compression. All archived data is encrypted at rest with AES-256-GCM, with keys managed outside the application process.

## 4. Immutability and Destruction

No record may be updated or deleted during its effective retention period. The append-only hash chain and HMAC signatures provide tamper evidence. After expiry, authorized destruction uses secure wipe procedures and produces a certificate of destruction containing the category, date range, authorization, method, and checksum of the destroyed archive. The in-memory Phase 5 implementation does not perform destructive operations; this policy defines the later archival boundary.

## 5. Examination and Access

Authorized personnel retrieve verified records through the audit API. Every query verifies chain integrity before returning results. Access requests must preserve trace ID, requester identity, scope, timestamp, and export format in a security audit event. Persistent WORM storage, key management, and jurisdiction-aware archival workers are reserved for the persistent-storage phase.
