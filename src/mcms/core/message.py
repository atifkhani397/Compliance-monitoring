"""Pydantic v2 data models for MACMS inter-agent messaging protocol."""

import base64
import re
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from src.mcms.core.exceptions import MessageValidationError

VALID_AGENT_IDS = {
    "agent-tm-001",
    "agent-cs-001",
    "agent-ru-001",
    "agent-rg-001",
}

SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
PAYLOAD_SCHEMA_PATTERN = re.compile(r"^[a-z0-9.-]+$")


class AlertPayload(BaseModel):
    """Payload for ALERT messages."""

    model_config = ConfigDict(extra="forbid")

    violation_type: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    detected_at: str
    evidence_refs: list[str]
    affected_entities: list[str]
    exculpatory: bool = False
    jurisdiction: str | None = None
    regulatory_requirement: str | None = None
    attributed_entity: str | None = None
    cross_jurisdictional: bool = False
    mria: bool = False
    board_level: bool = False
    senior_management: bool = False
    repeated_violation_count: int = Field(default=0, ge=0)
    system_generated_anomaly: bool = False
    sanctions_related: bool = False
    agent_status: Literal["HEALTHY", "DEGRADED", "STOPPED"] | None = None
    conflict_type: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    scenario_context: dict[str, Any] = Field(default_factory=dict)
    consensus_result: dict[str, Any] | None = None

    @field_validator("detected_at")
    @classmethod
    def validate_detected_at(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError as err:
            raise ValueError(f"detected_at must be ISO 8601 timestamp: {v}") from err
        return v


class QueryPayload(BaseModel):
    """Payload for QUERY messages."""

    model_config = ConfigDict(extra="forbid")

    query_type: str
    parameters: dict[str, Any]
    response_schema_required: str


class ConsensusPayload(BaseModel):
    """Consensus result embedded in an UPDATE message."""

    model_config = ConfigDict(extra="forbid")

    consensus_confidence: float = Field(ge=0.0, le=1.0)
    consensus_severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "NO_ALERT"]
    conflict_type: str | None = None
    contributing_agents: list[str]
    dissenting_agents: list[str]
    resolution_method: Literal["bayesian", "dempster_shafer", "hybrid", "escalation"]
    escalation_required: bool
    escalation_reason: str | None = None
    audit_trail_ref: str


class ResponsePayload(BaseModel):
    """Payload for RESPONSE messages."""

    model_config = ConfigDict(extra="forbid")

    query_id: str
    status: Literal["SUCCESS", "PARTIAL", "FAILED"]
    result_data: dict[str, Any]
    errors: list[str]
    resolution_method: Literal["bayesian", "dempster_shafer", "hybrid", "escalation"] | None = None

    @field_validator("query_id")
    @classmethod
    def validate_query_id_uuid(cls, v: str) -> str:
        try:
            val = UUID(v, version=4)
            if str(val) != v.lower():
                raise ValueError("query_id must be canonical UUID v4 string")
        except ValueError as err:
            raise ValueError(f"query_id must be a valid UUID v4 string: {v}") from err
        return v


class HumanDecisionPayload(BaseModel):
    """Human disposition carried by an UPDATE message."""

    model_config = ConfigDict(extra="forbid")

    decision: Literal["approve", "reject", "override", "request_more_info"]
    justification: str
    decided_by: str
    decided_at: str
    confidence_after: float = Field(ge=0.0, le=1.0)


class FeedbackPayload(BaseModel):
    """Labeled feedback carried by an UPDATE message."""

    model_config = ConfigDict(extra="forbid")

    decision_id: str
    alert_id: str
    agent_id: str
    violation_type: str
    human_decision: Literal["approve", "reject", "override", "request_more_info"]
    confidence_before: float = Field(ge=0.0, le=1.0)
    confidence_after: float | None = Field(default=None, ge=0.0, le=1.0)
    justification: str
    timestamp: str


class UpdatePayload(BaseModel):
    """Payload for UPDATE messages."""

    model_config = ConfigDict(extra="forbid")

    update_type: str
    entity_id: str
    changed_fields: dict[str, Any]
    previous_values: dict[str, Any]
    consensus_result: ConsensusPayload | None = None
    human_decision: HumanDecisionPayload | None = None
    feedback: FeedbackPayload | None = None
    reason: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)


