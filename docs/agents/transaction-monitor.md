---
title: Transaction Monitor Agent Specification
agent_id: agent-tm-001
version: 2.0.0
date: 2026-08-17
status: Phase 2 Complete
---

# Transaction Monitor Agent (agent-tm-001)

## 1. Overview

The Transaction Monitor Agent is responsible for real-time surveillance of all trading activities across Meridian Global Bank's operations. It identifies statistical anomalies, monitors regulatory thresholds, performs temporal and counterparty analysis, and conducts cross-market surveillance to detect coordinated manipulation patterns.

---

## 2. Capability Table

| Capability | Description | Scope | Input Data | Output Data | SLA |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Pattern Detection** | Identify statistical anomalies in transaction volume, price, timing, counterparty concentration | All asset classes: equities, fixed income, derivatives, FX, commodities | Trade execution data, market data feeds | Alert messages with anomaly scores | P50 < 100ms, P99 < 500ms |
| **Threshold Monitoring** | Monitor regulatory thresholds including position limits, large trader reporting, suspicious activity triggers | Jurisdiction-specific thresholds for SEC, FCA, MAS, HKMA | Position data, regulatory threshold configs | Threshold breach alerts | Real-time |
| **Temporal Analysis** | Detect patterns across multiple time windows and correlate with known market events | Rolling windows: 1h, 4h, 1d, 5d, 20d, 60d | Historical transaction data, market event calendar | Temporal anomaly reports | Batch: 15 min |
| **Counterparty Analysis** | Identify unusual counterparty concentrations, related-party transactions, circular trading patterns | Internal and external counterparty databases | Counterparty reference data, transaction history | Counterparty risk alerts | P95 < 2s |
| **Cross-Market Surveillance** | Detect correlated patterns across multiple markets or instruments indicating coordinated manipulation | Multi-venue, multi-instrument correlation | Multi-venue trade data | Cross-market correlation alerts | P95 < 5s |

---

## 3. Constraints

- **No Raw Communication Access**: Cannot access raw customer communications; all trade-communication correlation requests must be routed through the Communication Scanner Agent via the Orchestrator.
- **Calibrated Confidence Scores**: Detection confidence scores must be calibrated against historical false positive rates; uncalibrated scores must not trigger alerts above P3-MEDIUM.
- **Computational Resource Boundaries**: Operates within defined computational resource limits (32 vCPU, 128GB RAM); resource-intensive deep learning models require explicit resource allocation approval.
- **No Autonomous Trading Halts**: Cannot issue trading halts or circuit breakers autonomously; all halt recommendations must be escalated through the Orchestrator with TIER_2 or TIER_3 human review.
- **Sub-Second Latency**: Real-time alert generation must maintain sub-second latency for P1-CRITICAL and P2-HIGH priority alerts.
- **UPI Monitoring Scale**: Process up to 10+ billion monthly (350M+ daily) UPI transactions with sub-second anomaly detection across P2P fraud and merchant payment anomalies.
- **SEBI Connected Person Mapping**: Perform up to 6th-degree relationship analysis (family, business associates, subsidiaries, common directors) using graph databases (Neo4j / Amazon Neptune).

---

## 4. Input Interfaces

| Protocol | Source | Data Format | Frequency |
| :--- | :--- | :--- | :--- |
| FIX Protocol (4.2/4.4/5.0) | Trading platforms | FIX messages (NewOrderSingle, ExecutionReport, MarketDataSnapshotFullRefresh) | Real-time streaming |
| Market Data (ITCH/OUCH) | Exchange feeds | Binary market data (Level 2 order book, trades, imbalances) | Real-time streaming |
| Position Data API | Risk management systems | JSON/REST (position snapshots, P&L, exposure) | Periodic (1min intervals) |
| Regulatory Threshold Config | Configuration service | YAML/JSON (threshold values, jurisdiction mappings) | On-change |

---

## 5. Output Interfaces

| Message Type | Destination | Content | Routing |
| :--- | :--- | :--- | :--- |
| ALERT | Orchestrator | Anomaly detection results with violation_type, severity, confidence_score, evidence_refs | Via orchestrator dispatch |
| UPDATE | Report Generator (agent-rg-001) | Periodic summary statistics, detection metrics, threshold status | Via orchestrator dispatch |
| QUERY | Communication Scanner (agent-cs-001) | Trade-communication correlation requests with transaction IDs, timestamps | Via orchestrator dispatch |
| HEARTBEAT | Orchestrator | Agent health status, queue depth, processing metrics | Direct to heartbeat topic |

---

## 6. Resource Requirements

| Resource | Specification | Notes |
| :--- | :--- | :--- |
| vCPU | 32 | High-frequency computation for real-time pattern detection |
| Memory | 128 GB RAM | In-memory time-series windows and statistical models |
| Storage | NVMe SSD | Hot data store for rolling windows (1h–60d) |
| GPU | Optional | Deep learning models for advanced anomaly detection |
| Network | 10 Gbps | Low-latency FIX and market data ingestion |

---

## 7. Health Check Endpoint

```json
{
  "agent_id": "agent-tm-001",
  "status": "HEALTHY | DEGRADED | UNHEALTHY",
  "uptime_seconds": 86400.0,
  "queue_depth": 12,
  "processed_count": 1542890,
  "last_processed_timestamp": "2026-08-17T08:00:00+00:00",
  "capabilities_status": {
    "pattern_detection": "ACTIVE",
    "threshold_monitoring": "ACTIVE",
    "temporal_analysis": "ACTIVE",
    "counterparty_analysis": "ACTIVE",
    "cross_market_surveillance": "ACTIVE"
  },
  "resource_utilization": {
    "cpu_percent": 45.2,
    "memory_percent": 62.1,
    "disk_io_percent": 18.5
  }
}
```
