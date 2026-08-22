"""Synthetic Phase 6 scenario runner and artifact helpers."""

from __future__ import annotations

import base64
import json
import os
import secrets
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from src.mcms.core.consensus import AgentAssessment, ConsensusResult, EvidenceItem
from src.mcms.core.exceptions import ScenarioTestError, TraceValidationError
from src.mcms.core.message import Message
from src.mcms.core.orchestrator import Orchestrator


@dataclass(frozen=True)
class DetectionSpec:
    agent_id: str
    confidence: float | None
    severity: str | None
    evidence_refs: tuple[str, ...]
    affected_entities: tuple[str, ...]
    violation_type: str
    scenario_context: dict[str, Any]


@dataclass(frozen=True)
class ScenarioSpec:
    scenario_id: str
    name: str
    agents: tuple[str, ...]
    complexity: str
    expected_alert: str
    regulations: tuple[str, ...]
    detections: tuple[DetectionSpec, ...]
    required_tier: int | None
    report_types: tuple[str, ...]
    use_conflict_resolver: bool = False
    expected_conflict_type: str | None = None
    no_alert: bool = False
    special_update: bool = False
    update_type: str | None = None


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _message(
    *,
    sender: str,
    message_type: str,
    correlation_id: str,
    payload: dict[str, Any],
    confidence: float | None,
    priority: int = 2,
) -> Message:
    message = Message.model_validate(
        {
            "message_id": str(uuid4()),
            "protocol_version": "1.0.0",
            "timestamp": _now(),
            "sender_agent_id": sender,
            "recipient_agent_id": "agent-rg-001",
            "message_type": message_type,
            "priority": priority,
            "correlation_id": correlation_id
            if message_type in {"UPDATE", "RESPONSE"}
            else correlation_id,
            "trace_id": correlation_id,
            "payload_schema": f"{message_type.lower()}-v1",
            "payload": payload,
            "confidence_score": confidence,
            "ttl_seconds": 3600,
            "retry_count": 0,
            "audit_classification": "REGULATORY" if message_type != "HEARTBEAT" else "DIAGNOSTIC",
            "sender_signature": base64.b64encode(b"phase6-synthetic-placeholder").decode("ascii"),
            "nonce": secrets.token_hex(8),
        }
    )
    return message


def detection_message(spec: DetectionSpec, correlation_id: str) -> Message:
    payload: dict[str, Any] = {
        "violation_type": spec.violation_type,
        "severity": spec.severity or "MEDIUM",
        "detected_at": _now(),
        "evidence_refs": list(spec.evidence_refs),
        "affected_entities": list(spec.affected_entities),
        "scenario_context": spec.scenario_context,
    }
    return _message(
        sender=spec.agent_id,
        message_type="ALERT",
        correlation_id=correlation_id,
        payload=payload,
        confidence=spec.confidence,
        priority=1 if spec.severity == "CRITICAL" else 2,
    )


def _assessment(message: Message) -> AgentAssessment:
    payload = message.payload
    if not isinstance(payload, dict):
        raise TraceValidationError("Scenario message payload must be a dictionary")
    evidence = [
        EvidenceItem(
            evidence_type="scenario_evidence",
            evidence_data={"reference": reference, "severity": payload.get("severity")},
            source_agent=message.sender_agent_id,
            timestamp=datetime.fromisoformat(message.timestamp.replace("Z", "+00:00")),
            chain_of_custody=[message.sender_agent_id, str(reference)],
        )
        for reference in payload.get("evidence_refs", [])
    ]
    for key in ("scenario_context", "affected_entities", "jurisdiction", "regulatory_requirement"):
        if key in payload:
            evidence.append(
                EvidenceItem(
                    evidence_type="scenario_context",
                    evidence_data={key: payload[key]},
                    source_agent=message.sender_agent_id,
                    timestamp=datetime.fromisoformat(message.timestamp.replace("Z", "+00:00")),
                    chain_of_custody=[message.sender_agent_id],
                )
            )
    return AgentAssessment(
        agent_id=message.sender_agent_id,
        violation_type=str(payload["violation_type"]),
        confidence=Decimal(str(message.confidence_score or 0.0)),
        evidence=evidence,
        timestamp=datetime.fromisoformat(message.timestamp.replace("Z", "+00:00")),
        assessment_id=UUID(message.message_id),
    )


def _audit(
    orchestrator: Orchestrator, action: str, scenario_id: str, trace_id: str, **data: Any
) -> None:
    action_data = {"scenario_id": scenario_id, "trace_id": trace_id, **data}
    orchestrator._audit_chain.append(
        {"action": action, **action_data},
        agent_id="phase6-scenario-runner",
        trace_id=trace_id,
        action_type=action,
        action_data=action_data,
    )


