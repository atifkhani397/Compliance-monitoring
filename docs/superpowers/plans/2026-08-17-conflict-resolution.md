# Phase 3: Conflict Resolution & Consensus Algorithm Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement formal conflict resolution using Bayesian inference and Dempster-Shafer theory to dynamically resolve disagreements between compliance agents.

**Architecture:** A new `ConsensusEngine` will handle the pure mathematics (Bayesian updates + DS evidence fusion) using strictly `decimal.Decimal` types. The new `ConflictResolver` acts as a coordinator, processing intercepted correlated `ALERT` messages from the `Orchestrator`, running them through the engine, and generating either a resolved consensus `Message` or an `ESCALATION`. The `Orchestrator` will be augmented with a time-window buffer to detect correlated alerts.

**Tech Stack:** Python 3.11+, Pydantic v2, `decimal.Decimal`, Pytest (Asyncio).

**Spec:** Provided in Phase 3 prompt instructions.

## Global Constraints
- All mathematical operations MUST use `decimal.Decimal` (not float) to avoid precision errors.
- All code has type hints and passes `mypy --strict`.
- All code passes `ruff check` and `ruff format`.
- Minimum 25 new test cases (total should be 100+).
- All tests pass with `pytest -v`.
- Consensus results must be deterministic.
- Audit trail integration: every consensus decision is logged.

---

### Task 1: Taxonomy and Math Formalization Documentation

**Files:**
- Create: `docs/conflict-resolution/conflict-taxonomy.md`
- Create: `docs/conflict-resolution/consensus-algorithm.md`

**Interfaces:** N/A (Documentation)

- [ ] **Step 1: Write Conflict Taxonomy**
  Create `conflict-taxonomy.md` mapping Types A through G with examples, severity, and resolution strategies per the spec.
- [ ] **Step 2: Write Consensus Algorithm Spec**
  Create `consensus-algorithm.md` documenting Bayesian updates, Dempster-Shafer rules, the Hybrid protocol steps, Agent Weights, and Tie-Breaking rules.
- [ ] **Step 3: Commit**
  `git add docs/conflict-resolution/ && git commit -m "docs: formalize consensus math and conflict taxonomy"`

### Task 2: Extend Message Schema and Exceptions

**Files:**
- Modify: `src/mcms/core/message.py`
- Modify: `src/mcms/core/exceptions.py`
- Modify: `tests/test_message_schema.py`

**Interfaces:**
- Produces: `ConsensusPayload` (new model), updated `AlertPayload`, `EscalationPayload`, `ResponsePayload`.
- Produces: `ConsensusError`, `ConflictDetectionError`, `ConvergenceError`, `InvalidAssessmentError`.

- [ ] **Step 1: Add new Exceptions**
  Update `exceptions.py` with the 4 new consensus-related exceptions.
- [ ] **Step 2: Extend Message Schema**
  Add `ConsensusPayload` class. Add `consensus_result` to `AlertPayload`. Add `conflict_type` to `EscalationPayload`. Add `resolution_method` to `ResponsePayload`. Update `PayloadType`.
- [ ] **Step 3: Write tests for schema extensions**
  Update `test_message_schema.py` to test parsing the new optional fields and the `ConsensusPayload`.
- [ ] **Step 4: Verify**
  `pytest tests/test_message_schema.py` and `mypy --strict src/`
- [ ] **Step 5: Commit**
  `git add src/mcms/core/message.py src/mcms/core/exceptions.py tests/test_message_schema.py && git commit -m "feat: extend message schema for consensus payloads"`

### Task 3: Consensus Engine Foundation & Data Structures

**Files:**
- Create: `src/mcms/core/consensus.py`
- Create: `tests/test_consensus.py`

**Interfaces:**
- Produces: `AgentAssessment`, `EvidenceItem`, `ConsensusResult` datastructures using Pydantic.

- [ ] **Step 1: Define Data Models**
  In `consensus.py`, define `EvidenceItem`, `AgentAssessment`, and `ConsensusResult` (using Pydantic models for validation, utilizing `decimal.Decimal` for confidence fields).
- [ ] **Step 2: Write Data Model Tests**
  In `test_consensus.py`, write tests ensuring fields accept and parse `Decimal` correctly.
- [ ] **Step 3: Verify**
  `pytest tests/test_consensus.py` and `mypy --strict src/`
- [ ] **Step 4: Commit**
  `git add src/mcms/core/consensus.py tests/test_consensus.py && git commit -m "feat: implement consensus engine datastructures"`

