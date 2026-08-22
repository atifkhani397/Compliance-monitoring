import pytest

from src.mcms.core.exceptions import AssignmentError
from src.mcms.core.human_assignment import HumanAssignmentEngine, HumanProfile


def profile(
    human_id: str = "h1", tier: int = 1, skills: list[str] | None = None, **kwargs: object
) -> HumanProfile:
    return HumanProfile(
        human_id=human_id,
        name=human_id,
        tier=tier,
        skills=skills or [],
        **kwargs,
    )


def test_register_human_profile() -> None:
    engine = HumanAssignmentEngine()
    engine.register_human(profile())
    assert engine.humans["h1"].name == "h1"


def test_assign_human_by_tier() -> None:
    engine = HumanAssignmentEngine()
    engine.register_human(profile("tier2", 2))
    assert engine.assign(1, []) == "tier2"


def test_assign_human_by_skills() -> None:
    engine = HumanAssignmentEngine()
    engine.register_human(profile("aml", 1, ["aml"]))
    engine.register_human(profile("general", 1, ["general"]))
    assert engine.assign(1, ["aml"]) == "aml"


def test_workload_tracking() -> None:
    engine = HumanAssignmentEngine()
    engine.register_human(profile("h1", max_workload=2))
    assert engine.assign(1, []) == "h1"
    assert engine.get_workload("h1") == 1
    engine.release("h1")
    assert engine.get_workload("h1") == 0


def test_availability_check() -> None:
    engine = HumanAssignmentEngine()
    engine.register_human(profile("full", max_workload=1, current_workload=1))
    assert engine.get_availability("full") is False
    with pytest.raises(AssignmentError):
        engine.assign(1, [])


def test_conflict_of_interest_exclusion() -> None:
    engine = HumanAssignmentEngine()
    engine.register_human(profile("biased", 1, conflict_of_interest_flags=["entity-1"]))
    engine.register_human(profile("clear", 1))
    assert engine.assign(1, [], ["entity-1"]) == "clear"


def test_after_hours_routing() -> None:
    engine = HumanAssignmentEngine({"after_hours": True, "on_call": ["oncall"], "cco_id": "cco"})
    engine.register_human(profile("regular", 3))
    engine.register_human(profile("oncall", 3))
    assert engine.assign(3, []) == "oncall"


def test_performance_recording() -> None:
    engine = HumanAssignmentEngine()
    engine.register_human(profile())
    engine.record_performance("h1", "avg_response_seconds", 120.5)
    assert engine.humans["h1"].performance_metrics["avg_response_seconds"] == 120.5