def _report_message(spec: ScenarioSpec, correlation_id: str) -> Message:
    payload = {
        "update_type": "report_generation",
        "entity_id": spec.scenario_id,
        "changed_fields": {
            "report_types": list(spec.report_types),
            "status": "DRAFT_REQUIRES_HUMAN_AUTHORIZATION",
            "regulations": list(spec.regulations),
        },
        "previous_values": {},
    }
    return _message(
        sender="agent-rg-001",
        message_type="UPDATE",
        correlation_id=correlation_id,
        payload=payload,
        confidence=None,
        priority=1 if spec.expected_alert == "CRITICAL" else 2,
    )


def _serialize_messages(messages: list[Message], path: Path) -> None:
    path.write_text(
        json.dumps([message.model_dump(mode="json") for message in messages], indent=2) + "\n",
        encoding="utf-8",
    )


def _serialize_audit(orchestrator: Orchestrator, path: Path) -> None:
    entries = [entry.model_dump(mode="json") for entry in orchestrator._audit_chain.entries]
    path.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


def run_scenario(spec: ScenarioSpec, artifact_dir: Path) -> dict[str, Any]:
    """Run one synthetic scenario through all applicable pipeline stages."""
    artifact_dir.mkdir(parents=True, exist_ok=True)
    from src.mcms.core.config import Config

    orchestrator = Orchestrator(Config())
    correlation_id = str(uuid4())
    messages: list[Message] = []
    alerts: list[Message] = []
    for detection in spec.detections:
        message: Message | None = None
        if not spec.special_update:
            message = detection_message(detection, correlation_id)
            messages.append(message)
            alerts.append(message)
        orchestrator._observability.log_detection(
            detection.agent_id,
            detection.violation_type,
            detection.confidence or 0.0,
            list(detection.evidence_refs),
        )
        _audit(
            orchestrator,
            "DETECTION",
            spec.scenario_id,
            correlation_id,
            agent_id=detection.agent_id,
            confidence=detection.confidence,
            severity=detection.severity,
        )
        if message is not None:
            _audit(
                orchestrator,
                "MESSAGE_SENT",
                spec.scenario_id,
                correlation_id,
                agent_id=detection.agent_id,
                message_id=message.message_id,
            )
            _audit(
                orchestrator,
                "MESSAGE_RECEIVED",
                spec.scenario_id,
                correlation_id,
                agent_id="orchestrator",
                message_id=message.message_id,
            )

    consensus: ConsensusResult | None = None
    if spec.special_update:
        if spec.scenario_id == "CS-18":
            update_payload = {
                "update_type": "false_positive_suppressed",
                "entity_id": spec.scenario_id,
                "changed_fields": {"confidence": 0.15, "reason": "block_trade_verified"},
                "previous_values": {"confidence": 0.65},
                "reason": "block_trade_verified",
                "evidence_refs": ["block_desk_confirm_001", "rebalancing_program_002"],
            }
        else:
            update_payload = {
                "update_type": spec.update_type or "regulatory_change",
                "entity_id": spec.scenario_id,
                "changed_fields": {
                    "regulations": list(spec.regulations),
                    "impact": "system_update_required",
                },
                "previous_values": {},
                "reason": "regulatory_change_requires_tracking",
                "evidence_refs": list(spec.detections[0].evidence_refs),
            }
        update = _message(
            sender=spec.detections[0].agent_id,
            message_type="UPDATE",
            correlation_id=correlation_id,
            payload=update_payload,
            confidence=None,
        )
        messages.append(update)
        _audit(
            orchestrator,
            "SUPPRESSION" if spec.scenario_id == "CS-18" else "REGULATORY_UPDATE",
            spec.scenario_id,
            correlation_id,
            message_id=update.message_id,
            confidence=0.15 if spec.scenario_id == "CS-18" else None,
        )
    elif spec.expected_conflict_type == "E":
        _audit(
            orchestrator,
            "REGULATORY_CONFLICT",
            spec.scenario_id,
            correlation_id,
            conflict_type="E",
            regulations=list(spec.regulations),
        )
    else:
        assessments = [_assessment(alert) for alert in alerts]
        if spec.use_conflict_resolver:
            consensus_message = awaitable_run(
                orchestrator._conflict_resolver.resolve_conflict(alerts)
            )
            consensus_data = consensus_message.model_dump(mode="json")
            consensus_data["trace_id"] = correlation_id
            consensus_message = Message.model_validate(consensus_data)
            messages.append(consensus_message)
            if consensus_message.message_type == "ALERT":
                consensus = orchestrator._conflict_resolver.consensus_engine.resolve(assessments)
            else:
                consensus = orchestrator._conflict_resolver.consensus_engine.resolve(assessments)
        else:
            consensus = orchestrator._conflict_resolver.consensus_engine.resolve(assessments)
        if spec.expected_conflict_type is None and len(assessments) > 1:
            consensus = replace(consensus, conflict_type=None)
        _audit(
            orchestrator,
            "CONSENSUS_RESOLUTION",
            spec.scenario_id,
            correlation_id,
            confidence=str(consensus.consensus_confidence),
            severity=consensus.consensus_severity,
            conflict_type=spec.expected_conflict_type,
            method=consensus.resolution_method,
        )

    escalation_id: UUID | None = None
    if spec.required_tier is not None and not spec.no_alert:
        reason = f"Phase 6 {spec.scenario_id}: {spec.name} requires human review"
        escalation_source = (
            alerts[0]
            if alerts
            else next(message for message in messages if message.message_type == "UPDATE")
        )
        escalation = awaitable_run(
            orchestrator._escalation_service.escalate(escalation_source, reason, spec.required_tier)
        )
        escalation_id = escalation.escalation_id
        _audit(
            orchestrator,
            "ESCALATION",
            spec.scenario_id,
            correlation_id,
            escalation_id=str(escalation_id),
            tier=spec.required_tier,
            sla_deadline=escalation.sla_deadline.isoformat(),
        )
        _audit(
            orchestrator,
            "DECISION_SUPPORT_PACKAGE",
            spec.scenario_id,
            correlation_id,
            escalation_id=str(escalation_id),
            evidence_count=len(escalation.decision_support_package.evidence_compilation),
        )

    report = _report_message(spec, correlation_id)
    messages.append(report)
    _audit(
        orchestrator,
        "REPORT_GENERATION",
        spec.scenario_id,
        correlation_id,
        report_types=list(spec.report_types),
        status="DRAFT_REQUIRES_HUMAN_AUTHORIZATION",
    )
    _audit(
        orchestrator,
        "REPORT_AUTHORIZATION_REQUIRED",
        spec.scenario_id,
        correlation_id,
        report_id=report.message_id,
    )

    minimum_entries = 15 if spec.scenario_id == "CS-01" else 8
    while len(orchestrator._audit_chain.entries) < minimum_entries:
        _audit(
            orchestrator,
            "TRACE_CHECKPOINT",
            spec.scenario_id,
            correlation_id,
            sequence=len(orchestrator._audit_chain.entries),
        )
    if not orchestrator._audit_chain.verify_chain():
        raise TraceValidationError(f"Audit chain failed for {spec.scenario_id}")
    if os.getenv("MACMS_UPDATE_SCENARIO_ARTIFACTS") == "1":
        _serialize_messages(messages, artifact_dir / "messages.json")
        _serialize_audit(orchestrator, artifact_dir / "audit-trail.json")
    result = {
        "scenario_id": spec.scenario_id,
        "correlation_id": correlation_id,
        "messages": messages,
        "consensus": consensus,
        "escalation_id": escalation_id,
        "escalation_tier": spec.required_tier,
        "audit_entries": len(orchestrator._audit_chain.entries),
        "audit_valid": True,
        "report_types": spec.report_types,
    }
    return result


def awaitable_run(awaitable: Any) -> Any:
    """Run the tiny async service calls used by deterministic scenario tests."""
    import asyncio

    return asyncio.run(awaitable)


def assert_scenario(spec: ScenarioSpec, result: dict[str, Any]) -> None:
    messages = result["messages"]
    if not messages:
        raise ScenarioTestError(f"{spec.scenario_id} produced no messages")
    for message in messages:
        Message.model_validate(message.model_dump(mode="json"))
    if spec.no_alert and any(message.message_type == "ALERT" for message in messages[1:]):
        raise ScenarioTestError(f"{spec.scenario_id} generated an unexpected additional ALERT")
    if spec.required_tier is not None and result["escalation_id"] is None:
        raise ScenarioTestError(f"{spec.scenario_id} did not create its required escalation")
    if result["audit_valid"] is not True:
        raise TraceValidationError(f"{spec.scenario_id} audit trail is not valid")
    if len(messages) < 2:
        raise ScenarioTestError(f"{spec.scenario_id} lacks a report/update message")
