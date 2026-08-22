"""Structured logging, signed audit trails, and dashboard data for MACMS."""

from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import io
import json
import secrets
from collections import Counter
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import structlog

from src.mcms.core.audit import AuditChain, AuditEntry
from src.mcms.core.exceptions import AuditIntegrityError, DashboardError, ObservabilityError
from src.mcms.core.metrics import MetricsCollector

LOG_CATEGORIES = {
    "AGENT_LIFECYCLE",
    "DETECTION_EVENTS",
    "COMMUNICATION_EVENTS",
    "ESCALATION_EVENTS",
    "HUMAN_DECISION_EVENTS",
    "REPORT_GENERATION",
    "SYSTEM_PERFORMANCE",
    "SECURITY_EVENTS",
}
SEVERITIES = {"DEBUG", "INFO", "WARNING", "WARN", "ERROR", "ALERT", "CRITICAL", "FATAL"}


class ObservabilityService:
    """Provide one in-memory observability interface for all MACMS components."""

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        self.config = dict(config or {})
        audit_seed = str(self.config.get("initial_seed", "MERIDIAN_GENESIS_BLOCK"))
        self.audit_chain = AuditChain(audit_seed)
        metrics_config = self.config.get("metrics", {})
        self.metrics = MetricsCollector(
            metrics_config if isinstance(metrics_config, Mapping) else {}
        )
        self._logs: list[dict[str, Any]] = []
        self._log_path = Path(str(self.config.get("log_path", "data/observability/audit.jsonl")))
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        keys = self.config.get("agent_keys", {})
        self._agent_keys: dict[str, bytes] = (
            {str(agent): str(key).encode("utf-8") for agent, key in keys.items()}
            if isinstance(keys, Mapping)
            else {}
        )
        self._default_key = str(
            self.config.get("default_key", "macms-phase5-development-key")
        ).encode("utf-8")
        self._logger = structlog.get_logger("mcms.observability")

    @property
    def logs(self) -> list[dict[str, Any]]:
        return [dict(log) for log in self._logs]

    def _key_for(self, agent_id: str) -> bytes:
        return self._agent_keys.get(agent_id, self._default_key)

    def _signature(
        self,
        agent_id: str,
        timestamp: str,
        action_type: str,
        payload: Mapping[str, Any],
        nonce: str,
    ) -> str:
        canonical = json.dumps(
            {
                "agent_id": agent_id,
                "timestamp": timestamp,
                "action_type": action_type,
                "payload": payload,
                "nonce": nonce,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return base64.b64encode(
            hmac.new(self._key_for(agent_id), canonical, hashlib.sha256).digest()
        ).decode("ascii")

    def _append_file(self, entry: AuditEntry) -> None:
        with self._log_path.open("a", encoding="utf-8") as handle:
            handle.write(entry.model_dump_json() + "\n")

    def log(
        self,
        category: str,
        severity: str,
        message: str,
        context: dict[str, Any],
        trace_id: str | None = None,
    ) -> AuditEntry:
        """Write one signed structured log and return its audit entry."""
        category = category.upper()
        severity = severity.upper()
        if category not in LOG_CATEGORIES:
            raise ObservabilityError(f"Unsupported log category: {category}")
        if severity not in SEVERITIES:
            raise ObservabilityError(f"Unsupported log severity: {severity}")
        if not message:
            raise ObservabilityError("Structured log message cannot be empty")
        trace = trace_id or str(uuid4())
        agent_id = str(context.get("agent_id", "system"))
        timestamp = datetime.now(UTC).isoformat(timespec="milliseconds")
        nonce = secrets.token_hex(16)
        structured = {
            "timestamp": timestamp,
            "trace_id": trace,
            "agent_id": agent_id,
            "log_category": category,
            "severity": severity,
            "message": message,
            "context": dict(context),
        }
        signature = self._signature(agent_id, timestamp, category, structured, nonce)
        entry = self.audit_chain.append(
            structured,
            agent_id=agent_id,
            timestamp=timestamp,
            trace_id=trace,
            action_type=category,
            action_data=dict(context),
            signature=signature,
            nonce=nonce,
        )
        self._logs.append(structured)
        self._logger.bind(trace_id=trace, agent_id=agent_id, log_category=category).info(
            "macms_event",
            severity=severity,
            message=message,
            context=dict(context),
        )
        self._append_file(entry)
        return entry

    def log_agent_lifecycle(self, agent_id: str, event: str, details: dict[str, Any]) -> AuditEntry:
        return self.log(
            "AGENT_LIFECYCLE",
            str(details.get("severity", "INFO")),
            event,
            {"agent_id": agent_id, **details},
        )

    def log_detection(
        self, agent_id: str, violation_type: str, confidence: float, evidence: list[Any]
    ) -> AuditEntry:
        if not 0.0 <= confidence <= 1.0:
            raise ObservabilityError("Detection confidence must be between 0 and 1")
        return self.log(
            "DETECTION_EVENTS",
            "ALERT",
            f"Detection event: {violation_type}",
            {
                "agent_id": agent_id,
                "violation_type": violation_type,
                "confidence": confidence,
                "evidence": evidence,
            },
        )

    def log_communication(
        self, sender: str, recipient: str, message_type: str, status: str
    ) -> AuditEntry:
        return self.log(
            "COMMUNICATION_EVENTS",
            "INFO",
            f"Communication {message_type}: {status}",
            {
                "agent_id": sender,
                "sender": sender,
                "recipient": recipient,
                "message_type": message_type,
                "status": status,
            },
        )

    def log_escalation(
        self, escalation_id: UUID, event: str, details: dict[str, Any]
    ) -> AuditEntry:
        return self.log(
            "ESCALATION_EVENTS", "ALERT", event, {"escalation_id": str(escalation_id), **details}
        )

    def log_human_decision(
        self, escalation_id: UUID, human_id: str, decision: str, justification: str
    ) -> AuditEntry:
        return self.log(
            "HUMAN_DECISION_EVENTS",
            "INFO" if decision != "override" else "ALERT",
            f"Human decision: {decision}",
            {
                "escalation_id": str(escalation_id),
                "agent_id": human_id,
                "human_id": human_id,
                "decision": decision,
                "justification": justification,
            },
        )

    def log_report_generation(self, report_id: UUID, report_type: str, status: str) -> AuditEntry:
        return self.log(
            "REPORT_GENERATION",
            "INFO",
            f"Report generation: {status}",
            {"report_id": str(report_id), "report_type": report_type, "status": status},
        )

    def log_performance(self, agent_id: str, metric: str, value: float, unit: str) -> AuditEntry:
        self.metrics._record(agent_id, metric, value, {"unit": unit})
        return self.log(
            "SYSTEM_PERFORMANCE",
            "INFO",
            f"Performance metric: {metric}",
            {"agent_id": agent_id, "metric": metric, "value": value, "unit": unit},
        )

    def log_security(self, event_type: str, severity: str, details: dict[str, Any]) -> AuditEntry:
        return self.log("SECURITY_EVENTS", severity, event_type, details)

    def get_metrics(
        self, agent_id: str | None, metric_type: str, window: timedelta
    ) -> list[dict[str, Any]]:
        cutoff = datetime.now(UTC) - window
        return [
            {
                "agent_id": sample.agent_id,
                "metric": sample.metric,
                "value": sample.value,
                "timestamp": sample.timestamp.isoformat(),
                "context": dict(sample.context),
            }
            for sample in self.metrics.samples
            if (agent_id is None or sample.agent_id == agent_id)
            and (sample.metric == metric_type or sample.metric.startswith(f"{metric_type}:"))
            and sample.timestamp >= cutoff
        ]

    def _check_signatures(self) -> None:
        for entry in self.audit_chain.entries:
            if entry.signature is None or entry.nonce is None or entry.action_type is None:
                continue
            payload = entry.data
            expected = self._signature(
                entry.agent_id, entry.timestamp, entry.action_type, payload, entry.nonce
            )
            if not hmac.compare_digest(expected, entry.signature):
                raise AuditIntegrityError(
                    f"Signature verification failed at audit entry {entry.index}",
                    entry_index=entry.index,
                )

    def get_audit_trail(
        self,
        trace_id: str | None,
        agent_id: str | None,
        start: datetime,
        end: datetime,
    ) -> list[AuditEntry]:
        """Verify the complete chain before returning a filtered audit view."""
        start = start.astimezone(UTC) if start.tzinfo is not None else start.replace(tzinfo=UTC)
        end = end.astimezone(UTC) if end.tzinfo is not None else end.replace(tzinfo=UTC)
        self.verify_audit_integrity(start, end)
        return [
            entry
            for entry in self.audit_chain.entries
            if start <= datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00")) <= end
            and (
                trace_id is None
                or entry.trace_id == trace_id
                or entry.data.get("trace_id") == trace_id
            )
            and (agent_id is None or entry.agent_id == agent_id)
        ]

    def verify_audit_integrity(self, start: datetime, end: datetime) -> bool:
        """Verify hash links and HMAC signatures for the entire chain."""
        if start > end:
            raise ObservabilityError("Integrity verification start must not be after end")
        self.audit_chain.verify_chain()
        self._check_signatures()
        return True

    def export_audit(self, start: datetime, end: datetime, format: str) -> str:
        entries = self.get_audit_trail(None, None, start, end)
        normalized = format.lower()
        if normalized == "jsonl":
            return "\n".join(
                json.dumps(entry.model_dump(mode="json"), sort_keys=True) for entry in entries
            )
        if normalized == "csv":
            output = io.StringIO()
            fields = [
                "timestamp",
                "trace_id",
                "agent_id",
                "action_type",
                "action_data",
                "previous_hash",
                "current_hash",
                "signature",
                "nonce",
            ]
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            for entry in entries:
                writer.writerow(
                    {
                        "timestamp": entry.timestamp,
                        "trace_id": entry.trace_id or "",
                        "agent_id": entry.agent_id,
                        "action_type": entry.action_type or "",
                        "action_data": json.dumps(entry.action_data or entry.data, sort_keys=True),
                        "previous_hash": entry.previous_hash,
                        "current_hash": entry.current_hash,
                        "signature": entry.signature or "",
                        "nonce": entry.nonce or "",
                    }
                )
            return output.getvalue()
        raise ObservabilityError("Audit export format must be JSONL or CSV")

    @staticmethod
    def _timeframe_delta(timeframe: str) -> timedelta:
        values = {
            "1h": timedelta(hours=1),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
            "90d": timedelta(days=90),
        }
        return values.get(timeframe.lower(), timedelta(days=1))

    def get_dashboard_data(self, panel: str, timeframe: str) -> dict[str, Any]:
        """Return structured data for one of the three Phase 5 stakeholder panels."""
        normalized = panel.lower().replace(" ", "_")
        window = self._timeframe_delta(timeframe)
        since = datetime.now(UTC) - window
        entries = [
            entry
            for entry in self.audit_chain.entries
            if datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00")) >= since
        ]
        if normalized in {"system_health", "health"}:
            status: dict[str, str] = {}
            queues: dict[str, float] = {}
            errors: Counter[str] = Counter()
            for entry in entries:
                if entry.action_type == "AGENT_LIFECYCLE":
                    status[entry.agent_id] = str(
                        entry.data.get("context", {}).get(
                            "status", entry.data.get("message", "unknown")
                        )
                    ).lower()
                if entry.action_type == "SYSTEM_PERFORMANCE":
                    context = entry.data.get("context", {})
                    if context.get("metric", "").startswith("queue_depth"):
                        queues[entry.agent_id] = float(context.get("value", 0.0))
                if entry.action_type == "SECURITY_EVENTS" or entry.data.get("severity") in {
                    "ERROR",
                    "CRITICAL",
                    "FATAL",
                }:
                    errors[entry.agent_id] += 1
            agents = sorted(set(status) | set(queues) | set(errors))
            return {
                "panel": "system_health",
                "timeframe": timeframe,
                "agents": [
                    {
                        "agent_id": agent,
                        "status": status.get(agent, "unknown"),
                        "queue_depth": queues.get(agent, 0.0),
                        "error_count": errors.get(agent, 0),
                    }
                    for agent in agents
                ],
                "queue_thresholds": {"warning": 0.80, "critical": 0.95},
                "heartbeat_interval_seconds": 30,
            }
        if normalized in {"compliance_effectiveness", "compliance"}:
            detections: Counter[str] = Counter()
            false_positives: Counter[str] = Counter()
            for entry in entries:
                context = entry.data.get("context", {})
                violation = str(context.get("violation_type", "unknown"))
                if entry.action_type == "DETECTION_EVENTS":
                    detections[violation] += 1
                if (
                    entry.action_type == "HUMAN_DECISION_EVENTS"
                    and context.get("decision") == "reject"
                ):
                    false_positives[violation] += 1
            return {
                "panel": "compliance_effectiveness",
                "timeframe": timeframe,
                "detection_rate_by_violation": dict(detections),
                "false_positive_rate_by_violation": {
                    key: false_positives[key] / detections[key] if detections[key] else 0.0
                    for key in detections
                },
                "time_to_detection": [],
                "time_to_escalation": [],
                "time_to_resolution": [],
                "filing_accuracy": {},
            }
        if normalized in {"operational_intelligence", "operations"}:
            tiers: Counter[str] = Counter()
            decisions: Counter[str] = Counter()
            conflicts: Counter[str] = Counter()
            for entry in entries:
                context = entry.data.get("context", {})
                if entry.action_type == "ESCALATION_EVENTS":
                    tiers[str(context.get("tier", "unknown"))] += 1
                if entry.action_type == "HUMAN_DECISION_EVENTS":
                    decisions[str(context.get("decision", "unknown"))] += 1
                conflict = context.get("conflict_type")
                if conflict:
                    conflicts[str(conflict)] += 1
            return {
                "panel": "operational_intelligence",
                "timeframe": timeframe,
                "escalation_volume_by_tier": dict(tiers),
                "human_decision_patterns": {"decision_counts": dict(decisions)},
                "conflict_frequency": dict(conflicts),
                "regulatory_update_impact": [],
                "cost_per_detection": {},
            }
        raise DashboardError(f"Unknown dashboard panel: {panel}")
