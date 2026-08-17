"""Abstract Base Agent class for MACMS agents."""

import abc
import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import uuid4

from src.mcms.core.exceptions import SecurityError
from src.mcms.core.message import Message


class BaseAgent(abc.ABC):
    """Abstract base class establishing identity, health metrics, signing, and messaging contracts."""

    agent_id: ClassVar[str] = "agent-base-000"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.secret_key: str = self.config.get("secret_key", "default-macms-agent-secret-key-2026")
        self.start_time: float = time.time()
        self.last_processed_timestamp: str = datetime.now(UTC).isoformat()
        self.processed_count: int = 0
        self.outbound_queue: list[Message] = []
        self.status: str = "HEALTHY"

    @abc.abstractmethod
    async def process_message(self, message: Message) -> Message:
        """Abstract message processing handler. Must be implemented by concrete agent subclasses."""
        raise NotImplementedError("Subclasses must implement process_message")

    async def send_message(self, message: Message) -> None:
        """Places message on agent's outbound transmission buffer after verifying signature."""
        if not self.verify_signature(message):
            raise SecurityError(
                f"Cannot send message {message.message_id}: signature verification failed for agent {self.agent_id}"
            )
        self.outbound_queue.append(message)

    def _canonical_message_string(self, message: Message) -> str:
        """Computes deterministic canonical string representation of message fields for HMAC signing."""
        fields = [
            message.message_id,
            message.protocol_version,
            message.timestamp,
            message.sender_agent_id,
            json.dumps(message.recipient_agent_id, sort_keys=True),
            message.message_type,
            str(message.priority),
            message.trace_id,
            message.payload_schema,
            json.dumps(message.payload, sort_keys=True),
            message.nonce,
        ]
        return "|".join(fields)

    def sign_message(self, message: Message) -> str:
        """Calculates HMAC-SHA256 signature for message using agent secret key."""
        canonical_str = self._canonical_message_string(message)
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            canonical_str.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return base64.b64encode(signature).decode("utf-8")

    def verify_signature(self, message: Message) -> bool:
        """Verifies HMAC-SHA256 signature against computed value."""
        expected = self.sign_message(message)
        return hmac.compare_digest(expected, message.sender_signature)

    def heartbeat(self) -> Message:
        """Generates a valid signed HEARTBEAT message reflecting current agent state."""
        msg_id = str(uuid4())
        trace_id = str(uuid4())
        now_str = datetime.now(UTC).isoformat()
        nonce_str = secrets.token_hex(8)

        payload_dict = {
            "agent_status": self.status
            if self.status in ("HEALTHY", "DEGRADED", "UNHEALTHY")
            else "HEALTHY",
            "queue_depth": len(self.outbound_queue),
            "last_processed_timestamp": self.last_processed_timestamp,
        }

        # Create unsigned base model dictionary
        msg_dict = {
            "message_id": msg_id,
            "protocol_version": "1.0.0",
            "timestamp": now_str,
            "sender_agent_id": self.agent_id,
            "recipient_agent_id": self.agent_id,
            "message_type": "HEARTBEAT",
            "priority": 5,
            "trace_id": trace_id,
            "payload_schema": "heartbeat-v1",
            "payload": payload_dict,
            "ttl_seconds": 60,
            "retry_count": 0,
            "audit_classification": "DIAGNOSTIC",
            "sender_signature": "cGxhY2Vob2xkZXI=",
            "nonce": nonce_str,
        }

        temp_msg = Message.model_validate(msg_dict)
        signature = self.sign_message(temp_msg)
        msg_dict["sender_signature"] = signature

        return Message.model_validate(msg_dict)

    def health_check(self) -> dict[str, Any]:
        """Returns standard health check metrics dictionary."""
        uptime = round(time.time() - self.start_time, 2)
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "uptime_seconds": uptime,
            "queue_depth": len(self.outbound_queue),
            "processed_count": self.processed_count,
            "last_processed_timestamp": self.last_processed_timestamp,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} agent_id='{self.agent_id}' status='{self.status}'>"
