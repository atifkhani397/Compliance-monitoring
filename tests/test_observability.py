from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.mcms.core.exceptions import AuditIntegrityError
from src.mcms.core.observability import ObservabilityService


def make_service(tmp_path: object) -> ObservabilityService:
    path = str(tmp_path) + "/audit.jsonl"
    return ObservabilityService({"log_path": path, "agent_keys": {"agent-tm-001": "test-key"}})


def test_log_structured_message(tmp_path: object) -> None:
    service = make_service(tmp_path)
    entry = service.log(
        "DETECTION_EVENTS",
        "ALERT",
        "Pattern detected",
        {"agent_id": "agent-tm-001", "confidence": 0.92},
    )
    assert entry.trace_id is not None
    assert entry.signature is not None
    assert service.logs[0]["log_category"] == "DETECTION_EVENTS"


def test_log_agent_lifecycle_event(tmp_path: object) -> None:
    service = make_service(tmp_path)
    entry = service.log_agent_lifecycle("agent-tm-001", "started", {"status": "HEALTHY"})
    assert entry.action_type == "AGENT_LIFECYCLE"


def test_log_detection_event(tmp_path: object) -> None:
    service = make_service(tmp_path)
    entry = service.log_detection("agent-tm-001", "spoofing", 0.92, ["evidence-1"])
    assert entry.data["context"]["violation_type"] == "spoofing"


def test_log_escalation_event(tmp_path: object) -> None:
    service = make_service(tmp_path)
    escalation_id = uuid4()
    entry = service.log_escalation(escalation_id, "created", {"tier": 2})
    assert entry.data["context"]["escalation_id"] == str(escalation_id)


def test_log_human_decision_event(tmp_path: object) -> None:
    service = make_service(tmp_path)
    entry = service.log_human_decision(uuid4(), "analyst-1", "approve", "Evidence reviewed")
    assert entry.data["context"]["decision"] == "approve"


def test_query_audit_trail_by_trace_id(tmp_path: object) -> None:
    service = make_service(tmp_path)
    trace = str(uuid4())
    service.log("COMMUNICATION_EVENTS", "INFO", "sent", {"agent_id": "agent-tm-001"}, trace)
    entries = service.get_audit_trail(
        trace,
        None,
        datetime.now(UTC) - timedelta(minutes=1),
        datetime.now(UTC) + timedelta(minutes=1),
    )
    assert len(entries) == 1


def test_query_audit_trail_by_agent_id(tmp_path: object) -> None:
    service = make_service(tmp_path)
    service.log("AGENT_LIFECYCLE", "INFO", "started", {"agent_id": "agent-tm-001"})
    entries = service.get_audit_trail(
        None,
        "agent-tm-001",
        datetime.now(UTC) - timedelta(minutes=1),
        datetime.now(UTC) + timedelta(minutes=1),
    )
    assert len(entries) == 1


def test_query_audit_trail_by_date_range(tmp_path: object) -> None:
    service = make_service(tmp_path)
    service.log("SECURITY_EVENTS", "WARN", "access", {"agent_id": "system"})
    entries = service.get_audit_trail(
        None, None, datetime.now(UTC) - timedelta(hours=1), datetime.now(UTC) + timedelta(hours=1)
    )
    assert len(entries) == 1


def test_verify_audit_integrity_valid_chain(tmp_path: object) -> None:
    service = make_service(tmp_path)
    service.log("COMMUNICATION_EVENTS", "INFO", "sent", {"agent_id": "agent-tm-001"})
    assert (
        service.verify_audit_integrity(datetime.now(UTC) - timedelta(days=1), datetime.now(UTC))
        is True
    )


def test_verify_audit_integrity_tampered_chain_fails(tmp_path: object) -> None:
    service = make_service(tmp_path)
    service.log("COMMUNICATION_EVENTS", "INFO", "sent", {"agent_id": "agent-tm-001"})
    service.audit_chain._entries[0].data["message"] = "tampered"
    with pytest.raises(AuditIntegrityError):
        service.verify_audit_integrity(datetime.now(UTC) - timedelta(days=1), datetime.now(UTC))


def test_export_audit_to_jsonl(tmp_path: object) -> None:
    service = make_service(tmp_path)
    service.log("REPORT_GENERATION", "INFO", "report", {"agent_id": "system"})
    exported = service.export_audit(
        datetime.now(UTC) - timedelta(days=1), datetime.now(UTC), "jsonl"
    )
    assert '"action_type": "REPORT_GENERATION"' in exported


def test_get_dashboard_data_for_each_panel(tmp_path: object) -> None:
    service = make_service(tmp_path)
    service.log_agent_lifecycle("agent-tm-001", "started", {"status": "HEALTHY"})
    service.log_detection("agent-tm-001", "spoofing", 0.92, ["evidence-1"])
    service.log_escalation(uuid4(), "created", {"tier": 2, "conflict_type": "A"})
    assert service.get_dashboard_data("system_health", "24h")["panel"] == "system_health"
    assert (
        service.get_dashboard_data("compliance_effectiveness", "24h")["panel"]
        == "compliance_effectiveness"
    )
    assert (
        service.get_dashboard_data("operational_intelligence", "24h")["panel"]
        == "operational_intelligence"
    )
