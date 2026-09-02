"""Thread-safe agent registry service for MACMS."""

import asyncio
from typing import TYPE_CHECKING, Any

from src.mcms.core.exceptions import AgentNotFoundError

if TYPE_CHECKING:
    from src.mcms.agents.base import BaseAgent


class AgentRegistry:
    """In-memory agent registry with capability search and health tracking."""

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}
        self._health: dict[str, dict[str, Any]] = {}
        self._lock: asyncio.Lock = asyncio.Lock()

    def register(self, agent: "BaseAgent") -> None:
        """Adds agent to registry."""

        self._agents[agent.agent_id] = agent
        self._health[agent.agent_id] = agent.health_check()

    def unregister(self, agent_id: str) -> None:
        """Removes agent from registry."""
        if agent_id not in self._agents:
            raise AgentNotFoundError(agent_id)
        del self._agents[agent_id]
        self._health.pop(agent_id, None)

    def get_agent(self, agent_id: str) -> "BaseAgent | None":
        """Retrieves agent instance by ID."""
        return self._agents.get(agent_id)

    def list_agents(self) -> list[dict[str, Any]]:
        """Returns all registered agents with metadata."""
        result: list[dict[str, Any]] = []
        for agent_id, agent in self._agents.items():
            capabilities: list[str] = getattr(agent, "capabilities", [])
            result.append(
                {
                    "agent_id": agent_id,
                    "class": agent.__class__.__name__,
                    "status": agent.status,
                    "capabilities": capabilities,
                }
            )
        return result

    def get_agents_by_capability(self, capability: str) -> "list[BaseAgent]":
        """Finds agents supporting a capability."""
        results: list[BaseAgent] = []
        for agent in self._agents.values():
            caps: list[str] = getattr(agent, "capabilities", [])
            if capability in caps:
                results.append(agent)
        return results

    def update_health(self, agent_id: str, health: dict[str, Any]) -> None:
        """Updates health status for an agent."""
        if agent_id in self._agents:
            self._health[agent_id] = health

    def get_health(self, agent_id: str) -> dict[str, Any]:
        """Returns health status for an agent."""
        return self._health.get(agent_id, {})
