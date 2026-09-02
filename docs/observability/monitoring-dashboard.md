---
title: MACMS Monitoring Dashboard Design
date: 2026-08-22
version: 2.0.0
status: Implemented
---

# MACMS Monitoring Dashboard Design

The dashboard is an API data source with polling clients rather than a Grafana deployment or real-time streaming UI. All panel data is served by the API-key-protected FastAPI dashboard module.

## 1. System Health Panel

**Audience:** Operations Team.

| Metric group | Data shown | Alerting rule |
| --- | --- | --- |
| Agent status | Running, degraded, stopped, heartbeat age at 30-second intervals | Stale heartbeat or non-running status |
| Queue depth | Per-agent and named queue depth | Warning at 80% capacity; critical at 95% |
| Processing latency | P50, P95, P99 per agent and operation | Alert when percentile breaches configured SLA |
| Resources | CPU, memory, and network utilization with capacity projection fields | Capacity planning threshold |
| Errors | Error count/rate and time trend | Statistical-process-control anomaly flag |

Endpoints are `GET /health/system` and `GET /health/agents/{agent_id}`.

## 2. Compliance Effectiveness Panel

**Audience:** Compliance Leadership.

The panel reports detection rates by violation type over daily, weekly, and monthly windows; false-positive rates by agent and violation type with improvement tracking; time-to-detection, time-to-escalation, and time-to-resolution distributions; and regulatory filing accuracy and timeliness by jurisdiction. Detection and human-decision audit events are the source of truth, with empty distributions returned when the current in-memory window has no matching samples.

Endpoints are `/compliance/detection-rate`, `/compliance/false-positive-rate`, `/compliance/time-to-detection`, and `/compliance/filing-accuracy`.

## 3. Operational Intelligence Panel

**Audience:** Senior Management.

The panel reports escalation volume by tier, agent, and violation type; human approval rates, override frequency, and response-time patterns; conflict frequency and root-cause categories; regulatory-update impact from detection through deployment; and cost per automated versus manual detection. Phase 5 returns structured placeholders for dimensions without source events so later persistent integrations can populate them without changing the API contract.

Endpoints are `/operations/escalations`, `/operations/human-patterns`, `/operations/conflicts`, and `/operations/cost-per-detection`.

## 4. Audit Access

`GET /audit/trail` filters verified entries by trace ID, agent ID, and UTC date range. `GET /audit/integrity/{start}/{end}` runs full hash-chain and HMAC verification. Every endpoint requires the Phase 5 API-key skeleton; full identity and role authorization are reserved for Phase 8.
