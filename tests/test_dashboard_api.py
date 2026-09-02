from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from src.mcms.api import dashboard
from src.mcms.core.observability import ObservabilityService

API_KEY = "macms-phase5-api-key"


def client_with_data(tmp_path: object) -> TestClient:
    dashboard.observability = ObservabilityService({"log_path": str(tmp_path) + "/api-audit.jsonl"})
    dashboard.observability.log_agent_lifecycle("agent-tm-001", "started", {"status": "HEALTHY"})
    dashboard.observability.log_detection("agent-tm-001", "spoofing", 0.9, ["evidence"])
    dashboard.observability.log_escalation(uuid4(), "created", {"tier": 2, "conflict_type": "A"})
    return TestClient(dashboard.app)


def headers() -> dict[str, str]:
    return {"X-API-Key": API_KEY}


def test_system_health_endpoint(tmp_path: object) -> None:
    response = client_with_data(tmp_path).get("/health/system", headers=headers())
    assert response.status_code == 200
    assert response.json()["panel"] == "system_health"


def test_agent_health_endpoint(tmp_path: object) -> None:
    response = client_with_data(tmp_path).get("/health/agents/agent-tm-001", headers=headers())
    assert response.status_code == 200
    assert response.json()["agent_id"] == "agent-tm-001"


def test_detection_rate_endpoint(tmp_path: object) -> None:
    response = client_with_data(tmp_path).get("/compliance/detection-rate", headers=headers())
    assert response.status_code == 200
    assert "detection_rate_by_violation" in response.json()


def test_false_positive_rate_endpoint(tmp_path: object) -> None:
    response = client_with_data(tmp_path).get("/compliance/false-positive-rate", headers=headers())
    assert response.status_code == 200
    assert "false_positive_rate_by_violation" in response.json()


def test_time_to_detection_endpoint(tmp_path: object) -> None:
    response = client_with_data(tmp_path).get("/compliance/time-to-detection", headers=headers())
    assert response.status_code == 200
    assert "time_to_detection" in response.json()


def test_escalation_volume_endpoint(tmp_path: object) -> None:
    response = client_with_data(tmp_path).get("/operations/escalations", headers=headers())
    assert response.status_code == 200
    assert response.json()["escalation_volume_by_tier"]["2"] == 1


def test_human_patterns_endpoint(tmp_path: object) -> None:
    response = client_with_data(tmp_path).get("/operations/human-patterns", headers=headers())
    assert response.status_code == 200
    assert "human_decision_patterns" in response.json()


def test_conflict_frequency_endpoint(tmp_path: object) -> None:
    response = client_with_data(tmp_path).get("/operations/conflicts", headers=headers())
    assert response.status_code == 200
    assert response.json()["conflict_frequency"]["A"] == 1


def test_audit_trail_query_endpoint(tmp_path: object) -> None:
    client = client_with_data(tmp_path)
    start = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    end = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    response = client.get(f"/audit/trail?start={start}&end={end}", headers=headers())
    assert response.status_code == 200
    assert response.json()["count"] >= 3


def test_audit_integrity_endpoint(tmp_path: object) -> None:
    client = client_with_data(tmp_path)
    start = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    end = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    response = client.get(f"/audit/integrity/{start}/{end}", headers=headers())
    assert response.status_code == 200
    assert response.json()["valid"] is True
