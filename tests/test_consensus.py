from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from src.mcms.core.consensus import AgentAssessment, ConsensusEngine, EvidenceItem
from src.mcms.core.exceptions import ConvergenceError, InvalidAssessmentError


def assessment(
    agent_id: str,
    confidence: str,
    violation_type: str = "market-manipulation",
    severity: str = "HIGH",
    timestamp: datetime | None = None,
    **context: object,
) -> AgentAssessment:
    evidence_data = {"severity": severity, **context}
    return AgentAssessment(
        agent_id=agent_id,
        violation_type=violation_type,
        confidence=Decimal(confidence),
        evidence=[
            EvidenceItem(
                evidence_type="assessment",
                evidence_data=evidence_data,
                source_agent=agent_id,
                timestamp=timestamp or datetime.now(UTC),
                chain_of_custody=[agent_id],
            )
        ],
        timestamp=timestamp or datetime.now(UTC),
        assessment_id=uuid4(),
    )


def test_bayesian_single_agent() -> None:
    engine = ConsensusEngine()
    assert engine.bayesian_update(Decimal("0.5"), [Decimal("0.8")]) == Decimal("0.8")


def test_bayesian_two_agreeing_agents() -> None:
    result = ConsensusEngine().bayesian_update("0.5", ["0.8", "0.8"])
    assert result == Decimal("0.9411764705882352941176470588")


def test_bayesian_two_disagreeing_agents() -> None:
    result = ConsensusEngine().bayesian_update("0.5", ["0.9", "0.1"])
    assert result == Decimal("0.5")


def test_dempster_shafer_combines_two_bbas() -> None:
    result = ConsensusEngine().dempster_shafer_combine(
        [
            {"violation": "0.8", "no_violation": "0.1", "uncertain": "0.1"},
            {"violation": "0.7", "no_violation": "0.2", "uncertain": "0.1"},
        ]
    )
    assert result["violation"] > Decimal("0.7")
    assert sum(result.values(), Decimal("0")) == Decimal("1")


def test_dempster_shafer_complete_conflict() -> None:
    with pytest.raises(ConvergenceError):
        ConsensusEngine().dempster_shafer_combine(
            [
                {"violation": "1"},
                {"no_violation": "1"},
            ]
        )


def test_hybrid_consensus_with_agreeing_agents() -> None:
    result = ConsensusEngine().hybrid_consensus("0.8", {"violation": Decimal("0.75")})
    assert result.resolution_method == "hybrid"
    assert result.consensus_confidence == Decimal("0.775")
    assert result.escalation_required is False


def test_hybrid_consensus_with_disagreement_escalates() -> None:
    with pytest.raises(ConvergenceError):
        ConsensusEngine().hybrid_consensus("0.9", {"violation": Decimal("0.5")})


def test_type_a_detection_disagreement() -> None:
    result = ConsensusEngine().resolve(
        [
            assessment("agent-tm-001", "0.9"),
            assessment("agent-cs-001", "0.2"),
        ]
    )
    assert result.conflict_type == "A"
    assert result.escalation_required is True


def test_type_b_severity_disagreement() -> None:
    result = ConsensusEngine().resolve(
        [
            assessment("agent-tm-001", "0.8", severity="CRITICAL"),
            assessment("agent-cs-001", "0.8", severity="HIGH"),
        ]
    )
    assert result.conflict_type == "B"
    assert result.consensus_severity == "CRITICAL"


def test_type_c_attribution_disagreement() -> None:
    result = ConsensusEngine().resolve(
        [
            assessment("agent-tm-001", "0.8", attributed_entity="desk-a"),
            assessment("agent-cs-001", "0.8", attributed_entity="trader-b"),
        ]
    )
    assert result.conflict_type == "C"


def test_type_d_false_positive_suppression() -> None:
    result = ConsensusEngine().resolve(
        [
            assessment("agent-tm-001", "0.9"),
            assessment("agent-cs-001", "0.2", exculpatory=True),
        ]
    )
    assert result.conflict_type == "D"
    assert result.consensus_severity == "NO_ALERT"
    assert result.escalation_required is False


def test_type_e_regulatory_conflict_escalates() -> None:
    result = ConsensusEngine().resolve(
        [
            assessment("agent-ru-001", "0.8", jurisdiction="EU"),
            assessment("agent-cs-001", "0.8", jurisdiction="Singapore"),
        ]
    )
    assert result.conflict_type == "E"
    assert result.consensus_severity == "CRITICAL"
    assert result.escalation_required is True


def test_type_f_temporal_conflict() -> None:
    start = datetime(2026, 8, 22, 10, 0, tzinfo=UTC)
    result = ConsensusEngine().resolve(
        [
            assessment("agent-tm-001", "0.8", timestamp=start),
            assessment("agent-cs-001", "0.8", timestamp=start + timedelta(seconds=90)),
        ]
    )
    assert result.conflict_type == "F"


def test_type_g_scope_conflict() -> None:
    result = ConsensusEngine().resolve(
        [
            assessment("agent-tm-001", "0.8", affected_entities=["a", "b"]),
            assessment("agent-cs-001", "0.8", affected_entities=["a", "b", "c"]),
        ]
    )
    assert result.conflict_type == "G"


def test_dynamic_weight_calibration() -> None:
    engine = ConsensusEngine()
    weights = engine.calibrate_weights(
        [
            {"agent_id": "agent-tm-001", "accuracy": "1.0"},
            {"agent_id": "agent-cs-001", "accuracy": "0.5"},
        ]
    )
    assert weights["agent-tm-001"] > Decimal("0.35")
    assert sum(weights.values(), Decimal("0")) == Decimal("1")


def test_deterministic_audit_reference() -> None:
    first = assessment("agent-tm-001", "0.8")
    second = assessment("agent-cs-001", "0.8")
    first_result = ConsensusEngine().resolve([first, second])
    second_result = ConsensusEngine().resolve([first, second])
    assert first_result.audit_trail_ref == second_result.audit_trail_ref


def test_decimal_precision_is_preserved() -> None:
    result = ConsensusEngine().bayesian_update("0.333333333333333333", ["0.666666666666666667"])
    assert isinstance(result, Decimal)
    assert result.as_tuple().exponent < 0


def test_low_confidence_triggers_escalation() -> None:
    result = ConsensusEngine().resolve([assessment("agent-tm-001", "0.2")])
    assert result.escalation_required is True
    assert result.consensus_confidence < Decimal("0.7")


def test_invalid_agent_assessment_is_rejected() -> None:
    with pytest.raises(InvalidAssessmentError):
        assessment("unknown-agent", "0.8")
