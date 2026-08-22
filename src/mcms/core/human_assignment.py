"""In-memory human assignment and conflict-of-interest controls for Phase 4."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.mcms.core.exceptions import AssignmentError


@dataclass
class HumanProfile:
    """A compliance professional eligible to receive escalations."""

    human_id: str
    name: str
    tier: int
    skills: list[str]
    max_workload: int = 10
    current_workload: int = 0
    availability_schedule: dict[str, Any] = field(default_factory=dict)
    performance_metrics: dict[str, float] = field(default_factory=dict)
    conflict_of_interest_flags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.human_id:
            raise AssignmentError("human_id cannot be empty")
        if self.tier not in {1, 2, 3, 4}:
            raise AssignmentError("Human tier must be between 1 and 4")
        if self.max_workload < 1:
            raise AssignmentError("max_workload must be positive")
        if self.current_workload < 0 or self.current_workload > self.max_workload:
            raise AssignmentError("current_workload must be within max_workload")


class HumanAssignmentEngine:
    """Single source of truth for human pool availability and assignment."""

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        self.config = dict(config or {})
        self._humans: dict[str, HumanProfile] = {}
        self._performance_history: dict[str, list[tuple[str, float]]] = {}
        self._conflict_entities: set[str] = set()

    @property
    def humans(self) -> dict[str, HumanProfile]:
        return dict(self._humans)

    def register_human(self, human: HumanProfile) -> None:
        """Add or replace a human profile in the assignment pool."""
        self._humans[human.human_id] = human
        self._performance_history.setdefault(human.human_id, [])

    def update_skills(self, human_id: str, skills: list[str]) -> None:
        human = self._get_human(human_id)
        human.skills = list(dict.fromkeys(skills))

    def set_conflict_entities(self, entities: list[str]) -> None:
        """Set entities that must be excluded for the next assignment."""
        self._conflict_entities = set(entities)

    def get_workload(self, human_id: str) -> int:
        return self._get_human(human_id).current_workload

    def get_availability(self, human_id: str) -> bool:
        human = self._get_human(human_id)
        if human.current_workload >= human.max_workload:
            return False
        schedule = human.availability_schedule
        return schedule.get("available") is not False

    def _get_human(self, human_id: str) -> HumanProfile:
        human = self._humans.get(human_id)
        if human is None:
            raise AssignmentError(f"Human profile not found: {human_id}")
        return human

    def _is_after_hours(self) -> bool:
        configured = self.config.get("after_hours")
        if isinstance(configured, bool):
            return configured
        start = self.config.get("business_hours_start")
        end = self.config.get("business_hours_end")
        if not isinstance(start, int) or not isinstance(end, int):
            return False
        hour = datetime.now(UTC).hour
        return not start <= hour < end if start <= end else end <= hour < start

    def _eligible(
        self, tier: int, required_skills: set[str], conflict_entities: set[str]
    ) -> list[HumanProfile]:
        after_hours = self._is_after_hours()
        on_call = {str(item) for item in self.config.get("on_call", [])}
        cco_id = self.config.get("cco_id")
        candidates: list[HumanProfile] = []
        for human in self._humans.values():
            if human.tier < tier or not self.get_availability(human.human_id):
                continue
            if required_skills and not required_skills.intersection(human.skills):
                continue
            if conflict_entities.intersection(human.conflict_of_interest_flags):
                continue
            if (
                after_hours
                and tier >= 3
                and human.human_id not in on_call
                and human.human_id != cco_id
            ):
                continue
            if tier == 4 and cco_id is not None and human.human_id != cco_id:
                continue
            candidates.append(human)
        return candidates

    def assign(
        self,
        tier: int,
        required_skills: list[str],
        conflict_entities: list[str] | None = None,
    ) -> str:
        """Assign the least-loaded eligible human, incrementing workload."""
        if tier not in {1, 2, 3, 4}:
            raise AssignmentError("Assignment tier must be between 1 and 4")
        entities = set(conflict_entities or []) | self._conflict_entities
        candidates = self._eligible(tier, set(required_skills), entities)
        if not candidates:
            raise AssignmentError(
                f"No available human for tier {tier} and skills {sorted(required_skills)}"
            )
        selected = min(candidates, key=lambda human: (human.current_workload, human.human_id))
        selected.current_workload += 1
        return selected.human_id

    def release(self, human_id: str) -> None:
        human = self._get_human(human_id)
        human.current_workload = max(0, human.current_workload - 1)

    def record_performance(self, human_id: str, metric: str, value: float) -> None:
        human = self._get_human(human_id)
        if not metric:
            raise AssignmentError("Performance metric cannot be empty")
        human.performance_metrics[metric] = float(value)
        self._performance_history.setdefault(human_id, []).append((metric, float(value)))
