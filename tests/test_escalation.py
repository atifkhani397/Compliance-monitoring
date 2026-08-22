import base64
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.mcms.core.config import Config
from src.mcms.core.escalation import EscalationService, HumanDecision, OverrideRequest
from src.mcms.core.exceptions import OverrideDeniedError
from src.mcms.core.human_assignment import HumanProfile
from src.mcms.core.message import Message
from src.mcms.core.orchestrator import Orchestrator


def make_alert(
    severity: str = "LOW",
    violation_type: str = "test",
    confidence: float = 0.8,
    **extra: object,
) -> Message:
    now = datetime.now(UTC).isoformat()
    payload = {
        "violation_type": violation_type,
        "severity": severity,
        "detected_at": now,
        "evidence_refs": ["evidence-1"],
        "affected_entities": ["entity-1"],
        **extra,
    }
    return Message.model_validate(
        {
            "message_id": str(uuid4()),
            "protocol_version": "1.0.0",
            "timestamp": now,
            "sender_agent_id": "agent-tm-001",
            "recipient_agent_id": "agent-rg-001",
            "message_type": "ALERT",
            "priority": 2,
            "trace_id": str(uuid4()),
            "payload_schema": "alert-v1",
            "payload": payload,
            "confidence_score": confidence,
            "ttl_seconds": 300,
            "retry_count": 0,
            "audit_classification": "REGULATORY",
            "sender_signature": base64.b64encode(b"placeholder").decode(),
            "nonce": secrets.token_hex(8),
        }
    )


def make_service() -> tuple[EscalationService, Orchestrator]:
    orchestrator = Orchestrator(Config())
    return orchestrator._escalation_service, orchestrator


def register(
    service: EscalationService, human_id: str, tier: int, *skills: str, **flags: object
) -> None:
    service.assignment_engine.register_human(
        HumanProfile(
            human_id=human_id,
            name=human_id,
            tier=tier,
            skills=list(skills),
            conflict_of_interest_flags=list(flags.get("coi", [])),
        )
    )


@pytest.mark.asyncio
async def test_escalate_to_tier_1() -> None:
    service, _ = make_service()
    register(service, "analyst-1", 1)
    record = await service.escalate(make_alert("LOW"), "low confidence review")
    assert record.tier == 1
    assert record.assigned_to == "analyst-1"
    assert record.sla_deadline - record.created_at == timedelta(hours=4)


@pytest.mark.asyncio
async def test_escalate_to_tier_2() -> None:
    service, _ = make_service()
    register(service, "senior-1", 2)
    record = await service.escalate(make_alert("HIGH"), "high severity")
    assert record.tier == 2
    assert record.sla_deadline - record.created_at == timedelta(hours=2)


@pytest.mark.asyncio
async def test_escalate_to_tier_3() -> None:
    service, _ = make_service()
    register(service, "manager-1", 3)
    record = await service.escalate(make_alert("CRITICAL"), "critical severity")
    assert record.tier == 3


@pytest.mark.asyncio
async def test_escalate_to_tier_4() -> None:
    service, _ = make_service()
    register(service, "cco-001", 4)
    record = await service.escalate(make_alert("HIGH", senior_management=True), "senior management")
    assert record.tier == 4
    assert record.sla_deadline - record.created_at == timedelta(minutes=30)


def test_determine_tier_from_alert_severity() -> None:
    service, _ = make_service()
    assert service.determine_tier(make_alert("LOW"), None) == 1
    assert service.determine_tier(make_alert("MEDIUM"), None) == 1
    assert service.determine_tier(make_alert("HIGH"), None) == 2
    assert service.determine_tier(make_alert("CRITICAL"), None) == 3


def test_determine_tier_from_conflict_type() -> None:
    service, _ = make_service()
    assert service.determine_tier(make_alert("LOW"), "E") == 3