### Task 4: Consensus Engine Mathematical Implementation

**Files:**
- Modify: `src/mcms/core/consensus.py`
- Modify: `tests/test_consensus.py`

**Interfaces:**
- Produces: `ConsensusEngine` class with `bayesian_update`, `dempster_shafer_combine`, `hybrid_consensus`, `classify_conflict`, `resolve`, and `calibrate_weights`.

- [ ] **Step 1: Write failing math tests**
  Write 15 tests in `test_consensus.py` covering Bayesian updates, DS combination, K=1 (complete conflict), hybrid rules, Type D false positive, Type E regulatory logic, and convergence errors.
- [ ] **Step 2: Implement Bayesian & DS Math**
  Implement `bayesian_update` (Bayes rule) and `dempster_shafer_combine` (Dempster's Rule of Combination) using `Decimal`.
- [ ] **Step 3: Implement Hybrid Protocol**
  Implement `hybrid_consensus`, integrating Bayes -> DS. Implement `classify_conflict` and tie-breaking rules.
- [ ] **Step 4: Verify**
  `pytest tests/test_consensus.py` until all math tests pass.
- [ ] **Step 5: Commit**
  `git add src/mcms/core/consensus.py tests/test_consensus.py && git commit -m "feat: implement Bayesian and DS mathematical consensus"`

### Task 5: Conflict Resolver Service

**Files:**
- Create: `src/mcms/core/conflict_resolver.py`
- Create: `tests/test_conflict_resolver.py`

**Interfaces:**
- Consumes: `ConsensusEngine`, `Orchestrator` (forward reference), `Message`
- Produces: `ConflictResolver` class with `resolve_conflict`, `detect_conflict`, `build_assessment`, `build_resolution_message`

- [ ] **Step 1: Write failing resolver tests**
  Write 10 tests in `test_conflict_resolver.py` checking the translation of `Message` to `AgentAssessment`, generating output messages, and routing logic for Type D and E.
- [ ] **Step 2: Implement Translation Methods**
  Implement `build_assessment` and `build_resolution_message`.
- [ ] **Step 3: Implement Resolution Logic**
  Implement `detect_conflict`, `handle_false_positive`, `handle_regulatory_conflict`, and `resolve_conflict`. Integrate with Orchestrator's `audit_chain` dependency for logging.
- [ ] **Step 4: Verify**
  `pytest tests/test_conflict_resolver.py`
- [ ] **Step 5: Commit**
  `git add src/mcms/core/conflict_resolver.py tests/test_conflict_resolver.py && git commit -m "feat: implement conflict resolver coordinator"`

### Task 6: Orchestrator Integration

**Files:**
- Modify: `src/mcms/core/orchestrator.py`
- Modify: `tests/test_orchestrator.py`

**Interfaces:**
- Consumes: `ConflictResolver`
- Produces: Enhanced `Orchestrator` with message correlation buffering and async conflict routing.

- [ ] **Step 1: Write failing integration tests**
  Update `test_orchestrator.py` to test that sending multiple ALERTs with the same `correlation_id` triggers the conflict resolver instead of direct dispatch.
- [ ] **Step 2: Enhance Orchestrator state**
  Add a `_correlation_buffer: dict[str, list[Message]]` and `_alert_timestamps: dict[str, float]`. Add config parsing for `conflict_detection_window_seconds`.
- [ ] **Step 3: Modify Dispatch Logic**
  Update `dispatch` to catch `ALERT` messages with a `correlation_id`. If correlated, buffer them. If buffer window expires, pass to `route_to_resolver(messages)`. (Note: Since orchestrator is async, this may involve spawning an `asyncio.create_task` that sleeps for the window duration before evaluating the buffer).
- [ ] **Step 4: Verify**
  `pytest tests/test_orchestrator.py`
- [ ] **Step 5: Commit**
  `git add src/mcms/core/orchestrator.py tests/test_orchestrator.py && git commit -m "feat: integrate consensus correlation buffer in orchestrator"`

### Task 7: Final Validation

- [ ] **Step 1: Run complete suite**
  `pytest -v` (Ensure 100+ tests pass).
- [ ] **Step 2: Run Strict Type Checker**
  `mypy --strict src/`
- [ ] **Step 3: Run Linter/Formatter**
  `ruff check src/ tests/`
- [ ] **Step 4: End-to-end check**
  `python -c "from src.mcms.core.consensus import ConsensusEngine; from src.mcms.core.config import Config; ce = ConsensusEngine(Config()); print('ConsensusEngine OK')"`