class HeartbeatPayload(BaseModel):
    """Payload for HEARTBEAT messages."""

    model_config = ConfigDict(extra="forbid")

    agent_status: Literal["HEALTHY", "DEGRADED", "UNHEALTHY"]
    queue_depth: int = Field(ge=0)
    last_processed_timestamp: str

    @field_validator("last_processed_timestamp")
    @classmethod
    def validate_last_processed(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError as err:
            raise ValueError(f"last_processed_timestamp must be ISO 8601 format: {v}") from err
        return v


class EscalationPayload(BaseModel):
    """Payload for ESCALATION messages."""

    model_config = ConfigDict(extra="forbid")

    escalation_reason: str
    recommended_tier: Literal["TIER_1", "TIER_2", "TIER_3", "TIER_4"]
    decision_support_package_ref: str
    human_assignee_role: str
    conflict_type: str | None = None
    assigned_to: str | None = None
    tier: int | None = Field(default=None, ge=1, le=4)
    sla_deadline: str | None = None
    status: Literal["open", "in_review", "resolved", "auto_escalated", "overridden"] | None = None


PayloadType = (
    AlertPayload
    | QueryPayload
    | ResponsePayload
    | UpdatePayload
    | HeartbeatPayload
    | EscalationPayload
    | ConsensusPayload
    | HumanDecisionPayload
    | FeedbackPayload
    | dict[str, Any]
)


class BaseMessage(BaseModel):
    """Base inter-agent message container model."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    message_id: str = Field(description="UUID v4 message identifier.")
    protocol_version: str = Field(description="Semver version string.")
    timestamp: str = Field(description="ISO 8601 UTC timestamp.")
    sender_agent_id: str = Field(description="Sender agent ID.")
    recipient_agent_id: str | list[str] = Field(description="Single agent ID or list of IDs.")
    message_type: Literal["ALERT", "QUERY", "RESPONSE", "UPDATE", "HEARTBEAT", "ESCALATION"]
    priority: int = Field(ge=1, le=5, description="Priority level 1 to 5.")
    correlation_id: str | None = Field(default=None, description="UUID v4 correlation ID.")
    trace_id: str = Field(description="UUID v4 distributed trace ID.")
    payload_schema: str = Field(description="Pattern matching payload schema.")
    payload: PayloadType = Field(description="Structured message payload dictionary.")
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    ttl_seconds: int = Field(ge=1, le=86400)
    retry_count: int = Field(default=0, ge=0)
    audit_classification: Literal["REGULATORY", "OPERATIONAL", "DIAGNOSTIC"]
    sender_signature: str = Field(min_length=1)
    nonce: str = Field(min_length=16)

    @field_validator("message_id", "trace_id")
    @classmethod
    def validate_uuid_v4(cls, v: str, info: ValidationInfo) -> str:
        try:
            val = UUID(v, version=4)
            if str(val) != v.lower():
                raise ValueError(f"{info.field_name} must be canonical UUID v4 string")
        except ValueError as err:
            raise ValueError(f"{info.field_name} must be a valid UUID v4: {v}") from err
        return v

    @field_validator("correlation_id")
    @classmethod
    def validate_optional_correlation_uuid_v4(cls, v: str | None) -> str | None:
        if v is None:
            return None
        try:
            val = UUID(v, version=4)
            if str(val) != v.lower():
                raise ValueError("correlation_id must be canonical UUID v4 string")
        except ValueError as err:
            raise ValueError(f"correlation_id must be a valid UUID v4: {v}") from err
        return v

    @field_validator("protocol_version")
    @classmethod
    def validate_semver(cls, v: str) -> str:
        if not SEMVER_PATTERN.match(v):
            raise ValueError(f"protocol_version must match semver pattern (X.Y.Z): {v}")
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_iso8601(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError as err:
            raise ValueError(f"timestamp must be valid ISO 8601 date-time: {v}") from err
        return v

    @field_validator("sender_agent_id")
    @classmethod
    def validate_sender_id(cls, v: str) -> str:
        if v not in VALID_AGENT_IDS:
            raise ValueError(
                f"sender_agent_id '{v}' is not in valid agent registry: {VALID_AGENT_IDS}"
            )
        return v

    @field_validator("recipient_agent_id")
    @classmethod
    def validate_recipient_id(cls, v: str | list[str]) -> str | list[str]:
        if isinstance(v, str):
            if v not in VALID_AGENT_IDS:
                raise ValueError(
                    f"recipient_agent_id '{v}' is not in valid agent registry: {VALID_AGENT_IDS}"
                )
        elif isinstance(v, list):
            if not v:
                raise ValueError("recipient_agent_id list cannot be empty")
            for item in v:
                if item not in VALID_AGENT_IDS:
                    raise ValueError(f"recipient_agent_id item '{item}' is not valid agent ID")
        else:
            raise ValueError("recipient_agent_id must be a string or list of strings")
        return v

    @field_validator("payload_schema")
    @classmethod
    def validate_payload_schema_name(cls, v: str) -> str:
        if not PAYLOAD_SCHEMA_PATTERN.match(v):
            raise ValueError(f"payload_schema must match pattern '^[a-z0-9.-]+$': {v}")
        return v

    @field_validator("sender_signature")
    @classmethod
    def validate_base64_sig(cls, v: str) -> str:
        try:
            base64.b64decode(v, validate=True)
        except Exception as err:
            raise ValueError(f"sender_signature must be a valid base64 string: {v}") from err
        return v

    @model_validator(mode="after")
    def validate_conditional_fields_and_payload(self) -> "BaseMessage":
        # Conditional check for confidence_score
        if self.message_type in ("ALERT", "ESCALATION"):
            if self.confidence_score is None:
                raise ValueError(
                    f"confidence_score is required for message_type '{self.message_type}'"
                )
        # Conditional check for correlation_id
        if self.message_type in ("RESPONSE", "UPDATE"):
            if self.correlation_id is None:
                raise ValueError(
                    f"correlation_id is required for message_type '{self.message_type}'"
                )

        # Validate the typed payload matching message_type, then normalize it
        # back to a dictionary to preserve the Phase 1–2 runtime contract.
        try:
            typed_payload: BaseModel
            if self.message_type == "ALERT":
                typed_payload = AlertPayload.model_validate(self.payload)
            elif self.message_type == "QUERY":
                typed_payload = QueryPayload.model_validate(self.payload)
            elif self.message_type == "RESPONSE":
                typed_payload = ResponsePayload.model_validate(self.payload)
            elif self.message_type == "UPDATE":
                typed_payload = UpdatePayload.model_validate(self.payload)
            elif self.message_type == "HEARTBEAT":
                typed_payload = HeartbeatPayload.model_validate(self.payload)
            else:
                typed_payload = EscalationPayload.model_validate(self.payload)
            self.payload = typed_payload.model_dump(mode="json")
        except Exception as err:
            raise MessageValidationError(
                f"Payload validation failed for type '{self.message_type}': {err}",
                details={"message_type": self.message_type, "raw_error": str(err)},
            ) from err

        return self


# Alias Message to BaseMessage for core export contract
Message = BaseMessage
