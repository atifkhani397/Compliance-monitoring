---
title: MACMS Observability Logging Specification
date: 2026-08-17
version: 1.0.0
status: Approved
---

# MACMS Observability Logging Specification

This document defines the structured logging taxonomy, schema definition, retention policies, and trace correlation rules across the Multi-Agent Compliance Monitoring System (MACMS).

---

## 1. Appendix C Log Categories & Taxonomy

MACMS defines 8 mandatory log categories for system telemetry and regulatory auditing:

| Log Category Code | Category Name | Description & Event Scope | Default Severity Range | Min Retention Period |
| :--- | :--- | :--- | :--- | :--- |
| `LOG_CAT_01` | **Agent Lifecycle** | Startup, shutdown, heartbeat, state transitions, config reloads. | INFO to ERROR | 1 Year |
| `LOG_CAT_02` | **Detection Events** | Anomaly triggers, trade pattern flags, wash sale detections. | WARNING to CRITICAL | 7 Years |
| `LOG_CAT_03` | **Communication Events** | Inter-agent message sends/receives, routing retry events, DLQ pushes. | DEBUG to WARNING | 3 Years |
| `LOG_CAT_04` | **Escalation Events** | Human-in-the-loop triggers, priority elevation notifications. | INFO to CRITICAL | 7 Years |
| `LOG_CAT_05` | **Human Decision Events** | Compliance officer approvals, dismissals, notes, and override actions. | INFO to WARNING | 10 Years |
| `LOG_CAT_06` | **Report Generation** | SAR compilation starts, audit chain hashing events, report filings. | INFO to ERROR | 10 Years |
| `LOG_CAT_07` | **System Performance** | Latency stats, CPU/Memory telemetry, queue depth metrics. | DEBUG to WARNING | 90 Days |
| `LOG_CAT_08` | **Security Events** | Signature verification failures, mTLS authentication errors, unauthorized access. | WARNING to CRITICAL | 10 Years |

---

## 2. Structured JSON Log Schema

All structured logs emitted by MACMS components MUST conform to the following JSON schema:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MACMSStructuredLog",
  "type": "object",
  "required": [
    "timestamp",
    "trace_id",
    "agent_id",
    "log_category",
    "severity",
    "message",
    "context"
  ],
  "properties": {
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 UTC timestamp with millisecond precision."
    },
    "trace_id": {
      "type": "string",
      "format": "uuid",
      "description": "Distributed correlation trace ID matching inter-agent message trace_id."
    },
    "agent_id": {
      "type": "string",
      "description": "Unique identifier of agent emitting the log."
    },
    "log_category": {
      "type": "string",
      "enum": [
        "AGENT_LIFECYCLE",
        "DETECTION_EVENTS",
        "COMMUNICATION_EVENTS",
        "ESCALATION_EVENTS",
        "HUMAN_DECISION_EVENTS",
        "REPORT_GENERATION",
        "SYSTEM_PERFORMANCE",
        "SECURITY_EVENTS"
      ]
    },
    "severity": {
      "type": "string",
      "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    },
    "message": {
      "type": "string",
      "description": "Human-readable log description."
    },
    "context": {
      "type": "object",
      "description": "Contextual key-value metrics and event-specific metadata."
    }
  }
}
```

---

## 3. Distributed Trace Correlation

- **Correlation Rule**: Every log statement generated in response to an inter-agent message MUST bind the message's `trace_id` to `context.trace_id`.
- **OpenTelemetry Standard**: Distributed context propagation adheres to W3C Trace Context standards.
