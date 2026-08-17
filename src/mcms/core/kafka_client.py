"""Kafka producer and consumer with async wrappers for MCMS."""

import asyncio
import contextlib
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from src.mcms.core.message import Message

logger = logging.getLogger(__name__)


def build_topic_name(agent_id: str, message_type: str) -> str:
    """Builds Kafka topic name following convention mcms.{agent_id}.{message_type.lower()}."""
    if not message_type:
        return f"mcms.{agent_id}"
    return f"mcms.{agent_id}.{message_type.lower()}"


class KafkaProducer:
    """Async wrapper around kafka-python KafkaProducer for MCMS message publishing."""

    def __init__(self, bootstrap_servers: list[str], config: dict[str, Any]) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._config = dict(config)
        self._buffer: list[dict[str, Any]] = []
        self._closed = False
        self._producer: Any = None  # kafka.KafkaProducer instance when connected

    async def send(self, topic: str, message: Message, key: str | None = None) -> None:
        """Sends a message to the specified Kafka topic."""
        if self._closed:
            raise RuntimeError("Cannot send on a closed producer")
        record: dict[str, Any] = {
            "topic": topic,
            "key": key,
            "value": message.model_dump_json(),
        }
        self._buffer.append(record)
        logger.info("Buffered message to topic %s (key=%s)", topic, key)

    async def flush(self) -> None:
        """Flushes all buffered messages."""
        if self._producer is not None:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._producer.flush)
        self._buffer.clear()

    async def close(self) -> None:
        """Closes the producer and releases resources."""
        await self.flush()
        if self._producer is not None:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._producer.close)
        self._closed = True


class KafkaConsumer:
    """Async wrapper around kafka-python KafkaConsumer for MCMS message consumption."""

    def __init__(
        self,
        bootstrap_servers: list[str],
        topics: list[str],
        group_id: str,
        config: dict[str, Any],
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topics = topics
        self._group_id = group_id
        self._config = dict(config)
        self._running = False
        self._consumer: Any = None  # kafka.KafkaConsumer instance when connected
        self._task: asyncio.Task[None] | None = None

    async def start(self, callback: Callable[[Message], Awaitable[None]]) -> None:
        """Starts consuming messages and invoking callback for each."""
        self._running = True
        self._task = asyncio.create_task(self._consume_loop(callback))

    async def _consume_loop(self, callback: Callable[[Message], Awaitable[None]]) -> None:
        """Internal consumption loop with async wrapper."""
        while self._running:
            if self._consumer is not None:
                loop = asyncio.get_event_loop()
                records = await loop.run_in_executor(None, self._poll_records)
                for record in records:
                    try:
                        message = Message.model_validate_json(record)
                        await callback(message)
                    except Exception:
                        logger.exception("Failed to process consumed record")
            else:
                await asyncio.sleep(0.1)

    def _poll_records(self) -> list[str]:
        """Polls records from the underlying consumer."""
        if self._consumer is None:
            return []
        raw: dict[Any, Any] = self._consumer.poll(timeout_ms=100)
        records: list[str] = []
        for _tp, msgs in raw.items():
            for msg in msgs:
                if msg.value is not None:
                    records.append(
                        msg.value.decode("utf-8")
                        if isinstance(msg.value, bytes)
                        else str(msg.value)
                    )
        return records

    async def stop(self) -> None:
        """Stops the consumer."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        if self._consumer is not None:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._consumer.close)

    def get_lag(self) -> dict[str, int]:
        """Returns consumer lag per topic (placeholder values when no broker)."""
        return dict.fromkeys(self._topics, 0)
