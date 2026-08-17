"""Tests for MCMS central orchestrator."""

import secrets
from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import uuid4

import pytest

from src.mcms.agents.base import BaseAgent
from src.mcms.core.config import Config
from src.mcms.core.exceptions import AgentNotFoundError
from src.mcms.core.message import Message
from src.mcms.core.orchestrator import Orchestrator


class MockAgent(BaseAgent):
    """Mock TM agent that records received messages."""

    agent_id: ClassVar[str] = "agent-tm-001"
    capabilities: ClassVar[list[str]] = ["pattern_detection"]

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.received: list[Message] = []

    async def process_message(self, message: Message) -> Message:
        self.received.append(message)
        self.processed_count += 1
        return message


class MockAgentCS(BaseAgent):
    """Mock CS agent that records received messages."""

    agent_id: ClassVar[str] = "agent-cs-001"
    capabilities: ClassVar[list[str]] = ["keyword_detection"]

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.received: list[Message] = []

    async def process_message(self, message: Message) -> Message:
        self.received.append(message)
        self.processed_count += 1
        return message


def _make_message(
    sender: str = "agent-tm-001",
    recipient: str | list[str] = "agent-cs-001",
    msg_type: str = "ALERT",
    priority: int = 1,
) -> Message:
    """Helper to create valid test messages of various types."""
    now = datetime.now(UTC).isoformat()
    nonce = secrets.token_hex(8)
    payload: dict[str, Any] = {}
    confidence: float | None = None
    correlation_id: str | None = None
    audit = "OPERATIONAL"

    if msg_type == "ALERT":
        payload = {
            "violation_type": "test",
            "severity": "LOW",
            "detected_at": now,
            "evidence_refs": [],
            "affected_entities": [],
        }
        confidence = 0.9
        audit = "REGULATORY"
    elif msg_type == "HEARTBEAT":
        payload = {
            "agent_status": "HEALTHY",
            "queue_depth": 0,
            "last_processed_timestamp": now,
        }
        audit = "DIAGNOSTIC"
    elif msg_type == "ESCALATION":
        payload = {
            "escalation_reason": "test",
            "recommended_tier": "TIER_1",
            "decision_support_package_ref": "ref-001",
            "human_assignee_role": "analyst",
        }
        confidence = 0.8
        audit = "REGULATORY"
    elif msg_type == "UPDATE":
        payload = {
            "update_type": "test",
            "entity_id": "e1",
            "changed_fields": {},
            "previous_values": {},
        }
        correlation_id = str(uuid4())
        audit = "OPERATIONAL"

    return Message.model_validate(
        {
            "message_id": str(uuid4()),
            "protocol_version": "1.0.0",
            "timestamp": now,
            "sender_agent_id": sender,
            "recipient_agent_id": recipient,
            "message_type": msg_type,
            "priority": priority,
            "correlation_id": correlation_id,
            "trace_id": str(uuid4()),
            "payload_schema": f"{msg_type.lower()}-v1",
            "payload": payload,
            "confidence_score": confidence,
            "ttl_seconds": 300,
            "retry_count": 0,
            "audit_classification": audit,
            "sender_signature": "cGxhY2Vob2xkZXI=",
            "nonce": nonce,
        }
    )


class TestOrchestrator:
    """Tests for Orchestrator class."""

    @pytest.mark.asyncio
    async def test_register_and_unregister_agent(self) -> None:
        orch = Orchestrator(Config())
        agent = MockAgent()
        await orch.register_agent(agent)
        assert orch.get_agent_health("agent-tm-001")["status"] == "HEALTHY"
        await orch.unregister_agent("agent-tm-001")
        health = orch.get_agent_health("agent-tm-001")
        assert health == {}

    @pytest.mark.asyncio
    async def test_dispatch_to_single_agent(self) -> None:
        orch = Orchestrator(Config())
        agent = MockAgentCS()
        await orch.register_agent(agent)
        msg = _make_message(sender="agent-tm-001", recipient="agent-cs-001")
        await orch.dispatch(msg)
        assert len(agent.received) == 1

    @pytest.mark.asyncio
    async def test_dispatch_to_multiple_agents(self) -> None:
        orch = Orchestrator(Config())
        agent_cs = MockAgentCS()
        agent_tm = MockAgent()
        await orch.register_agent(agent_cs)
        await orch.register_agent(agent_tm)
        msg = _make_message(
            sender="agent-tm-001",
            recipient=["agent-tm-001", "agent-cs-001"],
            msg_type="UPDATE",
        )
        await orch.dispatch(msg)
        assert len(agent_tm.received) == 1
        assert len(agent_cs.received) == 1

    @pytest.mark.asyncio
    async def test_handle_heartbeat(self) -> None:
        orch = Orchestrator(Config())
        agent = MockAgent()
        await orch.register_agent(agent)
        hb = _make_message(
            sender="agent-tm-001",
            recipient="agent-tm-001",
            msg_type="HEARTBEAT",
        )
        await orch.handle_heartbeat(hb)
        health = orch.get_agent_health("agent-tm-001")
        assert "status" in health

    @pytest.mark.asyncio
    async def test_escalate_message(self) -> None:
        orch = Orchestrator(Config())
        agent = MockAgent()
        await orch.register_agent(agent)
        msg = _make_message(sender="agent-tm-001", recipient="agent-tm-001")
        await orch.escalate(msg, reason="Test escalation")
        assert len(orch._escalation_queue) == 1

    @pytest.mark.asyncio
    async def test_get_agent_health(self) -> None:
        orch = Orchestrator(Config())
        agent = MockAgent()
        await orch.register_agent(agent)
        health = orch.get_agent_health("agent-tm-001")
        assert health["agent_id"] == "agent-tm-001"
        assert health["status"] == "HEALTHY"

    @pytest.mark.asyncio
    async def test_get_system_health(self) -> None:
        orch = Orchestrator(Config())
        await orch.register_agent(MockAgent())
        await orch.register_agent(MockAgentCS())
        system_health = orch.get_system_health()
        assert len(system_health["agents"]) == 2

    @pytest.mark.asyncio
    async def test_graceful_shutdown(self) -> None:
        orch = Orchestrator(Config())
        agent = MockAgent()
        await orch.register_agent(agent)
        await orch.shutdown()
        assert orch._shutdown is True

    @pytest.mark.asyncio
    async def test_dispatch_to_unregistered_agent_raises_error(self) -> None:
        orch = Orchestrator(Config())
        msg = _make_message(sender="agent-tm-001", recipient="agent-cs-001")
        with pytest.raises(AgentNotFoundError):
            await orch.dispatch(msg)

    @pytest.mark.asyncio
    async def test_audit_trail_logging_on_dispatch(self) -> None:
        orch = Orchestrator(Config())
        agent = MockAgentCS()
        await orch.register_agent(agent)
        msg = _make_message(sender="agent-tm-001", recipient="agent-cs-001")
        await orch.dispatch(msg)
        assert len(orch._audit_chain.entries) >= 1
