"""Tests for MCMS agent registry service."""

import asyncio
from typing import Any, ClassVar

import pytest

from src.mcms.agents.base import BaseAgent
from src.mcms.core.exceptions import AgentNotFoundError
from src.mcms.core.message import Message
from src.mcms.core.registry import AgentRegistry


class StubAgentA(BaseAgent):
    """Stub agent for testing with TM identity."""

    agent_id: ClassVar[str] = "agent-tm-001"
    capabilities: ClassVar[list[str]] = ["pattern_detection"]

    async def process_message(self, message: Message) -> Message:
        raise NotImplementedError("StubAgentA does not process messages")


class StubAgentB(BaseAgent):
    """Stub agent for testing with CS identity."""

    agent_id: ClassVar[str] = "agent-cs-001"
    capabilities: ClassVar[list[str]] = ["keyword_detection", "sentiment_analysis"]

    async def process_message(self, message: Message) -> Message:
        raise NotImplementedError("StubAgentB does not process messages")


class StubAgentC(BaseAgent):
    """Stub agent for testing with RU identity."""

    agent_id: ClassVar[str] = "agent-ru-001"
    capabilities: ClassVar[list[str]] = ["keyword_detection"]

    async def process_message(self, message: Message) -> Message:
        raise NotImplementedError("StubAgentC does not process messages")


class TestAgentRegistry:
    """Tests for AgentRegistry class."""

    def test_register_agent(self) -> None:
        registry = AgentRegistry()
        agent = StubAgentA()
        registry.register(agent)
        assert registry.get_agent("agent-tm-001") is agent

    def test_unregister_agent(self) -> None:
        registry = AgentRegistry()
        agent = StubAgentA()
        registry.register(agent)
        registry.unregister("agent-tm-001")
        assert registry.get_agent("agent-tm-001") is None

    def test_get_agent_by_id(self) -> None:
        registry = AgentRegistry()
        agent = StubAgentA()
        registry.register(agent)
        result = registry.get_agent("agent-tm-001")
        assert result is agent
        assert registry.get_agent("nonexistent") is None

    def test_list_all_agents(self) -> None:
        registry = AgentRegistry()
        registry.register(StubAgentA())
        registry.register(StubAgentB())
        agents = registry.list_agents()
        assert len(agents) == 2
        agent_ids = {a["agent_id"] for a in agents}
        assert agent_ids == {"agent-tm-001", "agent-cs-001"}

    def test_get_agents_by_capability(self) -> None:
        registry = AgentRegistry()
        registry.register(StubAgentB())
        registry.register(StubAgentC())
        results = registry.get_agents_by_capability("keyword_detection")
        assert len(results) == 2
        results = registry.get_agents_by_capability("sentiment_analysis")
        assert len(results) == 1

    def test_update_and_get_health(self) -> None:
        registry = AgentRegistry()
        registry.register(StubAgentA())
        health: dict[str, Any] = {"status": "HEALTHY", "uptime_seconds": 120.0}
        registry.update_health("agent-tm-001", health)
        result = registry.get_health("agent-tm-001")
        assert result["status"] == "HEALTHY"

    @pytest.mark.asyncio
    async def test_thread_safe_concurrent_registration(self) -> None:
        registry = AgentRegistry()

        async def register_a() -> None:
            registry.register(StubAgentA())

        async def register_b() -> None:
            registry.register(StubAgentB())

        await asyncio.gather(register_a(), register_b())
        agents = registry.list_agents()
        assert len(agents) == 2

    def test_unregister_nonexistent_agent(self) -> None:
        registry = AgentRegistry()
        with pytest.raises(AgentNotFoundError):
            registry.unregister("nonexistent-agent")
