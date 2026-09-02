"""Core infrastructure, messaging, routing, audit, orchestrator, registry, and config modules for MACMS."""

from src.mcms.core.audit import AuditChain, AuditEntry
from src.mcms.core.config import Config
from src.mcms.core.exceptions import (
    AgentNotFoundError,
    AgentTimeoutError,
    AuditIntegrityError,
    CapabilityNotFoundError,
    ConfigError,
    KafkaConnectionError,
    MCMSException,
    MessageValidationError,
    OrchestratorError,
    RoutingError,
    SecurityError,
)
from src.mcms.core.kafka_client import KafkaConsumer, KafkaProducer, build_topic_name
from src.mcms.core.message import BaseMessage, Message
from src.mcms.core.orchestrator import Orchestrator
from src.mcms.core.registry import AgentRegistry
from src.mcms.core.routing import PriorityRoutingEngine
from src.mcms.core.security import SecurityManager

__all__ = [
    "AgentNotFoundError",
    "AgentRegistry",
    "AgentTimeoutError",
    "AuditChain",
    "AuditEntry",
    "AuditIntegrityError",
    "BaseMessage",
    "CapabilityNotFoundError",
    "Config",
    "ConfigError",
    "KafkaConnectionError",
    "KafkaConsumer",
    "KafkaProducer",
    "MCMSException",
    "Message",
    "MessageValidationError",
    "Orchestrator",
    "OrchestratorError",
    "PriorityRoutingEngine",
    "RoutingError",
    "SecurityError",
    "SecurityManager",
    "build_topic_name",
]
