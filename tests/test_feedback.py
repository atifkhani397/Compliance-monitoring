from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.mcms.core.config import Config
from src.mcms.core.escalation import HumanDecision
from src.mcms.core.feedback import FeedbackLoop, FeedbackRecord
from src.mcms.core.human_assignment import HumanProfile
from src.mcms.core.orchestrator import Orchestrator
from tests.test_escalation import make_alert


def setup_feedback() -> tuple[FeedbackLoop, object, str]:
    orchestrator = Orchestrator(Config())
    service = orchestrator._escalation_service
    service.assignment_engine.register_human(HumanProfile("analyst-1", "Analyst", 1, []))
    feedback = FeedbackLoop({"review_period_seconds": 0, "agent_weights": {"agent-tm-001": 0.35}})
    feedback.attach_service(service)
    service.feedback_loop = feedback
    return feedback, service, "analyst-1"


@pytest.mark.asyncio
async def test_capture_feedback_from_human_decision() -> None:
    feedback, service, human_id = setup_feedback()
    escalation = await service.escalate(make_alert(), "capture")
    record = await service.record_decision(
        escalation.escalation_id,
        HumanDecision(
            "approve", "The alert is supported by the evidence.", human_id, datetime.now(UTC), 0.9
        ),
    )
    assert record is None
    assert len(feedback.records) == 1
    assert feedback.records[0].alert_id == UUID(escalation.alert_message.message_id)


@pytest.mark.asyncio
async def test_calculate_false_positive_rate() -> None:
    feedback, service, human_id = setup_feedback()
    for _ in range(2):
        escalation = await service.escalate(make_alert(), "rate")
        await service.record_decision(
            escalation.escalation_id,
            HumanDecision(
                "reject",
                "The evidence does not support this alert.",
                human_id,
                datetime.now(UTC),
                0.1,
            ),
        )
    assert feedback.calculate_false_positive_rate("agent-tm-001", "test", 30) == 1.0


@pytest.mark.asyncio
async def test_get_human_decision_patterns() -> None:
    feedback, service, human_id = setup_feedback()
    escalation = await service.escalate(make_alert(), "patterns")
    await service.record_decision(
        escalation.escalation_id,
        HumanDecision(
            "approve",
            "The alert is supported by independent evidence.",
            human_id,
            datetime.now(UTC),
            0.8,
        ),
    )
    patterns = feedback.get_human_decision_patterns(human_id, 30)
    assert patterns["total_decisions"] == 1
    assert patterns["approval_rate"] == 1.0


@pytest.mark.asyncio
async def test_update_agent_threshold_raise() -> None:
    feedback, service, human_id = setup_feedback()
    for _ in range(3):
        escalation = await service.escalate(make_alert(), "raise")
        await service.record_decision(
            escalation.escalation_id,
            HumanDecision(
                "reject",
                "Repeated rejection demonstrates a false-positive pattern.",
                human_id,
                datetime.now(UTC),
                0.1,
            ),
        )
    result = await feedback.batch_update_thresholds()
    assert result["scheduled"]["agent-tm-001:test"] == 0.6
    assert feedback.thresholds["agent-tm-001:test"] == 0.6


@pytest.mark.asyncio
async def test_update_agent_threshold_lower() -> None:
    feedback, service, human_id = setup_feedback()
    escalation = await service.escalate(make_alert(confidence=0.4), "lower")
    await service.record_decision(
        escalation.escalation_id,
        HumanDecision(
            "approve",
            "Low-confidence alert approved after evidence review.",
            human_id,
            datetime.now(UTC),
            0.9,
        ),
    )
    result = await feedback.batch_update_thresholds()
    assert result["scheduled"]["agent-tm-001:test"] == 0.45


@pytest.mark.asyncio
async def test_batch_update_thresholds_applies_due_changes() -> None:
    feedback, service, human_id = setup_feedback()
    feedback.thresholds["agent-tm-001:test"] = 0.5
    for _ in range(3):
        escalation = await service.escalate(make_alert(), "batch")
        await service.record_decision(
            escalation.escalation_id,
            HumanDecision(
                "reject",
                "Batch review confirms insufficient supporting evidence.",
                human_id,
                datetime.now(UTC),
                0.1,
            ),
        )
    await feedback.batch_update_thresholds()
    assert feedback.thresholds["agent-tm-001:test"] == 0.6


@pytest.mark.asyncio
async def test_update_agent_weights() -> None:
    feedback, _, _ = setup_feedback()
    await feedback.update_agent_weights("agent-tm-001", {"false_positive_rate": 0.2})
    assert feedback.agent_weights["agent-tm-001"] == 0.3


def test_feedback_record_structure_validation() -> None:
    record = FeedbackRecord(
        feedback_id=UUID("00000000-0000-4000-8000-000000000001"),
        escalation_id=UUID("00000000-0000-4000-8000-000000000002"),
        alert_id=UUID("00000000-0000-4000-8000-000000000003"),
        agent_id="agent-tm-001",
        violation_type="test",
        agent_confidence=0.8,
        human_decision="approve",
        human_confidence=0.9,
        was_correct=None,
        justification="valid",
        timestamp=datetime.now(UTC),
        human_id="analyst-1",
    )
    assert record.agent_id == "agent-tm-001"
    assert record.human_id == "analyst-1"
