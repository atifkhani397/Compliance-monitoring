"""Custom exception classes for the Multi-Agent Compliance Monitoring System (MACMS)."""

from typing import Any


class MCMSException(Exception):
    """Base exception for all MACMS errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class MessageValidationError(MCMSException):
    """Raised when a message fails JSON Schema or Pydantic validation rules."""


class RoutingError(MCMSException):
    """Raised when message routing fails due to queue saturation, unroutable destination, or invalid recipient."""

    def __init__(
        self,
        message: str,
        retry_count: int = 0,
        dead_letter_queue: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details)
        self.retry_count = retry_count
        self.dead_letter_queue = dead_letter_queue


class SecurityError(MCMSException):
    """Raised when signature verification fails, mTLS authentication fails, or unauthorized access is detected."""


class AgentTimeoutError(MCMSException):
    """Raised when an agent operation exceeds its designated TTL or processing SLA."""


class AuditIntegrityError(MCMSException):
    """Raised when cryptographic hash-chain verification detects log tampering or broken hash linkage."""

    def __init__(
        self, message: str, entry_index: int, details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message, details)
        self.entry_index = entry_index


class AgentNotFoundError(MCMSException):
    """Raised when dispatching to an unregistered agent."""

    def __init__(self, agent_id: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(f"Agent not found in registry: {agent_id}", details)
        self.agent_id = agent_id


class OrchestratorError(MCMSException):
    """Base exception for orchestrator failures."""


class KafkaConnectionError(MCMSException):
    """Raised when Kafka client cannot connect."""

    def __init__(
        self,
        message: str,
        bootstrap_servers: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details)
        self.bootstrap_servers = bootstrap_servers or []


class ConfigError(MCMSException):
    """Raised when configuration is invalid or missing required fields."""


class CapabilityNotFoundError(MCMSException):
    """Raised when no agent supports a requested capability."""

    def __init__(self, capability: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(f"No agent found with capability: {capability}", details)
        self.capability = capability


class ConsensusError(MCMSException):
    """Base exception for deterministic consensus failures."""


class ConflictDetectionError(ConsensusError):
    """Raised when a group of alerts cannot be classified as a supported conflict."""


class ConvergenceError(ConsensusError):
    """Raised when Bayesian and Dempster-Shafer results diverge beyond the limit."""


class InvalidAssessmentError(ConsensusError):
    """Raised when an agent assessment violates the consensus input contract."""


class EscalationError(MCMSException):
    """Base exception for human-in-the-loop escalation failures."""


class AssignmentError(EscalationError):
    """Raised when no suitable available human can be assigned."""


class SlaViolationError(EscalationError):
    """Raised when an escalation exceeds its service-level agreement."""


class OverrideDeniedError(EscalationError):
    """Raised when an override lacks authority, justification, or approval."""


class FeedbackError(EscalationError):
    """Raised when feedback data is malformed or cannot be recorded."""


class ObservabilityError(MCMSException):
    """Base exception for structured observability failures."""


class MetricsError(ObservabilityError):
    """Raised when a metric cannot be recorded or queried."""


class DashboardError(ObservabilityError):
    """Raised when dashboard data cannot be retrieved."""
