"""Conflict detection and message-level orchestration for Phase 3."""

from __future__ import annotations

import base64
import secrets
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID, uuid4

from src.mcms.core.consensus import AgentAssessment, ConsensusEngine, ConsensusResult, EvidenceItem
from src.mcms.core.exceptions import ConflictDetectionError
from src.mcms.core.message import Message


def _payload(message: Message) -> dict[str, Any]:
    return cast(dict[str, Any], message.payload)


if TYPE_CHECKING:
    from src.mcms.core.orchestrator import Orchestrator


class ConflictResolver:
    """Convert correlated ALERT messages into consensus or escalation messages."""

    def __init__(self, consensus_engine: ConsensusEngine, orchestrator: Orchestrator) -> None:
        self.consensus_engine = consensus_engine
        self.orchestrator = orchestrator
        config = getattr(orchestrator, "_config", None)
        configured_window = 300
        if config is not None:
            getter = getattr(config, "get", None)
            if callable(getter):
                configured_window = getter("orchestrator.conflict_detection_window_seconds", 300)
        try:
            self.conflict_detection_window_seconds = max(1, int(configured_window))
        except (TypeError, ValueError):
            self.conflict_detection_window_seconds = 300

    @staticmethod
    def _correlation_key(message: Message) -> str:
        return message.correlation_id or message.trace_id

    @staticmethod
    def _message_timestamp(message: Message) -> datetime:
        value = message.timestamp
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)

    @staticmethod
    def _payload_severity(message: Message) -> str:
        return str(_payload(message).get("severity", "")).upper()

    def _within_time_window(self, messages: list[Message]) -> bool:
        if len(messages) < 2:
            return True
        timestamps = [self._message_timestamp(message) for message in messages]
        return (
            max(timestamps) - min(timestamps)
        ).total_seconds() <= self.conflict_detection_window_seconds

    def detect_conflict(self, messages: list[Message]) -> bool:
        """Return true when correlated ALERTs disagree within the configured time window."""
        if len(messages) < 2 or any(message.message_type != "ALERT" for message in messages):
            return False
        if len({self._correlation_key(message) for message in messages}) != 1:
            return False
        if not self._within_time_window(messages):
            return False
        violation_types = {str(_payload(message).get("violation_type", "")) for message in messages}
        confidences = {message.confidence_score for message in messages}
        severities = {self._payload_severity(message) for message in messages}
        timestamps = [self._message_timestamp(message) for message in messages]
        temporal_disagreement = (max(timestamps) - min(timestamps)).total_seconds() > 60
        context_shapes = {
            (
                _payload(message).get("exculpatory", False),
                _payload(message).get("jurisdiction"),
                _payload(message).get("regulatory_requirement"),
                _payload(message).get("attributed_entity"),
                tuple(sorted(str(item) for item in _payload(message).get("affected_entities", []))),
            )
            for message in messages
        }
        return (
            len(violation_types) > 1
            or len(severities) > 1
            or len(confidences) > 1
            or len(context_shapes) > 1
            or temporal_disagreement
        )

    def classify_conflict(self, messages: list[Message]) -> str:
        """Classify correlated messages with the engine's A–G taxonomy."""
        if len(messages) < 2 or any(message.message_type != "ALERT" for message in messages):
            raise ConflictDetectionError("At least two ALERT messages are required")
        if len({self._correlation_key(message) for message in messages}) != 1:
            raise ConflictDetectionError("Messages must share a correlation_id or trace_id")
        if not self._within_time_window(messages):
            raise ConflictDetectionError("Messages fall outside the conflict detection time window")
        return self.consensus_engine.classify_conflict(
            [self.build_assessment(message) for message in messages]
        )

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)

    def build_assessment(self, message: Message) -> AgentAssessment:
        """Convert a validated ALERT message to the standard assessment contract."""
        if message.message_type != "ALERT":
            raise ConflictDetectionError("Only ALERT messages can become agent assessments")
        evidence: list[EvidenceItem] = []
        evidence_refs = _payload(message).get("evidence_refs", [])
        for reference in evidence_refs:
            evidence.append(
                EvidenceItem(
                    evidence_type="reference",
                    evidence_data={
                        "reference": reference,
                        "severity": _payload(message).get("severity"),
                    },
                    source_agent=message.sender_agent_id,
                    timestamp=self._parse_timestamp(
                        str(_payload(message).get("detected_at", message.timestamp))
                    ),
                    chain_of_custody=[message.sender_agent_id, str(reference)],
                )
            )
        for key in (
            "exculpatory",
            "jurisdiction",
            "regulatory_requirement",
            "attributed_entity",
            "affected_entities",
        ):
            if key in _payload(message):
                evidence.append(
                    EvidenceItem(
                        evidence_type="context",
                        evidence_data={key: _payload(message)[key]},
                        source_agent=message.sender_agent_id,
                        timestamp=self._message_timestamp(message),
                        chain_of_custody=[message.sender_agent_id],
                    )
                )
        return AgentAssessment(
            agent_id=message.sender_agent_id,
            violation_type=str(_payload(message)["violation_type"]),
            confidence=Decimal(str(message.confidence_score))
            if message.confidence_score is not None
            else Decimal("0"),
            evidence=evidence,
            timestamp=self._message_timestamp(message),
            assessment_id=UUID(message.message_id),
        )

    @staticmethod
    def _result_payload(result: ConsensusResult) -> dict[str, Any]:
        return {
            "consensus_confidence": float(result.consensus_confidence),
            "consensus_severity": result.consensus_severity,
            "conflict_type": result.conflict_type,
            "contributing_agents": result.contributing_agents,
            "dissenting_agents": result.dissenting_agents,
            "resolution_method": result.resolution_method,
            "escalation_required": result.escalation_required,
            "escalation_reason": result.escalation_reason,
            "audit_trail_ref": str(result.audit_trail_ref),
        }

    def build_resolution_message(self, result: ConsensusResult) -> Message:
        """Convert a consensus result into a valid ALERT or ESCALATION message."""
        now = datetime.now(UTC).isoformat()
        message_id = str(uuid4())
        trace_id = str(result.audit_trail_ref)
        signature = base64.b64encode(b"conflict-resolver-placeholder").decode("ascii")
        if result.escalation_required:
            payload: dict[str, Any] = {
                "escalation_reason": result.escalation_reason or "Consensus requires human review",
                "recommended_tier": "TIER_3" if result.conflict_type == "E" else "TIER_2",
                "decision_support_package_ref": str(result.audit_trail_ref),
                "human_assignee_role": "legal-counsel"
                if result.conflict_type == "E"
                else "compliance-analyst",
                "conflict_type": result.conflict_type,
            }
            message_type = "ESCALATION"
            confidence = float(result.consensus_confidence)
            priority = 1 if result.conflict_type == "E" else 2
            audit_classification = "REGULATORY"
            payload_schema = "escalation-v1"
        else:
            payload = {
                "violation_type": "consensus-resolved",
                "severity": result.consensus_severity
                if result.consensus_severity != "NO_ALERT"
                else "LOW",
                "detected_at": now,
                "evidence_refs": [str(result.audit_trail_ref)],
                "affected_entities": result.contributing_agents,
                "consensus_result": self._result_payload(result),
            }
            message_type = "ALERT"
            confidence = float(result.consensus_confidence)
            priority = 2 if result.consensus_severity in {"HIGH", "CRITICAL"} else 3
            audit_classification = "REGULATORY"
            payload_schema = "alert-v1"
        return Message.model_validate(
            {
                "message_id": message_id,
                "protocol_version": "1.0.0",
                "timestamp": now,
                "sender_agent_id": "agent-rg-001",
                "recipient_agent_id": "agent-rg-001",
                "message_type": message_type,
                "priority": priority,
                "trace_id": trace_id,
                "payload_schema": payload_schema,
                "payload": payload,
                "confidence_score": confidence,
                "ttl_seconds": 300,
                "retry_count": 0,
                "audit_classification": audit_classification,
                "sender_signature": signature,
                "nonce": secrets.token_hex(8),
            }
        )

    async def _audit(self, action: str, messages: list[Message], result: ConsensusResult) -> None:
        audit_chain = getattr(self.orchestrator, "_audit_chain", None)
        event_data = {
            "action": action,
            "message_ids": sorted(message.message_id for message in messages),
            "conflict_type": result.conflict_type,
            "resolution_method": result.resolution_method,
            "consensus_confidence": str(result.consensus_confidence),
            "escalation_required": result.escalation_required,
            "audit_trail_ref": str(result.audit_trail_ref),
        }
        if audit_chain is not None:
            audit_chain.append(event_data, agent_id="conflict-resolver")
        observability = getattr(self.orchestrator, "_observability", None)
        if observability is not None:
            observability.log(
                "ESCALATION_EVENTS" if result.escalation_required else "DETECTION_EVENTS",
                "ALERT" if result.escalation_required else "INFO",
                action,
                {"agent_id": "conflict-resolver", **event_data},
                trace_id=str(result.audit_trail_ref),
            )

    async def resolve_conflict(self, alert_messages: list[Message]) -> Message:
        """Resolve correlated alerts, logging every decision to the orchestrator audit chain."""
        if not alert_messages or any(message.message_type != "ALERT" for message in alert_messages):
            raise ConflictDetectionError("Conflict resolution requires one or more ALERT messages")
        if len(alert_messages) > 1 and not self._within_time_window(alert_messages):
            raise ConflictDetectionError("Alerts are outside the conflict detection window")
        assessments = [self.build_assessment(message) for message in alert_messages]
        result = self.consensus_engine.resolve(assessments)
        if len(alert_messages) > 1 and not self.detect_conflict(alert_messages):
            result = ConsensusResult(
                consensus_confidence=result.consensus_confidence,
                consensus_severity=result.consensus_severity,
                conflict_type=None,
                contributing_agents=result.contributing_agents,
                dissenting_agents=[],
                resolution_method=result.resolution_method,
                escalation_required=result.escalation_required,
                escalation_reason=result.escalation_reason,
                audit_trail_ref=result.audit_trail_ref,
            )
        await self._audit("CONFLICT_RESOLUTION", alert_messages, result)
        return self.build_resolution_message(result)

    async def handle_false_positive(self, messages: list[Message]) -> Message:
        """Suppress Type D conflicts when exculpatory evidence is present."""
        assessments = [self.build_assessment(message) for message in messages]
        result = self.consensus_engine.resolve(assessments)
        if result.conflict_type != "D":
            raise ConflictDetectionError(
                "Messages do not represent a Type D false-positive conflict"
            )
        await self._audit("FALSE_POSITIVE_SUPPRESSED", messages, result)
        return self.build_resolution_message(result)

    async def handle_regulatory_conflict(self, messages: list[Message]) -> Message:
        """Escalate Type E conflicts immediately to legal counsel."""
        assessments = [self.build_assessment(message) for message in messages]
        result = self.consensus_engine.resolve(assessments)
        if result.conflict_type != "E":
            raise ConflictDetectionError("Messages do not represent a Type E regulatory conflict")
        await self._audit("REGULATORY_CONFLICT_ESCALATED", messages, result)
        return self.build_resolution_message(result)
