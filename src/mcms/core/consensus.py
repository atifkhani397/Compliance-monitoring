"""Deterministic consensus algorithms for multi-agent compliance assessments."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from src.mcms.core.exceptions import (
    ConsensusError,
    ConvergenceError,
    InvalidAssessmentError,
)

ZERO = Decimal("0")
ONE = Decimal("1")
HALF = Decimal("0.5")
DEFAULT_ESCALATION_THRESHOLD = Decimal("0.7")
DEFAULT_CONVERGENCE_THRESHOLD = Decimal("0.2")
SEVERITY_ORDER = {"NO_ALERT": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
DEFAULT_AGENT_WEIGHTS = {
    "agent-tm-001": Decimal("0.35"),
    "agent-cs-001": Decimal("0.30"),
    "agent-ru-001": Decimal("0.20"),
    "agent-rg-001": Decimal("0.15"),
}
VALID_AGENT_IDS = frozenset(DEFAULT_AGENT_WEIGHTS)
FRAME = frozenset({"violation", "no_violation", "uncertain"})


def _decimal(value: Decimal | float | int | str, field_name: str = "value") -> Decimal:
    """Convert a numeric input through its string form to avoid binary float artefacts."""
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise InvalidAssessmentError(
            f"{field_name} must be a finite decimal", {field_name: value}
        ) from error
    if not result.is_finite():
        raise InvalidAssessmentError(f"{field_name} must be finite", {field_name: str(value)})
    return result


def _bounded(value: Decimal, field_name: str) -> Decimal:
    if value < ZERO or value > ONE:
        raise InvalidAssessmentError(
            f"{field_name} must be between 0 and 1", {field_name: str(value)}
        )
    return value


@dataclass(frozen=True)
class EvidenceItem:
    """A traceable evidence item supplied by an agent."""

    evidence_type: str
    evidence_data: dict[str, Any]
    source_agent: str
    timestamp: datetime
    chain_of_custody: list[str]


@dataclass(frozen=True)
class AgentAssessment:
    """Standardized input contract for one agent's compliance assessment."""

    agent_id: str
    violation_type: str
    confidence: Decimal
    evidence: list[EvidenceItem]
    timestamp: datetime
    assessment_id: UUID

    def __post_init__(self) -> None:
        if self.agent_id not in VALID_AGENT_IDS:
            raise InvalidAssessmentError("Unknown agent_id", {"agent_id": self.agent_id})
        normalized = _bounded(_decimal(self.confidence, "confidence"), "confidence")
        object.__setattr__(self, "confidence", normalized)
        if not self.violation_type:
            raise InvalidAssessmentError("violation_type cannot be empty")
        for item in self.evidence:
            if not isinstance(item, EvidenceItem):
                raise InvalidAssessmentError("evidence must contain EvidenceItem values")


@dataclass(frozen=True)
class ConsensusResult:
    """Standardized output contract for a consensus decision."""

    consensus_confidence: Decimal
    consensus_severity: str
    conflict_type: str | None
    contributing_agents: list[str]
    dissenting_agents: list[str]
    resolution_method: str
    escalation_required: bool
    escalation_reason: str | None
    audit_trail_ref: UUID

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "consensus_confidence",
            _bounded(
                _decimal(self.consensus_confidence, "consensus_confidence"), "consensus_confidence"
            ),
        )
        if self.consensus_severity not in SEVERITY_ORDER:
            raise ConsensusError(f"Unsupported consensus severity: {self.consensus_severity}")
        if self.resolution_method not in {"bayesian", "dempster_shafer", "hybrid", "escalation"}:
            raise ConsensusError(f"Unsupported resolution method: {self.resolution_method}")


