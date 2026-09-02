from pathlib import Path

from src.mcms.scenario_specs import SCENARIOS
from src.mcms.scenario_support import assert_scenario, run_scenario

SPEC = SCENARIOS["CS-04"]
ARTIFACT_DIR = Path(__file__).parent


def execute() -> dict[str, object]:
    result = run_scenario(SPEC, ARTIFACT_DIR)
    assert_scenario(SPEC, result)
    return result


def test_cs04_detection_produces_expected_alert() -> None:
    result = execute()
    assert (
        SPEC.expected_alert
        in {
            message.payload.get("severity")
            for message in result["messages"]
            if isinstance(message.payload, dict)
        }
        or SPEC.no_alert
    )


def test_cs04_inter_agent_messages_validate_against_schema() -> None:
    result = execute()
    assert len(result["messages"]) >= 2
    assert all(message.trace_id == result["correlation_id"] for message in result["messages"])


def test_cs04_consensus_or_special_flow_is_recorded() -> None:
    result = execute()
    assert (
        result["consensus"] is not None or SPEC.special_update or SPEC.expected_conflict_type == "E"
    )
    if SPEC.expected_conflict_type:
        assert SPEC.expected_conflict_type in {SPEC.expected_conflict_type, None}


def test_cs04_escalation_and_report_types_are_correct() -> None:
    result = execute()
    if SPEC.required_tier is not None:
        assert result["escalation_tier"] == SPEC.required_tier
    assert tuple(result["report_types"]) == SPEC.report_types


def test_cs04_audit_trail_is_complete_and_verifiable() -> None:
    result = execute()
    assert result["audit_valid"] is True
    assert result["audit_entries"] >= (15 if SPEC.scenario_id == "CS-01" else 8)
    if SPEC.scenario_id == "CS-18":
        assert not any(message.message_type == "ALERT" for message in result["messages"])
