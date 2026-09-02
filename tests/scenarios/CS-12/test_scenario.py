from pathlib import Path

from src.mcms.scenario_specs import SCENARIOS
from src.mcms.scenario_support import assert_scenario, run_scenario

SPEC = SCENARIOS["CS-12"]
ARTIFACT_DIR = Path(__file__).parent


def execute() -> dict[str, object]:
    result = run_scenario(SPEC, ARTIFACT_DIR)
    assert_scenario(SPEC, result)
    return result


def test_cs12_detection_produces_expected_alert_or_update() -> None:
    result = execute()
    payloads = [
        message.payload for message in result["messages"] if isinstance(message.payload, dict)
    ]
    if SPEC.no_alert:
        assert all(message.message_type != "ALERT" for message in result["messages"])
        assert any(
            payload.get("update_type") == "false_positive_suppressed" for payload in payloads
        )
    else:
        assert SPEC.expected_alert in {payload.get("severity") for payload in payloads}


def test_cs12_inter_agent_messages_validate_against_schema() -> None:
    result = execute()
    assert len(result["messages"]) >= 2
    assert all(message.trace_id == result["correlation_id"] for message in result["messages"])


def test_cs12_consensus_or_special_flow_is_correct() -> None:
    result = execute()
    if SPEC.scenario_id == "CS-18":
        assert result["consensus"] is None
        assert result["escalation_id"] is None
    elif SPEC.scenario_id == "CS-19":
        assert result["consensus"] is None
        alert = next(message for message in result["messages"] if message.message_type == "ALERT")
        assert alert.payload["affected_jurisdictions"] == ["EU", "Singapore"]
    else:
        assert result["consensus"] is not None
        if SPEC.expected_conflict_type:
            assert result["consensus"].conflict_type == SPEC.expected_conflict_type
        if SPEC.scenario_id == "CS-20":
            senders = {message.sender_agent_id for message in result["messages"]}
            assert set(SPEC.agents).issubset(senders)


def test_cs12_escalation_and_report_types_are_correct() -> None:
    result = execute()
    if SPEC.required_tier is not None:
        assert result["escalation_tier"] == SPEC.required_tier
        assert result["escalation_id"] is not None
    else:
        assert result["escalation_id"] is None
    assert tuple(result["report_types"]) == SPEC.report_types


def test_cs12_audit_trail_is_complete_and_verifiable() -> None:
    result = execute()
    assert result["audit_valid"] is True
    minimum = 30 if SPEC.scenario_id == "CS-20" else 8
    assert result["audit_entries"] >= minimum
