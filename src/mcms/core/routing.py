"""Priority-based inter-agent message routing engine for MACMS."""

import asyncio
from collections import defaultdict

from src.mcms.core.exceptions import RoutingError
from src.mcms.core.message import VALID_AGENT_IDS, Message

PRIORITY_SLAS = {
    1: 300,  # P1-CRITICAL: < 5 minutes
    2: 900,  # P2-HIGH: < 15 minutes
    3: 3600,  # P3-MEDIUM: < 1 hour
    4: 14400,  # P4-LOW: < 4 hours
    5: 86400,  # P5-INFORMATIONAL: < 24 hours
}


class PriorityRoutingEngine:
    """Manages message queuing, priority ordering, multicast distribution, and DLQ routing."""

    def __init__(self, max_queue_depth: int = 1000, max_retries: int = 3) -> None:
        self.max_queue_depth = max_queue_depth
        self.max_retries = max_retries
        self._counter = 0
        # Inbound queues keyed by agent_id containing PriorityQueue items: (priority, count, message)
        self._queues: dict[str, asyncio.PriorityQueue[tuple[int, int, Message]]] = defaultdict(
            asyncio.PriorityQueue
        )
        self._dead_letter_queue: list[dict[str, Message | str]] = []

    def get_queue_depth(self, agent_id: str) -> int:
        """Returns current queue depth for specified agent."""
        if agent_id not in self._queues:
            return 0
        return self._queues[agent_id].qsize()

    def is_backpressure_triggered(self, agent_id: str) -> bool:
        """Checks if agent's queue depth exceeds back-pressure threshold."""
        return self.get_queue_depth(agent_id) >= self.max_queue_depth

    async def route_message(self, message: Message) -> list[str]:
        """Routes message to destination queue(s). Supports single agent ID or multicast list.

        Returns list of recipient agent IDs successfully queued.
        Raises RoutingError if recipient is invalid or backpressure rejects delivery.
        """
        recipients = (
            [message.recipient_agent_id]
            if isinstance(message.recipient_agent_id, str)
            else message.recipient_agent_id
        )

        for recipient in recipients:
            if recipient not in VALID_AGENT_IDS:
                raise RoutingError(f"Invalid recipient agent ID: {recipient}")

            if self.is_backpressure_triggered(recipient):
                raise RoutingError(
                    f"Back-pressure limit reached for agent {recipient} (depth: {self.get_queue_depth(recipient)})",
                    retry_count=message.retry_count,
                    dead_letter_queue=True,
                )

            # Check retry count threshold for DLQ
            if message.retry_count > self.max_retries:
                self._send_to_dlq(message, f"Exceeded max retries ({self.max_retries})")
                raise RoutingError(
                    f"Message {message.message_id} exceeded max retries and was sent to DLQ",
                    retry_count=message.retry_count,
                    dead_letter_queue=True,
                )

            self._counter += 1
            # PriorityQueue sorts items naturally; lower number = higher priority (1 = P1-CRITICAL)
            await self._queues[recipient].put((message.priority, self._counter, message))

        return recipients

    async def pop_next_message(self, agent_id: str, timeout: float = 1.0) -> Message | None:
        """Pops the highest-priority message for the specified agent.

        Returns None if queue is empty or operation times out.
        """
        if agent_id not in self._queues or self._queues[agent_id].empty():
            return None

        try:
            _, _, message = await asyncio.wait_for(self._queues[agent_id].get(), timeout=timeout)
            return message
        except TimeoutError:
            return None

    def _send_to_dlq(self, message: Message, reason: str) -> None:
        """Routes unroutable message to Dead Letter Queue."""
        self._dead_letter_queue.append({"message": message, "reason": reason})

    def get_dlq_entries(self) -> list[dict[str, Message | str]]:
        """Returns copies of all entries in the Dead Letter Queue."""
        return list(self._dead_letter_queue)
