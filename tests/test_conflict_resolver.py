import secrets
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest

from src.mcms.agents.base import BaseAgent
from src.mcms.core.config import Config
from src.mcms.core.conflict_resolver import ConflictResolver
from src.mcms.core.exceptions import ConflictDetectionError
from src.mcms.core.message import Message
from src.mcms.core.orchestrator import Orchestrator


class RecordingAgent(BaseAgent):
    agent_id = "agent-rg-001"

    async def process_message(self, message: Message) -> Message:
        self.outbound_queue.append(message)
        return message


def alert(
    sender: str,
    correlation_id: str,
    confidence: float,
    severity: str = "HIGH",
    timestamp: datetime | None = None,
    **context: Any,
) -> Message:
    now = timestamp or datetime.now(UTC)
    payload = {
        "violation_type": "market-manipulation",
        "severity": severity,
        "detected_at": now.isoformat(),
        "evidence_refs": [f"evidence-{sender}"],
        "affected_entities": context.pop("affected_entities", ["account-1"]),
        **context,
    }
    return Message.model_validate(
        {
            "message_id": str(uuid4()),
            "protocol_version": "1.0.0",
            "timestamp": now.isoformat(),
            "sender_agent_id": sender,
            "recipient_agent_id": "agent-rg-001",
            "message_type": "ALERT",
            "priority": 2,
            "correlation_id": correlation_id,
            "trace_id": str(uuid4()),
            "payload_schema": "alert-v1",
            "payload": payload,
            "confidence_score": confidence,
            "ttl_seconds": 300,
            "retry_count": 0,
            "audit_classification": "REGULATORY",
            "sender_signature": "cGxhY2Vob2xkZXI=",
            "nonce": secrets.token_hex(8),
        }
    )


@pytest.fixture
def resolver() -> tuple[ConflictResolver, Orchestrator]:
    orchestrator = Orchestrator(Config())
    return orchestrator._conflict_resolver, orchestrator


def test_detect_conflict_between_disagreeing_alerts(
    resolver: tuple[ConflictResolver, Orchestrator],
) -> None:
    service, _ = resolver
    correlation_id = str(uuid4())
    assert (
        service.detect_conflict(
            [
                alert("agent-tm-001", correlation_id, 0.9),
                alert("agent-cs-001", correlation_id, 0.2),
            ]
        )
        is True
    )


def test_no_conflict_between_agreeing_alerts(
    resolver: tuple[ConflictResolver, Orchestrator],
) -> None:
    service, _ = resolver
    correlation_id = str(uuid4())
    first = alert("agent-tm-001", correlation_id, 0.8)
    second = alert("agent-cs-001", correlation_id, 0.8)
    assert service.detect_conflict([first, second]) is False


@pytest.mark.asyncio
async def test_classify_type_a(resolver: tuple[ConflictResolver, Orchestrator]) -> None:
    service, _ = resolver
    correlation_id = str(uuid4())
    assert (
        service.classify_conflict(
            [
                alert("agent-tm-001", correlation_id, 0.9),
                alert("agent-cs-001", correlation_id, 0.2),
            ]
        )
        == "A"
    )


@pytest.mark.asyncio
async def test_classify_type_b(resolver: tuple[ConflictResolver, Orchestrator]) -> None:
    service, _ = resolver
    correlation_id = str(uuid4())
    assert (
        service.classify_conflict(
            [
                alert("agent-tm-001", correlation_id, 0.8, severity="CRITICAL"),
                alert("agent-cs-001", correlation_id, 0.8, severity="HIGH"),
            ]
        )
        == "B"
    )


@pytest.mark.asyncio
async def test_handle_false_positive_suppresses_alert(
    resolver: tuple[ConflictResolver, Orchestrator],
) -> None:
    service, _ = resolver
    correlation_id = str(uuid4())
    result = await service.handle_false_positive(
        [
            alert("agent-tm-001", correlation_id, 0.9),
            alert("agent-cs-001", correlation_id, 0.2, exculpatory=True),
        ]
    )
    assert result.message_type == "ALERT"
    assert result.payload["consensus_result"]["consensus_severity"] == "NO_ALERT"
    assert result.payload["consensus_result"]["escalation_required"] is False