class ConsensusEngine:
    """Resolve assessments using deterministic Bayesian and Dempster–Shafer fusion."""

    def __init__(self, config: Mapping[str, Any] | Any | None = None) -> None:
        raw: Mapping[str, Any] = config if isinstance(config, Mapping) else {}
        if config is not None and not isinstance(config, Mapping):
            get_consensus_config = getattr(config, "get_consensus_config", None)
            if callable(get_consensus_config):
                raw = {"consensus": get_consensus_config()}
            else:
                get_method = getattr(config, "get", None)
                if callable(get_method):
                    raw = {
                        "consensus": {
                            "prior": get_method("consensus.prior", HALF),
                            "escalation_threshold": get_method(
                                "consensus.escalation_threshold", DEFAULT_ESCALATION_THRESHOLD
                            ),
                            "convergence_threshold": get_method(
                                "consensus.convergence_threshold", DEFAULT_CONVERGENCE_THRESHOLD
                            ),
                            "agent_weights": get_method(
                                "consensus.agent_weights", DEFAULT_AGENT_WEIGHTS
                            ),
                        }
                    }
        consensus_config = raw.get("consensus", {})
        if not isinstance(consensus_config, Mapping):
            consensus_config = {}
        raw_weights = consensus_config.get(
            "agent_weights", raw.get("agent_weights", DEFAULT_AGENT_WEIGHTS)
        )
        self.agent_weights = self._load_weights(raw_weights)
        self.escalation_threshold = _bounded(
            _decimal(consensus_config.get("escalation_threshold", DEFAULT_ESCALATION_THRESHOLD)),
            "escalation_threshold",
        )
        self.convergence_threshold = _bounded(
            _decimal(consensus_config.get("convergence_threshold", DEFAULT_CONVERGENCE_THRESHOLD)),
            "convergence_threshold",
        )
        self.prior = _bounded(_decimal(consensus_config.get("prior", HALF)), "prior")

    @staticmethod
    def _load_weights(raw_weights: Any) -> dict[str, Decimal]:
        weights: dict[str, Decimal] = {}
        source = raw_weights if isinstance(raw_weights, Mapping) else DEFAULT_AGENT_WEIGHTS
        for agent_id in VALID_AGENT_IDS:
            weights[agent_id] = _bounded(
                _decimal(
                    source.get(agent_id, DEFAULT_AGENT_WEIGHTS[agent_id]), f"weight:{agent_id}"
                ),
                f"weight:{agent_id}",
            )
        total = sum(weights.values(), ZERO)
        if total <= ZERO:
            raise ConsensusError("At least one agent weight must be positive")
        ordered_ids = sorted(weights)
        normalized = {agent_id: weights[agent_id] / total for agent_id in ordered_ids}
        normalized[ordered_ids[-1]] = ONE - sum(
            (normalized[agent_id] for agent_id in ordered_ids[:-1]), ZERO
        )
        return normalized

    def bayesian_update(
        self, prior: Decimal | float | int | str, likelihoods: Sequence[Decimal | float | int | str]
    ) -> Decimal:
        """Return P(H|E) using prior odds and independent evidence likelihoods."""
        prior_decimal = _bounded(_decimal(prior, "prior"), "prior")
        if not likelihoods:
            return prior_decimal
        evidence = [_bounded(_decimal(value, "likelihood"), "likelihood") for value in likelihoods]
        numerator = prior_decimal
        complement = ONE - prior_decimal
        for likelihood in evidence:
            numerator *= likelihood
            complement *= ONE - likelihood
        denominator = numerator + complement
        if denominator == ZERO:
            return HALF
        return _bounded(numerator / denominator, "posterior")

    @staticmethod
    def _subset_key(key: Any) -> frozenset[str]:
        if isinstance(key, (frozenset, set, tuple, list)):
            values = {str(item) for item in key}
        else:
            text = str(key).strip().lower()
            if text in {"theta", "all", "{violation,no_violation,uncertain}"}:
                values = set(FRAME)
            elif "|" in text:
                values = {item for item in text.split("|") if item}
            else:
                values = {text}
        if not values or not values.issubset(FRAME):
            raise ConsensusError(f"Invalid Dempster-Shafer hypothesis: {sorted(values)}")
        return frozenset(values)

    @staticmethod
    def _public_key(subset: frozenset[str]) -> str:
        if subset == FRAME:
            return "theta"
        return "|".join(sorted(subset))

    def dempster_shafer_combine(
        self, bbas: Sequence[Mapping[Any, Decimal | float | int | str]]
    ) -> dict[str, Decimal]:
        """Combine BBAs using Dempster's normalized conjunctive rule."""
        if not bbas:
            return {"uncertain": ONE}
        combined: dict[frozenset[str], Decimal] = {FRAME: ONE}
        for bba in bbas:
            if not bba:
                raise ConsensusError("Each BBA must contain at least one hypothesis")
            normalized_input: dict[frozenset[str], Decimal] = {}
            total = ZERO
            for key, raw_mass in bba.items():
                subset = self._subset_key(key)
                mass = _bounded(_decimal(raw_mass, "mass"), "mass")
                normalized_input[subset] = normalized_input.get(subset, ZERO) + mass
                total += mass
            if total <= ZERO:
                raise ConsensusError("BBA mass total must be positive")
            normalized_input = {key: value / total for key, value in normalized_input.items()}
            next_combined: dict[frozenset[str], Decimal] = {}
            conflict = ZERO
            for left, left_mass in combined.items():
                for right, right_mass in normalized_input.items():
                    intersection = left & right
                    product = left_mass * right_mass
                    if not intersection:
                        conflict += product
                    else:
                        next_combined[intersection] = (
                            next_combined.get(intersection, ZERO) + product
                        )
            if conflict >= ONE:
                raise ConvergenceError(
                    "Dempster-Shafer combination is completely conflicting (K=1)",
                    {"K": str(conflict)},
                )
            normalization = ONE - conflict
            combined = {key: value / normalization for key, value in next_combined.items()}
        return {
            self._public_key(key): value
            for key, value in sorted(combined.items(), key=lambda item: self._public_key(item[0]))
        }

    @staticmethod
    def _belief_for_violation(ds_belief: Mapping[str, Decimal]) -> Decimal:
        direct = ds_belief.get("belief_violation", ds_belief.get("violation", ZERO))
        return _bounded(_decimal(direct, "belief_violation"), "belief_violation")

    def _audit_ref(self, values: Mapping[str, Any]) -> UUID:
        canonical = json.dumps(values, sort_keys=True, default=str, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        # UUID v5 provides deterministic bits; set the version nibble to v4 so
        # the result remains valid for the inter-agent message trace contract.
        return UUID(int=uuid5(NAMESPACE_URL, digest).int, version=4)

    def hybrid_consensus(
        self, bayesian_posterior: Decimal | float | int | str, ds_belief: dict[str, Decimal]
    ) -> ConsensusResult:
        """Fuse Bayesian posterior and DS belief, escalating on material divergence."""
        posterior = _bounded(
            _decimal(bayesian_posterior, "bayesian_posterior"), "bayesian_posterior"
        )
        belief = self._belief_for_violation(ds_belief)
        disagreement = abs(posterior - belief)
        confidence = (posterior + belief) / Decimal("2")
        if disagreement > self.convergence_threshold:
            raise ConvergenceError(
                "Bayesian and Dempster-Shafer results disagree beyond the convergence threshold",
                {
                    "bayesian": str(posterior),
                    "dempster_shafer": str(belief),
                    "difference": str(disagreement),
                },
            )
        severity = (
            "HIGH"
            if confidence >= self.escalation_threshold
            else "NO_ALERT"
            if confidence < HALF
            else "MEDIUM"
        )
        return ConsensusResult(
            consensus_confidence=confidence,
            consensus_severity=severity,
            conflict_type=None,
            contributing_agents=[],
            dissenting_agents=[],
            resolution_method="hybrid",
            escalation_required=confidence < self.escalation_threshold,
            escalation_reason="Consensus confidence is below 0.7"
            if confidence < self.escalation_threshold
            else None,
            audit_trail_ref=self._audit_ref(
                {
                    "bayesian": str(posterior),
                    "ds": {key: str(value) for key, value in ds_belief.items()},
                }
            ),
        )

    @staticmethod
    def _evidence_values(assessments: list[AgentAssessment], keys: set[str]) -> list[Any]:
        values: list[Any] = []
        for assessment in assessments:
            for item in assessment.evidence:
                for key in keys:
                    if key in item.evidence_data:
                        values.append(item.evidence_data[key])
        return values

    def classify_conflict(self, assessments: list[AgentAssessment]) -> str:
        """Classify disagreement using the Phase 3 A–G taxonomy."""
        if len(assessments) < 2:
            return "A"
        violation_types = {assessment.violation_type for assessment in assessments}
        regulatory_values = self._evidence_values(
            assessments, {"jurisdiction", "regulatory_requirement", "regulatory_conflict"}
        )
        if len(set(map(str, regulatory_values))) > 1 or any(
            "regulat" in assessment.violation_type.lower() for assessment in assessments
        ):
            return "E"
        has_exculpatory = any(
            item.evidence_type.lower() in {"exculpatory", "exculpatory_evidence"}
            or bool(item.evidence_data.get("exculpatory", False))
            for assessment in assessments
            for item in assessment.evidence
        )
        has_positive = any(assessment.confidence >= HALF for assessment in assessments)
        has_negative = any(assessment.confidence < HALF for assessment in assessments)
        if has_exculpatory and has_positive:
            return "D"
        if has_positive and has_negative:
            return "A"
        severities = self._evidence_values(assessments, {"severity"})
        if len({str(value).upper() for value in severities}) > 1:
            return "B"
        attributions = self._evidence_values(
            assessments, {"attributed_entity", "attribution", "responsible_entity", "actor"}
        )
        if len(set(map(str, attributions))) > 1:
            return "C"
        timestamps = [assessment.timestamp for assessment in assessments]
        if (max(timestamps) - min(timestamps)).total_seconds() > 60:
            return "F"
        affected = self._evidence_values(assessments, {"affected_entities", "entity_id"})
        if len({json.dumps(value, sort_keys=True, default=str) for value in affected}) > 1:
            return "G"
        if len(violation_types) > 1:
            return "C"
        return "B" if len(assessments) > 1 else "A"

    @staticmethod
    def _severity(assessment: AgentAssessment) -> str:
        values = ConsensusEngine._evidence_values([assessment], {"severity"})
        if values:
            severity = str(values[0]).upper()
            if severity in SEVERITY_ORDER:
                return severity
        return (
            "HIGH"
            if assessment.confidence >= Decimal("0.8")
            else "MEDIUM"
            if assessment.confidence >= HALF
            else "LOW"
        )

    def calibrate_weights(self, historical_outcomes: list[dict[str, Any]]) -> dict[str, Decimal]:
        """Adjust weights by historical accuracy, then normalize them to sum to one."""
        accuracy_by_agent: dict[str, list[Decimal]] = {agent_id: [] for agent_id in VALID_AGENT_IDS}
        for outcome in historical_outcomes:
            agent_id = str(outcome.get("agent_id", ""))
            if agent_id not in accuracy_by_agent:
                continue
            raw_accuracy = outcome.get("accuracy", outcome.get("correct"))
            if isinstance(raw_accuracy, bool):
                accuracy = ONE if raw_accuracy else ZERO
            elif raw_accuracy is None:
                continue
            else:
                accuracy = _bounded(_decimal(raw_accuracy, "accuracy"), "accuracy")
            accuracy_by_agent[agent_id].append(accuracy)
        adjusted: dict[str, Decimal] = {}
        for agent_id, weight in self.agent_weights.items():
            observations = accuracy_by_agent[agent_id]
            factor = sum(observations, ZERO) / Decimal(len(observations)) if observations else ONE
            adjusted[agent_id] = weight * factor
        total = sum(adjusted.values(), ZERO)
        if total == ZERO:
            return dict(self.agent_weights)
        ordered_ids = sorted(adjusted)
        self.agent_weights = {agent_id: adjusted[agent_id] / total for agent_id in ordered_ids}
        self.agent_weights[ordered_ids[-1]] = ONE - sum(
            (self.agent_weights[agent_id] for agent_id in ordered_ids[:-1]), ZERO
        )
        return dict(self.agent_weights)

    def resolve(self, assessments: list[AgentAssessment]) -> ConsensusResult:
        """Resolve a set of assessments into one reproducible decision."""
        if not assessments:
            raise InvalidAssessmentError("At least one assessment is required")
        conflict_type = self.classify_conflict(assessments) if len(assessments) > 1 else None
        contributing = sorted({assessment.agent_id for assessment in assessments})
        if conflict_type == "D":
            confidence = max((assessment.confidence for assessment in assessments), default=ZERO)
            result = ConsensusResult(
                consensus_confidence=confidence,
                consensus_severity="NO_ALERT",
                conflict_type=conflict_type,
                contributing_agents=contributing,
                dissenting_agents=sorted(
                    {
                        assessment.agent_id
                        for assessment in assessments
                        if assessment.confidence >= HALF
                    }
                ),
                resolution_method="escalation",
                escalation_required=False,
                escalation_reason="Exculpatory evidence overrides the suspected false positive",
                audit_trail_ref=self._audit_ref(
                    {"type": "D", "agents": contributing, "confidence": str(confidence)}
                ),
            )
            return result

        likelihoods = [assessment.confidence for assessment in assessments]
        bayesian = self.bayesian_update(self.prior, likelihoods)
        max_weight = max(self.agent_weights.values())
        bbas: list[dict[str, Decimal]] = []
        for assessment in assessments:
            weight_factor = self.agent_weights.get(assessment.agent_id, ZERO) / max_weight
            effective_confidence = HALF + weight_factor * (assessment.confidence - HALF)
            bbas.append(
                {
                    "violation": effective_confidence * Decimal("0.85"),
                    "no_violation": (ONE - effective_confidence) * Decimal("0.85"),
                    "uncertain": Decimal("0.15"),
                }
            )
        ds = self.dempster_shafer_combine(bbas)
        try:
            hybrid = self.hybrid_consensus(bayesian, ds)
            method = hybrid.resolution_method
            confidence = hybrid.consensus_confidence
            escalation_required = hybrid.escalation_required
            escalation_reason = hybrid.escalation_reason
        except ConvergenceError as error:
            confidence = min(bayesian, self._belief_for_violation(ds))
            method = "escalation"
            escalation_required = True
            escalation_reason = str(error)
        if conflict_type == "E":
            escalation_required = True
            escalation_reason = "Regulatory conflict requires immediate legal counsel escalation"
        severity_candidates = [self._severity(assessment) for assessment in assessments]
        weighted_severity = (
            max(severity_candidates, key=lambda value: SEVERITY_ORDER[value])
            if severity_candidates
            else "NO_ALERT"
        )
        severity = "NO_ALERT" if confidence < HALF else weighted_severity
        dissenting = sorted(
            assessment.agent_id
            for assessment in assessments
            if abs(assessment.confidence - confidence) >= Decimal("0.2")
            or self._severity(assessment) != weighted_severity
        )
        if len(assessments) > 1 and len({assessment.agent_id for assessment in assessments}) >= 2:
            confidence_scores = sorted(assessment.confidence for assessment in assessments)
            if confidence_scores[-1] - confidence_scores[0] < Decimal("0.1"):
                escalation_required = True
                escalation_reason = (
                    "Agent confidence scores differ by less than 0.1; human tie-break required"
                )
        if conflict_type == "E":
            severity = "CRITICAL"
        result_data = {
            "confidence": str(confidence),
            "severity": severity,
            "conflict_type": conflict_type,
            "agents": contributing,
            "method": method,
            "escalation": escalation_required,
        }
        return ConsensusResult(
            consensus_confidence=confidence,
            consensus_severity=severity,
            conflict_type=conflict_type,
            contributing_agents=contributing,
            dissenting_agents=dissenting,
            resolution_method=method,
            escalation_required=escalation_required,
            escalation_reason=escalation_reason,
            audit_trail_ref=self._audit_ref(result_data),
        )
