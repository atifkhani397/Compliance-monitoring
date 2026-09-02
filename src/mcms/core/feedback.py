"""In-memory human-feedback capture and rule-based agent calibration for Phase 4."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from src.mcms.core.exceptions import FeedbackError

if TYPE_CHECKING:
    from src.mcms.core.escalation import EscalationService, HumanDecision


@dataclass
class FeedbackRecord:
    """Labeled feedback record used for threshold and performance analysis."""

    feedback_id: UUID
    escalation_id: UUID
    alert_id: UUID
    agent_id: str
    violation_type: str
    agent_confidence: float
    human_decision: str
    human_confidence: float | None
    was_correct: bool | None
    justification: str
    timestamp: datetime
    human_id: str = "unknown"

    def __post_init__(self) -> None:
        if not 0.0 <= self.agent_confidence <= 1.0:
            raise FeedbackError("agent_confidence must be between 0 and 1")
        if self.human_confidence is not None and not 0.0 <= self.human_confidence <= 1.0:
            raise FeedbackError("human_confidence must be between 0 and 1")
        if self.human_decision not in {"approve", "reject", "override", "request_more_info"}:
            raise FeedbackError(f"Unsupported human decision: {self.human_decision}")


class FeedbackLoop:
    """Capture feedback and expose deterministic, review-gated calibration rules."""

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        self.config = dict(config or {})
        self.records: list[FeedbackRecord] = []
        self.thresholds: dict[str, float] = (
            {str(key): float(value) for key, value in self.config.get("thresholds", {}).items()}
            if isinstance(self.config.get("thresholds", {}), Mapping)
            else {}
        )
        self.agent_weights: dict[str, float] = (
            {str(key): float(value) for key, value in self.config.get("agent_weights", {}).items()}
            if isinstance(self.config.get("agent_weights", {}), Mapping)
            else {}
        )
        self.pending_updates: list[dict[str, Any]] = []
        self._escalation_service: EscalationService | None = None

    def attach_service(self, escalation_service: EscalationService) -> None:
        self._escalation_service = escalation_service

    async def capture_feedback(
        self, escalation_id: UUID, human_decision: HumanDecision
    ) -> FeedbackRecord:
        """Create a labeled record from an escalation and a human decision."""
        if self._escalation_service is None:
            raise FeedbackError("FeedbackLoop must be attached to an EscalationService")
        escalation = self._escalation_service.records.get(escalation_id)
        if escalation is None:
            raise FeedbackError(f"Escalation not found: {escalation_id}")
        payload = escalation.alert_message.payload
        if not isinstance(payload, dict):
            raise FeedbackError("Escalation alert payload is not a dictionary")
        confidence = escalation.alert_message.confidence_score
        record = FeedbackRecord(
            feedback_id=uuid4(),
            escalation_id=escalation_id,
            alert_id=UUID(escalation.alert_message.message_id),
            agent_id=escalation.alert_message.sender_agent_id,
            violation_type=str(payload.get("violation_type", "unknown")),
            agent_confidence=float(confidence or 0.0),
            human_decision=human_decision.decision,
            human_confidence=human_decision.confidence_after,
            was_correct=None,
            justification=human_decision.justification,
            timestamp=human_decision.decided_at,
            human_id=human_decision.decided_by,
        )
        self.records.append(record)
        return record

    @staticmethod
    def _within_window(timestamp: datetime, window_days: int) -> bool:
        return timestamp >= datetime.now(UTC) - timedelta(days=window_days)

    def calculate_false_positive_rate(
        self, agent_id: str, violation_type: str, window_days: int
    ) -> float:
        """Return rejected-alert share for an agent and violation type."""
        matching = [
            record
            for record in self.records
            if record.agent_id == agent_id
            and record.violation_type == violation_type
            and self._within_window(record.timestamp, window_days)
        ]
        if not matching:
            return 0.0
        rejected = sum(record.human_decision == "reject" for record in matching)
        return rejected / len(matching)

    def get_human_decision_patterns(self, human_id: str, window_days: int) -> dict[str, Any]:
        """Return decision counts and rates for one human reviewer."""
        matching = [
            record
            for record in self.records
            if record.timestamp >= datetime.now(UTC) - timedelta(days=window_days)
            and self._record_human_id(record) == human_id
        ]
        counts = Counter(record.human_decision for record in matching)
        total = len(matching)
        return {
            "human_id": human_id,
            "total_decisions": total,
            "decision_counts": dict(counts),
            "approval_rate": counts.get("approve", 0) / total if total else 0.0,
            "override_frequency": counts.get("override", 0) / total if total else 0.0,
            "average_response_seconds": 0.0,
        }

    @staticmethod
    def _record_human_id(record: FeedbackRecord) -> str:
        # The decision maker is intentionally encoded in the justification metadata
        # only when an integration supplies it; the base contract remains compact.
        return record.human_id

    def _schedule_update(self, update: dict[str, Any]) -> None:
        review_seconds = int(self.config.get("review_period_seconds", 24 * 60 * 60))
        update["effective_at"] = datetime.now(UTC) + timedelta(seconds=max(0, review_seconds))
        self.pending_updates.append(update)

    async def batch_update_thresholds(self) -> dict[str, Any]:
        """Apply due updates and schedule the weekly rule-based adjustments."""
        now = datetime.now(UTC)
        applied: dict[str, float] = {}
        remaining: list[dict[str, Any]] = []
        for update in self.pending_updates:
            effective_at = update.get("effective_at")
            if isinstance(effective_at, datetime) and effective_at <= now:
                key = str(update["threshold_key"])
                self.thresholds[key] = max(0.0, min(1.0, float(update["new_threshold"])))
                applied[key] = self.thresholds[key]
            else:
                remaining.append(update)
        self.pending_updates = remaining

        grouped: dict[tuple[str, str], list[FeedbackRecord]] = {}
        for record in self.records:
            grouped.setdefault((record.agent_id, record.violation_type), []).append(record)
        scheduled: dict[str, float] = {}
        for (agent_id, violation_type), records in grouped.items():
            key = f"{agent_id}:{violation_type}"
            current = self.thresholds.get(key, 0.5)
            rejects = sum(record.human_decision == "reject" for record in records)
            approvals_low_confidence = sum(
                record.human_decision == "approve" and record.agent_confidence < 0.5
                for record in records
            )
            new_value = current
            if rejects >= 3:
                new_value = min(1.0, current + 0.1)
            elif approvals_low_confidence > 0:
                new_value = max(0.0, current - 0.05)
            if new_value != current:
                update = {
                    "threshold_key": key,
                    "agent_id": agent_id,
                    "violation_type": violation_type,
                    "old_threshold": current,
                    "new_threshold": new_value,
                    "reason": "human_feedback_rule",
                }
                self._schedule_update(update)
                scheduled[key] = new_value

        # Apply newly scheduled updates only when their configured review period
        # has elapsed; the default period remains 24 hours.
        remaining = []
        for update in self.pending_updates:
            effective_at = update.get("effective_at")
            if isinstance(effective_at, datetime) and effective_at <= datetime.now(UTC):
                key = str(update["threshold_key"])
                self.thresholds[key] = max(0.0, min(1.0, float(update["new_threshold"])))
                applied[key] = self.thresholds[key]
            else:
                remaining.append(update)
        self.pending_updates = remaining
        return {
            "applied": applied,
            "scheduled": scheduled,
            "pending_count": len(self.pending_updates),
        }

    async def update_agent_weights(self, agent_id: str, adjustment: dict[str, Any]) -> None:
        """Adjust an agent weight, applying the false-positive rule when requested."""
        current = self.agent_weights.get(agent_id, 0.0)
        delta_value = adjustment.get("delta", adjustment.get("adjustment"))
        if delta_value is None and adjustment.get("false_positive_rate", 0.0) > 0.15:
            delta_value = -0.05
        if delta_value is None:
            raise FeedbackError("Weight adjustment requires delta or adjustment")
        try:
            new_weight = max(0.0, min(1.0, current + float(delta_value)))
        except (TypeError, ValueError) as error:
            raise FeedbackError("Weight adjustment must be numeric") from error
        self.agent_weights[agent_id] = new_weight

    def export_to_jsonl(self) -> str:
        """Export feedback records as line-delimited JSON."""
        lines = []
        for record in self.records:
            data = asdict(record)
            data["feedback_id"] = str(record.feedback_id)
            data["escalation_id"] = str(record.escalation_id)
            data["alert_id"] = str(record.alert_id)
            data["timestamp"] = record.timestamp.isoformat()
            lines.append(json.dumps(data, sort_keys=True))
        return "\n".join(lines)
