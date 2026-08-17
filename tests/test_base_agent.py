"""Test cases for MACMS BaseAgent abstract class and subclasses."""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.mcms.agents.base import BaseAgent
from src.mcms.core.exceptions import SecurityError
from src.mcms.core.message import Message


class ConcreteTestAgent(BaseAgent):
    agent_id = "agent-tm-001"

    async def process_message(self, message: Message) -> Message:
        self.processed_count += 1
        return message


def make_test_message(agent: BaseAgent) -> Message:
    now_str = datetime.now(UTC).isoformat()
    msg_dict = {
        "message_id": str(uuid4()),
        "protocol_version": "1.0.0",
        "timestamp": now_str,
        "sender_agent_id": agent.agent_id,
        "recipient_agent_id": "agent-cs-001",
        "message_type": "HEARTBEAT",
        "priority": 5,
        "trace_id": str(uuid4()),
        "payload_schema": "heartbeat-v1",
        "payload": {
            "agent_status": "HEALTHY",
            "queue_depth": 0,
            "last_processed_timestamp": now_str,
        },
        "ttl_seconds": 60,
        "retry_count": 0,
        "audit_classification": "DIAGNOSTIC",
        "sender_signature": "cGxhY2Vob2xkZXI=",
        "nonce": "1234567890123456",
    }
    temp = Message.model_validate(msg_dict)
    sig = agent.sign_message(temp)
    msg_dict["sender_signature"] = sig
    return Message.model_validate(msg_dict)


def test_abstract_base_agent_instantiation_raises_error():
    with pytest.raises(TypeError):
        BaseAgent({"secret_key": "test"})  # Can't instantiate abstract class


def test_concrete_agent_instantiation():
    agent = ConcreteTestAgent({"secret_key": "my-secret-key"})
    assert agent.agent_id == "agent-tm-001"
    assert agent.status == "HEALTHY"
    assert "agent-tm-001" in repr(agent)


def test_heartbeat_generation():
    agent = ConcreteTestAgent({"secret_key": "my-secret-key"})
    hb = agent.heartbeat()
    assert isinstance(hb, Message)
    assert hb.message_type == "HEARTBEAT"
    assert hb.sender_agent_id == "agent-tm-001"
    assert agent.verify_signature(hb) is True


def test_health_check_format():
    agent = ConcreteTestAgent()
    hc = agent.health_check()
    assert hc["agent_id"] == "agent-tm-001"
    assert hc["status"] == "HEALTHY"
    assert "uptime_seconds" in hc
    assert hc["queue_depth"] == 0


def test_message_signing_and_verification():
    agent = ConcreteTestAgent({"secret_key": "secret-123"})
    msg = make_test_message(agent)
    assert agent.verify_signature(msg) is True


def test_signature_verification_failure_on_tampered_payload():
    agent = ConcreteTestAgent({"secret_key": "secret-123"})
    msg = make_test_message(agent)

    # Tamper with message priority
    msg_dict = msg.model_dump()
    msg_dict["priority"] = 1
    tampered_msg = Message.model_validate(msg_dict)

    assert agent.verify_signature(tampered_msg) is False


def test_send_message_places_in_outbound_queue():
    async def _test():
        agent = ConcreteTestAgent({"secret_key": "secret-123"})
        msg = make_test_message(agent)
        await agent.send_message(msg)
        assert len(agent.outbound_queue) == 1
        assert agent.outbound_queue[0].message_id == msg.message_id

    asyncio.run(_test())


def test_send_message_rejects_unverified_signature():
    async def _test():
        agent = ConcreteTestAgent({"secret_key": "secret-123"})
        msg = make_test_message(agent)

        # Tamper with signature
        data = msg.model_dump()
        data["sender_signature"] = "aW52YWxpZC1zaWduYXR1cmU="
        bad_msg = Message.model_validate(data)

        with pytest.raises(SecurityError):
            await agent.send_message(bad_msg)

    asyncio.run(_test())
