"""Human-in-the-loop escalation service for the MACMS Phase 4 framework."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, Literal, cast
from uuid import UUID, uuid4

from src.mcms.core.audit import AuditEntry
from src.mcms.core.consensus import EvidenceItem
from src.mcms.core.exceptions import (
    EscalationError,
    OverrideDeniedError,
    SlaViolationError,
)
from src.mcms.core.human_assignment import HumanAssignmentEngine
from src.mcms.core.message import Message

if TYPE_CHECKING:
    from src.mcms.core.feedback import FeedbackLoop
    from src.mcms.core.orchestrator import Orchestrator


def _payload(message: Message) -> dict[str, Any]:
    return cast(dict[str, Any], message.payload)


DecisionType = Literal["approve", "reject", "override", "request_more_info"]
EscalationStatus = Literal["open", "in_review", "resolved", "auto_escalated", "overridden"]


@dataclass
class DecisionSupportPackage:
    """Evidence-backed context supplied to a human reviewer."""

    alert_summary: dict[str, Any]
    evidence_compilation: list[EvidenceItem]
    historical_context: list[dict[str, Any]]
    regulatory_context: list[str]
    recommended_action: str
    risk_assessment: dict[str, Any]
    similar_cases: list[dict[str, Any]]
    agent_disagreement: dict[str, Any] | None = None


@dataclass
class HumanDecision:
    """A human decision on an escalation."""

    decision: DecisionType
    justification: str
    decided_by: str
    decided_at: datetime
    confidence_after: float

    def __post_init__(self) -> None:
        if len(self.justification.strip()) < 1:
            raise EscalationError("Human decision justification cannot be empty")
        if not 0.0 <= self.confidence_after <= 1.0:
            raise EscalationError("confidence_after must be between 0 and 1")


@dataclass
class OverrideRequest:
    """Request to replace a previously recorded decision."""

    original_decision: str
    override_decision: str
    justification: str
    requested_by: str
    secondary_approver: str | None = None
    approved_at: datetime | None = None


@dataclass
class EscalationRecord:
    """In-memory lifecycle record for one escalation."""

    escalation_id: UUID
    alert_message: Message
    created_at: datetime
    assigned_to: str
    tier: int
    sla_deadline: datetime
    status: EscalationStatus
    decision_support_package: DecisionSupportPackage
    human_decision: HumanDecision | None = None
    resolution: str | None = None
    audit_trail: list[AuditEntry] = field(default_factory=list)


class EscalationService:
    """Manage human review records without external notification integrations."""

    DEFAULT_SLA_SECONDS = {1: 4 * 60 * 60, 2: 2 * 60 * 60, 3: 60 * 60, 4: 30 * 60}
    REQUIRED_OVERRIDE_TIER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

    def __init__(self, config: Mapping[str, Any] | None, orchestrator: Orchestrator) -> None:
        self.config = dict(config or {})
        self.orchestrator = orchestrator
        assignment_config = self.config.get("human_assignment", {})
        if not isinstance(assignment_config, Mapping):
            assignment_config = {}
        self.assignment_engine = HumanAssignmentEngine(assignment_config)
        self.records: dict[UUID, EscalationRecord] = {}
        self._override_history: list[tuple[str, str, datetime]] = []
        from src.mcms.core.feedback import FeedbackLoop

        feedback_config = self.config.get("feedback", {})
        if not isinstance(feedback_config, Mapping):
            feedback_config = {}
        self.feedback_loop: FeedbackLoop | None = FeedbackLoop(feedback_config)
        self.feedback_loop.attach_service(self)

    @property
    def escalations(self) -> list[EscalationRecord]:
        return list(self.records.values())

    @staticmethod
    def _severity(alert: Message) -> str:
        return str(_payload(alert).get("severity", "LOW")).upper()

    @staticmethod
    def _conflict_type(alert: Message) -> str | None:
        value = _payload(alert).get("conflict_type")
        consensus = _payload(alert).get("consensus_result")
        if value is None and isinstance(consensus, Mapping):
            value = consensus.get("conflict_type")
        return str(value) if value else None

    def determine_tier(self, alert: Message, conflict_type: str | None) -> int:
        """Determine the minimum human tier for an alert and its context."""
        payload = _payload(alert)
        severity = self._severity(alert)
        if (
            conflict_type == "E"
            or payload.get("cross_jurisdictional")
            or payload.get("agent_status") in {"DEGRADED", "STOPPED"}
            or payload.get("sanctions_related")
            or payload.get("system_generated_anomaly")
        ):
            return 3
        if payload.get("mria") or payload.get("board_level") or payload.get("senior_management"):
            return 4
        violation_type = str(payload.get("violation_type", "")).lower()
        if any(token in violation_type for token in ("sanction", "ofac", "insider", "10b-5")):
            return 3
        if payload.get("repeated_violation_count", 0) >= 3:
            return 3
        if severity == "CRITICAL":
            return 3
        if severity == "HIGH":
            return 2
        return 1

    def _sla_seconds(self, tier: int) -> int:
        configured = self.config.get("sla_seconds", {})
        if isinstance(configured, Mapping):
            value = configured.get(tier, configured.get(f"TIER_{tier}"))
            if value is not None:
                try:
                    return max(1, int(value))
                except (TypeError, ValueError):
                    pass
        return self.DEFAULT_SLA_SECONDS[tier]

    def _required_skills(self, alert: Message, conflict_type: str | None) -> list[str]:
        payload = _payload(alert)
        configured = payload.get("required_skills", [])
        skills = (
            [str(skill).lower() for skill in configured] if isinstance(configured, list) else []
        )
        if conflict_type == "E" or payload.get("jurisdiction"):
            skills.append("regulatory")
        return list(dict.fromkeys(skills))

    def get_decision_support_package(self, escalation_id: UUID) -> DecisionSupportPackage:
        """Return the immutable-at-call-time decision support package for an escalation."""
        record = self.records.get(escalation_id)
        if record is None:
            raise EscalationError(f"Escalation not found: {escalation_id}")
        return record.decision_support_package

    def _build_package(self, alert: Message, conflict_type: str | None) -> DecisionSupportPackage:
        payload = _payload(alert)
        timestamp = datetime.fromisoformat(alert.timestamp.replace("Z", "+00:00")).astimezone(UTC)
        evidence = [
            EvidenceItem(
                evidence_type="message_reference",
                evidence_data={"reference": reference},
                source_agent=alert.sender_agent_id,
                timestamp=timestamp,
                chain_of_custody=[alert.sender_agent_id, str(reference)],
            )
            for reference in payload.get("evidence_refs", [])
        ]
        disagreement = payload.get("consensus_result")
        disagreement_data = dict(disagreement) if isinstance(disagreement, Mapping) else None
        if disagreement_data is None and conflict_type is not None:
            disagreement_data = {"conflict_type": conflict_type}
        severity = self._severity(alert)
        confidence = alert.confidence_score if alert.confidence_score is not None else 0.0
        regulatory_context = []
        if payload.get("jurisdiction"):
            regulatory_context.append(str(payload["jurisdiction"]))
        if payload.get("regulatory_requirement"):
            regulatory_context.append(str(payload["regulatory_requirement"]))
        return DecisionSupportPackage(
            alert_summary={
                "alert_id": alert.message_id,
                "violation_type": payload.get("violation_type"),
                "severity": severity,
                "confidence": confidence,
                "detected_at": payload.get("detected_at", alert.timestamp),
            },
            evidence_compilation=evidence,
            historical_context=list(self.config.get("historical_context", [])),
            regulatory_context=regulatory_context,
            recommended_action=(
                "Apply consensus recommendation and review dissenting evidence"
                if disagreement_data
                else "Review alert evidence and determine disposition"
            ),
            risk_assessment={
                "financial": severity in {"HIGH", "CRITICAL"},
                "reputational": severity == "CRITICAL",
                "regulatory": bool(regulatory_context) or severity in {"HIGH", "CRITICAL"},
            },
            similar_cases=list(self.config.get("similar_cases", [])),
            agent_disagreement=disagreement_data,
        )

    async def assign_to_human(self, escalation: EscalationRecord) -> str:
        """Assign an escalation using the human assignment engine."""
        conflict_type = self._conflict_type(escalation.alert_message)
        entities = [
            str(item) for item in _payload(escalation.alert_message).get("affected_entities", [])
        ]
        assigned = self.assignment_engine.assign(
            escalation.tier,
            self._required_skills(escalation.alert_message, conflict_type),
            conflict_entities=entities,
        )
        escalation.assigned_to = assigned
        return assigned

    async def escalate(
        self, message: Message, reason: str, recommended_tier: int = 1
    ) -> EscalationRecord:
        """Create, assign, and audit a human escalation record."""
        conflict_type = self._conflict_type(message)
        tier = max(self.determine_tier(message, conflict_type), min(4, max(1, recommended_tier)))
        created_at = datetime.now(UTC)
        package = self._build_package(message, conflict_type)
        record = EscalationRecord(
            escalation_id=uuid4(),
            alert_message=message,
            created_at=created_at,
            assigned_to="unassigned",
            tier=tier,
            sla_deadline=created_at + timedelta(seconds=self._sla_seconds(tier)),
            status="open",
            decision_support_package=package,
        )
        self.records[record.escalation_id] = record
        try:
            await self.assign_to_human(record)
        except Exception:
            record.assigned_to = "unassigned"
        self._audit(record, "ESCALATION_CREATED", {"reason": reason})
        return record

    def _audit(self, record: EscalationRecord, action: str, context: dict[str, Any]) -> None:
        audit_chain = getattr(self.orchestrator, "_audit_chain", None)
        data = {
            "action": action,
            "escalation_id": str(record.escalation_id),
            "alert_id": record.alert_message.message_id,
            "tier": record.tier,
            "assigned_to": record.assigned_to,
            "status": record.status,
            **context,
        }
        if audit_chain is not None:
            record.audit_trail.append(audit_chain.append(data, agent_id="escalation-service"))
        observability = getattr(self.orchestrator, "_observability", None)
        if observability is not None:
            observability.log_escalation(record.escalation_id, action, context)

    async def check_sla(self) -> list[EscalationRecord]:
        """Return open records at or beyond the 50-percent SLA warning point."""
        now = datetime.now(UTC)
        due: list[EscalationRecord] = []
        for record in self.records.values():
            if record.status in {"resolved", "overridden"}:
                continue
            total_seconds = self._sla_seconds(record.tier)
            warning_deadline = record.created_at + timedelta(seconds=total_seconds / 2)
            if now >= warning_deadline:
                due.append(record)
        return due

    async def auto_escalate(self, escalation_id: UUID) -> None:
        """Move an overdue record to the next tier and reassign it."""
        record = self.records.get(escalation_id)
        if record is None:
            raise EscalationError(f"Escalation not found: {escalation_id}")
        if record.tier >= 4:
            record.status = "open"
            self._audit(record, "SLA_VIOLATION_TIER_4", {})
            raise SlaViolationError("Tier 4 escalation has exceeded its final SLA")
        previous_tier = record.tier
        record.tier += 1
        record.status = "auto_escalated"
        record.sla_deadline = datetime.now(UTC) + timedelta(seconds=self._sla_seconds(record.tier))
        try:
            await self.assign_to_human(record)
        except Exception:
            record.assigned_to = "unassigned"
        self._audit(record, "AUTO_ESCALATED", {"previous_tier": previous_tier})

    async def record_decision(self, escalation_id: UUID, human_decision: HumanDecision) -> None:
        """Record a human disposition and emit feedback when configured."""
        record = self.records.get(escalation_id)
        if record is None:
            raise EscalationError(f"Escalation not found: {escalation_id}")
        record.human_decision = human_decision
        record.status = "overridden" if human_decision.decision == "override" else "resolved"
        record.resolution = human_decision.decision
        self._audit(
            record,
            "HUMAN_DECISION",
            {
                "decision": human_decision.decision,
                "decided_by": human_decision.decided_by,
                "confidence_after": human_decision.confidence_after,
                "justification": human_decision.justification,
            },
        )
        if self.feedback_loop is not None:
            await self.feedback_loop.capture_feedback(escalation_id, human_decision)
        observability = getattr(self.orchestrator, "_observability", None)
        if observability is not None:
            observability.log_human_decision(
                escalation_id,
                human_decision.decided_by,
                human_decision.decision,
                human_decision.justification,
            )
        if record.assigned_to != "unassigned":
            self.assignment_engine.release(record.assigned_to)

    async def process_override(self, escalation_id: UUID, override: OverrideRequest) -> None:
        """Validate and record a human override under the authority matrix."""
        record = self.records.get(escalation_id)
        if record is None:
            raise OverrideDeniedError(f"Escalation not found: {escalation_id}")
        if len(override.justification.strip()) < 50:
            raise OverrideDeniedError("Override justification must contain at least 50 characters")
        human = self.assignment_engine.humans.get(override.requested_by)
        required_tier = self.REQUIRED_OVERRIDE_TIER.get(self._severity(record.alert_message), 4)
        if human is None or human.tier < required_tier:
            raise OverrideDeniedError("Requester lacks authority for this alert severity")
        if required_tier == 4 and (
            not override.secondary_approver or override.secondary_approver == override.requested_by
        ):
            raise OverrideDeniedError(
                "CRITICAL overrides require an independent secondary approver"
            )
        violation_type = str(_payload(record.alert_message).get("violation_type", ""))
        now = datetime.now(UTC)
        if any(
            human_id == override.requested_by
            and violation == violation_type
            and (now - timestamp).total_seconds() < 3600
            for human_id, violation, timestamp in self._override_history
        ):
            raise OverrideDeniedError(
                "The same analyst cannot override this violation type within one hour"
            )
        self._override_history.append((override.requested_by, violation_type, now))
        decision = HumanDecision(
            decision="override",
            justification=override.justification,
            decided_by=override.requested_by,
            decided_at=override.approved_at or now,
            confidence_after=float(record.alert_message.confidence_score or 0.0),
        )
        await self.record_decision(escalation_id, decision)
        self._audit(
            record,
            "HUMAN_OVERRIDE",
            {
                "before": override.original_decision,
                "after": override.override_decision,
                "secondary_approver": override.secondary_approver,
            },
        )

    async def close_escalation(self, escalation_id: UUID, resolution: str) -> None:
        """Close an escalation with an auditable resolution statement."""
        record = self.records.get(escalation_id)
        if record is None:
            raise EscalationError(f"Escalation not found: {escalation_id}")
        if not resolution.strip():
            raise EscalationError("Escalation resolution cannot be empty")
        record.resolution = resolution
        record.status = "resolved"
        self._audit(record, "ESCALATION_CLOSED", {"resolution": resolution})
        if record.assigned_to != "unassigned":
            self.assignment_engine.release(record.assigned_to)
