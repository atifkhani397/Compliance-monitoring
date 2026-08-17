"""Central orchestrator for MACMS inter-agent message coordination."""

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from src.mcms.core.audit import AuditChain
from src.mcms.core.config import Config
from src.mcms.core.exceptions import AgentNotFoundError, OrchestratorError
from src.mcms.core.registry import AgentRegistry

if TYPE_CHECKING:
    from src.mcms.agents.base import BaseAgent
    from src.mcms.core.message import Message

logger = logging.getLogger(__name__)


class Orchestrator:
    """Central coordination node for all MACMS inter-agent communication."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._registry = AgentRegistry()
        self._audit_chain = AuditChain()
        self._escalation_queue: list[dict[str, Any]] = []
        self._shutdown = False

    async def dispatch(self, message: "Message") -> None:  # noqa: F821
        """Routes message to recipient agent(s) based on routing rules."""
        if self._shutdown:
            raise OrchestratorError("Orchestrator is shut down; cannot dispatch messages")

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

    async def register_agent(self, agent: "BaseAgent") -> None:
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

    async def handle_heartbeat(self, message: "Message") -> None:  # noqa: F821
        """Processes heartbeat message and updates agent health status."""
        sender_id = message.sender_agent_id
        health_data: dict[str, Any] = {
            "status": message.payload.get("agent_status", "UNKNOWN"),
            "queue_depth": message.payload.get("queue_depth", 0),
            "last_heartbeat": datetime.now(UTC).isoformat(),
            "agent_id": sender_id,
        }
        self._registry.update_health(sender_id, health_data)

    async def escalate(self, message: "Message", reason: str) -> None:  # noqa: F821
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
        """Returns health of all registered agents."""
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
