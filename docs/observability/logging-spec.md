---
title: MACMS Observability Logging Specification
date: 2026-08-22
version: 2.0.0
status: Implemented
---

# MACMS Observability Logging Specification

## 1. Mandatory Log Categories

| Category | Severities | Retention |
| --- | --- | ---: |
| `AGENT_LIFECYCLE` | INFO, WARN, ERROR, FATAL | 7 years |
| `DETECTION_EVENTS` | INFO, WARN, ALERT, CRITICAL | 7 years; 10 years for SAR-related events |
| `COMMUNICATION_EVENTS` | DEBUG, INFO, WARN, ERROR | 5 years |
| `ESCALATION_EVENTS` | INFO, WARN, ALERT | 7 years |
| `HUMAN_DECISION_EVENTS` | INFO, ALERT | 10 years |
| `REPORT_GENERATION` | INFO, WARN, ERROR | 7 years or applicable regulation |
| `SYSTEM_PERFORMANCE` | DEBUG, INFO, WARN | 1 year rolling |
| `SECURITY_EVENTS` | WARN, ALERT, CRITICAL | 7 years |

## 2. Structured JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MACMSStructuredLog",
  "type": "object",
  "required": ["timestamp", "trace_id", "agent_id", "log_category", "severity", "message", "context"],
  "properties": {
    "timestamp": {"type": "string", "format": "date-time"},
    "trace_id": {"type": "string", "format": "uuid"},
    "agent_id": {"type": "string"},
    "log_category": {"type": "string", "enum": ["AGENT_LIFECYCLE", "DETECTION_EVENTS", "COMMUNICATION_EVENTS", "ESCALATION_EVENTS", "HUMAN_DECISION_EVENTS", "REPORT_GENERATION", "SYSTEM_PERFORMANCE", "SECURITY_EVENTS"]},
    "severity": {"type": "string", "enum": ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "ALERT", "CRITICAL", "FATAL"]},
    "message": {"type": "string"},
    "context": {"type": "object"},
    "source_file": {"type": "string"},
    "line_number": {"type": "integer"},
    "thread_id": {"type": "string"}
  }
}
```

## 3. Correlation and Environments

All logs created while processing an inter-agent message carry that message’s `trace_id`. Helper methods place event-specific context in the structured `context` object, including evidence, violation type, confidence, escalation identity, reviewer identity, resource values, and operation status. Development permits DEBUG logs. Test defaults to INFO. Production uses WARN for `SYSTEM_PERFORMANCE` logs while retaining regulatory event severities.

The Phase 5 implementation writes structured entries to an in-memory buffer and JSONL file, with the audit chain providing HMAC signatures, nonce values, and tamper-evident linkage. The file writer is intentionally local and in-memory; external aggregation is reserved for a later phase.
