"""Test cases for MACMS Pydantic v2 Message schema validation."""

import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.mcms.core.message import Message


def create_base_msg_dict(**kwargs) -> dict:
    """Helper returning valid base message dictionary."""
    base = {
        "message_id": str(uuid4()),
        "protocol_version": "1.0.0",
        "timestamp": datetime.now(UTC).isoformat(),
        "sender_agent_id": "agent-tm-001",
        "recipient_agent_id": "agent-cs-001",
        "message_type": "HEARTBEAT",
        "priority": 3,
        "trace_id": str(uuid4()),
        "payload_schema": "heartbeat-v1",
        "payload": {
            "agent_status": "HEALTHY",
            "queue_depth": 0,
            "last_processed_timestamp": datetime.now(UTC).isoformat(),
        },
        "ttl_seconds": 300,
        "retry_count": 0,
        "audit_classification": "OPERATIONAL",
        "sender_signature": "dGVzdC1zaWduYXR1cmU=",
        "nonce": "1234567890123456",
    }
    base.update(kwargs)
    return base


def test_valid_heartbeat_message():
    data = create_base_msg_dict()
    msg = Message.model_validate(data)
    assert msg.message_type == "HEARTBEAT"
    assert msg.sender_agent_id == "agent-tm-001"


def test_valid_alert_message():
    data = create_base_msg_dict(
        message_type="ALERT",
        payload_schema="alert-v1",
        confidence_score=0.95,
        payload={
            "violation_type": "WASH_SALE",
            "severity": "CRITICAL",
            "detected_at": datetime.now(UTC).isoformat(),
            "evidence_refs": ["ref-101", "ref-102"],
            "affected_entities": ["trader-44"],
        },
    )
    msg = Message.model_validate(data)
    assert msg.message_type == "ALERT"
    assert msg.confidence_score == 0.95


def test_valid_query_message():
    data = create_base_msg_dict(
        message_type="QUERY",
        payload_schema="query-v1",
        payload={
            "query_type": "GET_COMMUNICATION_LOGS",
            "parameters": {"trader_id": "trader-44"},
            "response_schema_required": "comms-response-v1",
        },
    )
    msg = Message.model_validate(data)
    assert msg.message_type == "QUERY"


def test_valid_response_message():
    corr_id = str(uuid4())
    data = create_base_msg_dict(
        message_type="RESPONSE",
        payload_schema="response-v1",
        correlation_id=corr_id,
        payload={
            "query_id": str(uuid4()),
            "status": "SUCCESS",
            "result_data": {"logs_found": 3},
            "errors": [],
        },
    )
    msg = Message.model_validate(data)
    assert msg.message_type == "RESPONSE"
    assert msg.correlation_id == corr_id


def test_valid_update_message():
    corr_id = str(uuid4())
    data = create_base_msg_dict(
        message_type="UPDATE",
        payload_schema="update-v1",
        correlation_id=corr_id,
        payload={
            "update_type": "POLICY_CHANGE",
            "entity_id": "policy-909",
            "changed_fields": {"max_threshold": 10000},
            "previous_values": {"max_threshold": 5000},
        },
    )
    msg = Message.model_validate(data)
    assert msg.message_type == "UPDATE"


def test_valid_escalation_message():
    data = create_base_msg_dict(
        message_type="ESCALATION",
        payload_schema="escalation-v1",
        confidence_score=0.88,
        payload={
            "escalation_reason": "High probability front-running detected",
            "recommended_tier": "TIER_2",
            "decision_support_package_ref": "dsp-7781",
            "human_assignee_role": "Senior Compliance Officer",
        },
    )
    msg = Message.model_validate(data)
    assert msg.message_type == "ESCALATION"


def test_invalid_uuid_rejection():
    data = create_base_msg_dict(message_id="invalid-uuid-string")
    with pytest.raises(ValidationError):
        Message.model_validate(data)


def test_invalid_semver_rejection():
    data = create_base_msg_dict(protocol_version="v1.0")
    with pytest.raises(ValidationError):
        Message.model_validate(data)


def test_missing_required_field_rejection():
    data = create_base_msg_dict()
    del data["ttl_seconds"]
    with pytest.raises(ValidationError):
        Message.model_validate(data)


def test_confidence_score_out_of_range_rejection():
    data = create_base_msg_dict(
        message_type="ALERT",
        payload_schema="alert-v1",
        confidence_score=1.5,
        payload={
            "violation_type": "SPOOFING",
            "severity": "HIGH",
            "detected_at": datetime.now(UTC).isoformat(),
            "evidence_refs": [],
            "affected_entities": [],
        },
    )
    with pytest.raises(ValidationError):
        Message.model_validate(data)


def test_confidence_score_missing_for_alert_rejection():
    data = create_base_msg_dict(
        message_type="ALERT",
        payload_schema="alert-v1",
        confidence_score=None,
        payload={
            "violation_type": "SPOOFING",
            "severity": "HIGH",
            "detected_at": datetime.now(UTC).isoformat(),
            "evidence_refs": [],
            "affected_entities": [],
        },
    )
    with pytest.raises(ValidationError):
        Message.model_validate(data)


def test_correlation_id_missing_for_response_rejection():
    data = create_base_msg_dict(
        message_type="RESPONSE",
        payload_schema="response-v1",
        correlation_id=None,
        payload={
            "query_id": str(uuid4()),
            "status": "SUCCESS",
            "result_data": {},
            "errors": [],
        },
    )
    with pytest.raises(ValidationError):
        Message.model_validate(data)


def test_invalid_priority_level_rejection():
    data = create_base_msg_dict(priority=6)
    with pytest.raises(ValidationError):
        Message.model_validate(data)


def test_invalid_message_type_rejection():
    data = create_base_msg_dict(message_type="INVALID_TYPE")
    with pytest.raises(ValidationError):
        Message.model_validate(data)


def test_invalid_audit_classification_rejection():
    data = create_base_msg_dict(audit_classification="UNKNOWN")
    with pytest.raises(ValidationError):
        Message.model_validate(data)


def test_base64_signature_validation_failure():
    data = create_base_msg_dict(sender_signature="!!!NotBase64!!!")
    with pytest.raises(ValidationError):
        Message.model_validate(data)


def test_timestamp_format_validation_failure():
    data = create_base_msg_dict(timestamp="Monday, 17 Aug 2026")
    with pytest.raises(ValidationError):
        Message.model_validate(data)


def test_multicast_recipient_list_valid():
    data = create_base_msg_dict(recipient_agent_id=["agent-cs-001", "agent-rg-001"])
    msg = Message.model_validate(data)
    assert isinstance(msg.recipient_agent_id, list)
    assert len(msg.recipient_agent_id) == 2


def test_model_json_schema_export_compatibility():
    schema = Message.model_json_schema()
    assert "properties" in schema
    assert "message_id" in schema["properties"]
    assert "priority" in schema["properties"]
    # Programmatic JSON serialization check
    json_str = json.dumps(schema)
    assert len(json_str) > 100