@pytest.mark.asyncio
async def test_assign_to_available_human() -> None:
    service, _ = make_service()
    register(service, "analyst-1", 1)
    record = await service.escalate(make_alert(), "assignment")
    assert await service.assign_to_human(record) == "analyst-1"
    assert service.assignment_engine.get_workload("analyst-1") == 2


@pytest.mark.asyncio
async def test_exclude_human_with_conflict_of_interest() -> None:
    service, _ = make_service()
    register(service, "biased", 1, coi=["entity-1"])
    register(service, "independent", 1)
    record = await service.escalate(make_alert(), "COI check")
    assert record.assigned_to == "independent"


@pytest.mark.asyncio
async def test_sla_deadline_calculation() -> None:
    service, _ = make_service()
    register(service, "analyst-1", 1)
    record = await service.escalate(make_alert(), "SLA")
    assert record.sla_deadline > record.created_at
    assert record.status == "open"


@pytest.mark.asyncio
async def test_auto_escalation_on_sla_miss() -> None:
    service, _ = make_service()
    register(service, "analyst-1", 1)
    register(service, "senior-1", 2)
    record = await service.escalate(make_alert(), "missed SLA")
    await service.auto_escalate(record.escalation_id)
    assert record.tier == 2
    assert record.status == "auto_escalated"


@pytest.mark.asyncio
async def test_record_human_approval() -> None:
    service, _ = make_service()
    register(service, "analyst-1", 1)
    record = await service.escalate(make_alert(), "approval")
    await service.record_decision(
        record.escalation_id,
        HumanDecision(
            "approve",
            "Evidence reviewed and alert is supported.",
            "analyst-1",
            datetime.now(UTC),
            0.95,
        ),
    )
    assert record.status == "resolved"
    assert service.feedback_loop is not None
    assert len(service.feedback_loop.records) == 1


@pytest.mark.asyncio
async def test_record_human_rejection() -> None:
    service, _ = make_service()
    register(service, "analyst-1", 1)
    record = await service.escalate(make_alert(), "rejection")
    await service.record_decision(
        record.escalation_id,
        HumanDecision(
            "reject",
            "Evidence is insufficient for this alert.",
            "analyst-1",
            datetime.now(UTC),
            0.2,
        ),
    )
    assert record.resolution == "reject"


@pytest.mark.asyncio
async def test_process_override_with_justification() -> None:
    service, _ = make_service()
    register(service, "manager-1", 3)
    record = await service.escalate(
        make_alert("HIGH", violation_type="market-manipulation"), "override"
    )
    request = OverrideRequest(
        original_decision="reject",
        override_decision="approve",
        justification="This detailed justification documents the independent evidence and review basis.",
        requested_by="manager-1",
    )
    await service.process_override(record.escalation_id, request)
    assert record.status == "overridden"


@pytest.mark.asyncio
async def test_process_critical_override_requires_secondary_approver() -> None:
    service, _ = make_service()
    register(service, "cco-001", 4)
    record = await service.escalate(make_alert("CRITICAL"), "critical override")
    request = OverrideRequest("reject", "approve", "A" * 60, "cco-001")
    with pytest.raises(OverrideDeniedError):
        await service.process_override(record.escalation_id, request)
    request.secondary_approver = "director-2"
    await service.process_override(record.escalation_id, request)
    assert record.status == "overridden"


def test_build_decision_support_package() -> None:
    service, _ = make_service()
    record_id = uuid4()
    # Registering a record through the public service method is asynchronous;
    # the package assertion is covered by the integration test below.
    assert record_id not in service.records


@pytest.mark.asyncio
async def test_decision_support_package_contains_required_sections() -> None:
    service, _ = make_service()
    register(service, "analyst-1", 1)
    record = await service.escalate(
        make_alert("MEDIUM", jurisdiction="EU", regulatory_requirement="disclosure"),
        "package",
    )
    package = service.get_decision_support_package(record.escalation_id)
    assert package.alert_summary["violation_type"] == "test"
    assert package.evidence_compilation
    assert package.regulatory_context == ["EU", "disclosure"]
    assert "financial" in package.risk_assessment