@pytest.mark.asyncio
async def test_handle_regulatory_conflict_escalates_to_legal_counsel(
    resolver: tuple[ConflictResolver, Orchestrator],
) -> None:
    service, _ = resolver
    correlation_id = str(uuid4())
    result = await service.handle_regulatory_conflict(
        [
            alert("agent-ru-001", correlation_id, 0.8, jurisdiction="EU"),
            alert("agent-cs-001", correlation_id, 0.8, jurisdiction="Singapore"),
        ]
    )
    assert result.message_type == "ESCALATION"
    assert result.payload["human_assignee_role"] == "legal-counsel"
    assert result.payload["conflict_type"] == "E"


def test_build_assessment_from_alert(resolver: tuple[ConflictResolver, Orchestrator]) -> None:
    service, _ = resolver
    message = alert("agent-tm-001", str(uuid4()), 0.8)
    assessment = service.build_assessment(message)
    assert assessment.agent_id == "agent-tm-001"
    assert assessment.confidence == Decimal("0.8")
    assert assessment.evidence[0].source_agent == "agent-tm-001"


@pytest.mark.asyncio
async def test_build_resolution_message_from_result(
    resolver: tuple[ConflictResolver, Orchestrator],
) -> None:
    service, _ = resolver
    correlation_id = str(uuid4())
    result = await service.resolve_conflict(
        [
            alert("agent-tm-001", correlation_id, 0.9),
            alert("agent-cs-001", correlation_id, 0.2),
        ]
    )
    assert result.message_type in {"ALERT", "ESCALATION"}
    assert result.sender_agent_id == "agent-rg-001"


def test_time_window_expiration(resolver: tuple[ConflictResolver, Orchestrator]) -> None:
    service, _ = resolver
    correlation_id = str(uuid4())
    start = datetime(2026, 8, 22, 10, 0, tzinfo=UTC)
    within_window = [
        alert("agent-tm-001", correlation_id, 0.8, timestamp=start),
        alert("agent-cs-001", correlation_id, 0.8, timestamp=start + timedelta(seconds=90)),
    ]
    assert service.detect_conflict(within_window) is True
    assert service.classify_conflict(within_window) == "F"
    assert (
        service.detect_conflict(
            [
                alert("agent-tm-001", correlation_id, 0.9, timestamp=start),
                alert(
                    "agent-cs-001", correlation_id, 0.2, timestamp=start + timedelta(seconds=301)
                ),
            ]
        )
        is False
    )
    with pytest.raises(ConflictDetectionError):
        service.classify_conflict(
            [
                alert("agent-tm-001", correlation_id, 0.9, timestamp=start),
                alert(
                    "agent-cs-001", correlation_id, 0.2, timestamp=start + timedelta(seconds=301)
                ),
            ]
        )


@pytest.mark.asyncio
async def test_orchestrator_routes_correlated_alerts_to_resolver() -> None:
    orchestrator = Orchestrator(Config())
    report_agent = RecordingAgent()
    await orchestrator.register_agent(report_agent)
    correlation_id = str(uuid4())
    await orchestrator.dispatch(alert("agent-tm-001", correlation_id, 0.9))
    await orchestrator.dispatch(alert("agent-cs-001", correlation_id, 0.2))
    assert len(orchestrator._resolved_messages) == 1
    # The first alert is handled directly; the second correlated alert triggers
    # the resolver and adds one resolved output.
    assert len(report_agent.outbound_queue) == 2
    assert any(
        entry.data.get("action") == "CONFLICT_RESOLUTION"
        for entry in orchestrator._audit_chain.entries
    )


@pytest.mark.asyncio
async def test_single_alert_is_still_dispatched_directly() -> None:
    orchestrator = Orchestrator(Config())
    report_agent = RecordingAgent()
    await orchestrator.register_agent(report_agent)
    await orchestrator.dispatch(alert("agent-tm-001", str(uuid4()), 0.8))
    assert len(report_agent.outbound_queue) == 1
    assert len(orchestrator._resolved_messages) == 0
