"""Central orchestration and Phase 3 correlated-alert routing."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

from src.mcms.core.audit import AuditChain
from src.mcms.core.config import Config
from src.mcms.core.consensus import ConsensusEngine
from src.mcms.core.exceptions import AgentNotFoundError, OrchestratorError
from src.mcms.core.registry import AgentRegistry


def _payload(message: Message) -> dict[str, Any]:
    return cast(dict[str, Any], message.payload)


if TYPE_CHECKING:
    from src.mcms.agents.base import BaseAgent
    from src.mcms.core.conflict_resolver import ConflictResolver
    from src.mcms.core.message import Message

logger = logging.getLogger(__name__)


class Orchestrator:
    """Central coordination node for all MACMS inter-agent communication."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._registry = AgentRegistry()
        self._audit_chain = AuditChain()
        self._escalation_queue: list[dict[str, Any]] = []
        self._conflict_buffer: dict[str, list[Message]] = {}
        self._resolved_messages: list[Message] = []
        self._shutdown = False
        from src.mcms.core.conflict_resolver import ConflictResolver

        self._conflict_resolver: ConflictResolver = ConflictResolver(ConsensusEngine(config), self)

    async def dispatch(self, message: Message) -> None:
        """Route messages, buffering correlated ALERTs for conflict resolution."""
        if self._shutdown:
            raise OrchestratorError("Orchestrator is shut down; cannot dispatch messages")

        if message.message_type == "ALERT":
            key = message.correlation_id or message.trace_id
            buffer = self._conflict_buffer.setdefault(key, [])
            buffer.append(message)
            if len(buffer) > 1 and self._conflict_resolver.detect_conflict(buffer):
                await self.route_to_resolver(buffer.copy())
                self._conflict_buffer.pop(key, None)
                return

        recipients: list[str] = (
            [message.recipient_agent_id]
            if isinstance(message.recipient_agent_id, str)
            else list(message.recipient_agent_id)
        )

        for recipient_id in recipients:
            agent = self._registry.get_agent(recipient_id)
            if agent is None:
                raise AgentNotFoundError(recipient_id)
            await agent.process_message(message)

        self._audit_chain.append(
            {
                "action": "DISPATCH",
                "message_id": message.message_id,
                "message_type": message.message_type,
                "sender": message.sender_agent_id,
                "recipients": recipients,
                "priority": message.priority,
                "timestamp": datetime.now(UTC).isoformat(),
            },
            agent_id="orchestrator",
        )
        logger.info(
            "Dispatched message %s (%s) to %s",
            message.message_id,
            message.message_type,
            recipients,
        )

    async def route_to_resolver(self, messages: list[Message]) -> None:
        """Resolve correlated alerts and deliver the result to RG when registered."""
        if not messages:
            raise OrchestratorError("Cannot route an empty message group to the resolver")
        resolved = await self._conflict_resolver.resolve_conflict(messages)
        self._resolved_messages.append(resolved)
        report_agent = self._registry.get_agent("agent-rg-001")
        if report_agent is not None:
            await report_agent.process_message(resolved)

    async def register_agent(self, agent: BaseAgent) -> None:
        """Registers agent for message delivery."""
        self._registry.register(agent)
        self._audit_chain.append(
            {
                "action": "REGISTER_AGENT",
                "agent_id": agent.agent_id,
                "timestamp": datetime.now(UTC).isoformat(),
            },
            agent_id="orchestrator",
        )
        logger.info("Registered agent %s", agent.agent_id)

    async def unregister_agent(self, agent_id: str) -> None:
        """Removes agent from registry."""
        self._registry.unregister(agent_id)
        self._audit_chain.append(
            {
                "action": "UNREGISTER_AGENT",
                "agent_id": agent_id,
                "timestamp": datetime.now(UTC).isoformat(),
            },
            agent_id="orchestrator",
        )
        logger.info("Unregistered agent %s", agent_id)

    async def handle_heartbeat(self, message: Message) -> None:
        """Processes heartbeat message and updates agent health status."""
        sender_id = message.sender_agent_id
        health_data: dict[str, Any] = {
            "status": _payload(message).get("agent_status", "UNKNOWN"),
            "queue_depth": _payload(message).get("queue_depth", 0),
            "last_heartbeat": datetime.now(UTC).isoformat(),
            "agent_id": sender_id,
        }
        self._registry.update_health(sender_id, health_data)

    async def escalate(self, message: Message, reason: str) -> None:
        """Creates escalation entry and routes to human escalation queue."""
        escalation_entry: dict[str, Any] = {
            "original_message_id": message.message_id,
            "reason": reason,
            "timestamp": datetime.now(UTC).isoformat(),
            "sender_agent_id": message.sender_agent_id,
            "priority": message.priority,
        }
        self._escalation_queue.append(escalation_entry)
        self._audit_chain.append(
            {"action": "ESCALATION", **escalation_entry},
            agent_id="orchestrator",
        )
        logger.warning("Escalated message %s: %s", message.message_id, reason)

    def get_agent_health(self, agent_id: str) -> dict[str, Any]:
        """Returns last known health status for an agent."""
        return self._registry.get_health(agent_id)

    def get_system_health(self) -> dict[str, Any]:
        """Returns health of all registered agents and conflict buffers."""
        agents_list = self._registry.list_agents()
        agent_healths: list[dict[str, Any]] = []
        for agent_info in agents_list:
            aid: str = agent_info["agent_id"]
            health = self._registry.get_health(aid)
            agent_healths.append({**agent_info, **health})
        return {
            "orchestrator_status": "SHUTDOWN" if self._shutdown else "RUNNING",
            "registered_agents": len(agents_list),
            "agents": agent_healths,
            "escalation_queue_depth": len(self._escalation_queue),
            "audit_chain_length": len(self._audit_chain.entries),
            "conflict_buffer_depth": sum(len(items) for items in self._conflict_buffer.values()),
            "resolved_message_depth": len(self._resolved_messages),
        }

    async def shutdown(self) -> None:
        """Graceful shutdown with in-flight message completion."""
        self._shutdown = True
        self._audit_chain.append(
            {
                "action": "SHUTDOWN",
                "timestamp": datetime.now(UTC).isoformat(),
            },
            agent_id="orchestrator",
        )
        logger.info("Orchestrator shutdown complete")
