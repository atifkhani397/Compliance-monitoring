---
title: MACMS Consensus Algorithm Specification
date: 2026-08-22
version: 2.0.0
status: Implemented
---

# MACMS Consensus Algorithm Specification

## 1. Scope and Invariants

The consensus engine transforms one or more `AgentAssessment` records into one deterministic `ConsensusResult`. All numerical operations use `decimal.Decimal`; inputs are converted from their textual representation so binary floating-point artifacts cannot change a decision. The same ordered set of assessment values produces the same confidence, severity, conflict classification, escalation state, and audit reference.

The frame of discernment is:

> Θ = {violation, no_violation, uncertain}

Assessments retain their original evidence and timestamps. The engine never lets one agent directly override another; every disagreement goes through the consensus contract.

## 2. Bayesian Consensus Layer

Each agent supplies a confidence that is interpreted as an evidence likelihood `P(Ei|H)`. The default prior is `P(H)=0.5`. For independent evidence, the posterior is calculated as:

`P(H|E1,E2,...,En) = P(H) × Π P(Ei|H) / [P(H) × Π P(Ei|H) + (1-P(H)) × Π (1-P(Ei|H))]`

The implementation uses historical false-positive and accuracy outcomes to calibrate agent influence. A single assessment returns its likelihood as the posterior when the default prior is neutral. Priors may be configured under `consensus.prior`.

## 3. Dempster–Shafer Evidence Fusion

Each assessment is converted into a basic belief assignment. The implementation assigns the weighted confidence to the violation and no-violation hypotheses, with a residual uncertain mass. For two BBAs, the normalized Dempster rule is:

`m12(A) = Σ[B ∩ C = A] m1(B)m2(C) / (1-K)`

where:

`K = Σ[B ∩ C = ∅] m1(B)m2(C)`

Belief for violation is the direct mass assigned to `{violation}`. Plausibility is the sum of masses whose hypotheses intersect `{violation}`. A complete conflict (`K=1`) raises `ConvergenceError`; the engine does not silently normalize an impossible combination.

## 4. Hybrid Consensus Protocol

The hybrid protocol follows the master prompt exactly. First, Bayesian updating is applied to strong statistical evidence such as a Transaction Monitor threshold breach. Second, Dempster–Shafer fusion combines uncertain or conflicting evidence. Third, the Bayesian posterior and DS violation belief are averaged as a deterministic confidence estimate. Fourth, the result retains the two intermediate values through the audit reference and uses the difference for uncertainty quantification. Fifth, confidence below 0.7 triggers escalation, and Type E always escalates.

If the Bayesian posterior and DS belief differ by more than 0.2, the engine raises `ConvergenceError`; the resolver converts that failure into an escalation result with the lower confidence value. A result with confidence below 0.5 is `NO_ALERT`, while a confident result takes the highest severity supported by contributing evidence.

## 5. Agent Weight Calibration

The default weights are direct transaction evidence for TM at 0.35, corroborating communications evidence for CS at 0.30, regulatory context for RU at 0.20, and report compilation for RG at 0.15. Weights are normalized to sum to 1.0. Historical outcomes may contain `accuracy` in the range 0–1 or boolean `correct` values. Each base weight is multiplied by the agent’s mean historical accuracy and normalized again.

| Agent | Default weight | Rationale |
| --- | ---: | --- |
| TM (`agent-tm-001`) | 0.35 | Direct transaction evidence |
| CS (`agent-cs-001`) | 0.30 | Communication corroboration |
| RU (`agent-ru-001`) | 0.20 | Regulatory context |
| RG (`agent-rg-001`) | 0.15 | Report compilation rather than detection |

## 6. Tie-Breaking and Mandatory Escalation

If confidence scores differ by less than 0.1, the result requires a human analyst tie-break. Type D is resolved in favor of explicit exculpatory evidence and suppresses the alert. Type E is immediately escalated to legal counsel. Three or more contributing agents are fused in one Dempster–Shafer operation rather than pairwise calls.

## 7. Worked Examples

### Example 1: Detection Disagreement

TM provides `0.90` and CS provides `0.20`, with a neutral prior of `0.50`. The Bayesian numerator is `0.50 × 0.90 × 0.20 = 0.09`; the complement is `0.50 × 0.10 × 0.80 = 0.04`. Therefore the posterior is `0.09 / 0.13 = 0.6923`. After weighted DS fusion, suppose the violation belief is `0.58`. The hybrid confidence is `(0.6923 + 0.58)/2 = 0.6362`, below 0.7, so the result is escalated as Type A.

### Example 2: Severity Disagreement

TM and CS both identify market manipulation with confidences `0.86` and `0.82`, but TM reports CRITICAL while CS reports HIGH. The confidence spread is `0.04`, below 0.1, so a human tie-break is mandatory. The engine retains the conservative CRITICAL severity, records Type B, and emits an escalation reason explaining the tie.

### Example 3: Regulatory Conflict

RU supplies EU disclosure evidence with confidence `0.88`, while a second regulatory assessment supplies a Singapore data-localization restriction with confidence `0.84`. The conflicting jurisdictions classify the event as Type E regardless of numerical agreement. The engine marks severity CRITICAL and emits an immediate legal-counsel escalation with the contributing evidence references.

### Example 4: False-Positive Suppression

TM reports a large-trade violation at `0.92`; CS contributes an `exculpatory` item containing pre-arranged block-trade documentation. Type D takes precedence. The engine emits `NO_ALERT`, sets `escalation_required=false`, and records that exculpatory evidence suppressed the false positive.

## 8. Error Contracts

`ConsensusError` is the base consensus failure. `ConflictDetectionError` indicates that messages cannot be grouped or classified. `ConvergenceError` indicates complete DS conflict or a Bayesian–DS divergence above 0.2. `InvalidAssessmentError` indicates malformed agent input. The resolver logs all successful and exceptional decisions to the audit chain.
