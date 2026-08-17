"""Test cases for MACMS PriorityRoutingEngine."""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.mcms.core.exceptions import RoutingError
from src.mcms.core.message import Message
from src.mcms.core.routing import PriorityRoutingEngine


def make_msg(
    priority: int = 3, recipient: str | list[str] = "agent-cs-001", retry_count: int = 0
) -> Message:
    return Message.model_validate(
        {
            "message_id": str(uuid4()),
            "protocol_version": "1.0.0",
            "timestamp": datetime.now(UTC).isoformat(),
            "sender_agent_id": "agent-tm-001",
            "recipient_agent_id": recipient,
            "message_type": "HEARTBEAT",
            "priority": priority,
            "trace_id": str(uuid4()),
            "payload_schema": "heartbeat-v1",
            "payload": {
                "agent_status": "HEALTHY",
                "queue_depth": 0,
                "last_processed_timestamp": datetime.now(UTC).isoformat(),
            },
            "ttl_seconds": 300,
            "retry_count": retry_count,
            "audit_classification": "OPERATIONAL",
            "sender_signature": "dGVzdC1zaWduYXR1cmU=",
            "nonce": "1234567890123456",
        }
    )


def test_route_to_single_agent():
    async def _test():
        engine = PriorityRoutingEngine()
        msg = make_msg(recipient="agent-cs-001")
        recipients = await engine.route_message(msg)
        assert recipients == ["agent-cs-001"]
        assert engine.get_queue_depth("agent-cs-001") == 1

    asyncio.run(_test())


def test_route_to_multicast_agents():
    async def _test():
        engine = PriorityRoutingEngine()
        msg = make_msg(recipient=["agent-cs-001", "agent-rg-001"])
        recipients = await engine.route_message(msg)
        assert len(recipients) == 2
        assert engine.get_queue_depth("agent-cs-001") == 1
        assert engine.get_queue_depth("agent-rg-001") == 1

    asyncio.run(_test())


def test_priority_queue_ordering():
    async def _test():
        engine = PriorityRoutingEngine()

        msg_p3 = make_msg(priority=3)
        msg_p1 = make_msg(priority=1)
        msg_p2 = make_msg(priority=2)

        await engine.route_message(msg_p3)
        await engine.route_message(msg_p1)
        await engine.route_message(msg_p2)

        first = await engine.pop_next_message("agent-cs-001")
        second = await engine.pop_next_message("agent-cs-001")
        third = await engine.pop_next_message("agent-cs-001")

        assert first is not None and first.priority == 1
        assert second is not None and second.priority == 2
        assert third is not None and third.priority == 3

    asyncio.run(_test())


def test_backpressure_threshold_detection():
    async def _test():
        engine = PriorityRoutingEngine(max_queue_depth=2)
        await engine.route_message(make_msg())
        await engine.route_message(make_msg())

        assert engine.is_backpressure_triggered("agent-cs-001") is True

        with pytest.raises(RoutingError) as exc_info:
            await engine.route_message(make_msg())
        assert "Back-pressure limit reached" in exc_info.value.message

    asyncio.run(_test())


def test_dead_letter_queue_after_max_retries():
    async def _test():
        engine = PriorityRoutingEngine(max_retries=2)
        msg = make_msg(retry_count=3)  # retry_count > max_retries

        with pytest.raises(RoutingError) as exc_info:
            await engine.route_message(msg)
        assert exc_info.value.dead_letter_queue is True

        dlq = engine.get_dlq_entries()
        assert len(dlq) == 1
        assert dlq[0]["message"].message_id == msg.message_id

    asyncio.run(_test())


def test_invalid_recipient_rejection():
    async def _test():
        engine = PriorityRoutingEngine()
        data = make_msg().model_dump()
        data["recipient_agent_id"] = "agent-tm-001"
        msg = Message.model_construct(**data)
        msg.recipient_agent_id = "agent-invalid-999"

        with pytest.raises(RoutingError) as exc_info:
            await engine.route_message(msg)
        assert "Invalid recipient agent ID" in exc_info.value.message

    asyncio.run(_test())


def test_pop_empty_queue_returns_none():
    async def _test():
        engine = PriorityRoutingEngine()
        res = await engine.pop_next_message("agent-tm-001", timeout=0.1)
        assert res is None

    asyncio.run(_test())


def test_retry_count_increment():
    async def _test():
        engine = PriorityRoutingEngine(max_retries=5)
        msg = make_msg(retry_count=2)
        await engine.route_message(msg)
        popped = await engine.pop_next_message("agent-cs-001")
        assert popped is not None
        assert popped.retry_count == 2

    asyncio.run(_test())
