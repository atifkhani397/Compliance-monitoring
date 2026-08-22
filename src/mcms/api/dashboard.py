"""FastAPI dashboard API for MACMS Phase 5 observability."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query

from src.mcms.core.exceptions import AuditIntegrityError, DashboardError, ObservabilityError
from src.mcms.core.observability import ObservabilityService

app = FastAPI(title="MACMS Observability Dashboard API", version="1.0.0")
observability = ObservabilityService({"log_path": "data/observability/dashboard-audit.jsonl"})
API_KEY = os.environ.get("MCMS_DASHBOARD_API_KEY", "macms-phase5-api-key")


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Skeleton API-key authentication; full identity auth is reserved for Phase 8."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Valid API key required")


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    if " " in normalized and normalized.endswith(" 00:00"):
        normalized = normalized[:-6] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise HTTPException(status_code=400, detail="Timestamp must be ISO 8601") from error
    return parsed.replace(tzinfo=parsed.tzinfo or UTC)


def _panel(panel: str, timeframe: str) -> dict[str, Any]:
    try:
        return observability.get_dashboard_data(panel, timeframe)
    except DashboardError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/health/system", dependencies=[Depends(require_api_key)])
def system_health(timeframe: str = Query(default="24h")) -> dict[str, Any]:
    return _panel("system_health", timeframe)


@app.get("/health/agents/{agent_id}", dependencies=[Depends(require_api_key)])
def agent_health(agent_id: str, timeframe: str = Query(default="24h")) -> dict[str, Any]:
    data = _panel("system_health", timeframe)
    agents = [agent for agent in data["agents"] if agent["agent_id"] == agent_id]
    return {
        "panel": "agent_health",
        "timeframe": timeframe,
        "agent_id": agent_id,
        "health": agents[0]
        if agents
        else {"agent_id": agent_id, "status": "unknown", "queue_depth": 0.0, "error_count": 0},
    }


@app.get("/compliance/detection-rate", dependencies=[Depends(require_api_key)])
def detection_rate(timeframe: str = Query(default="24h")) -> dict[str, Any]:
    return _panel("compliance_effectiveness", timeframe)


@app.get("/compliance/false-positive-rate", dependencies=[Depends(require_api_key)])
def false_positive_rate(timeframe: str = Query(default="24h")) -> dict[str, Any]:
    data = _panel("compliance_effectiveness", timeframe)
    return {
        "panel": data["panel"],
        "timeframe": data["timeframe"],
        "false_positive_rate_by_violation": data["false_positive_rate_by_violation"],
    }


@app.get("/compliance/time-to-detection", dependencies=[Depends(require_api_key)])
def time_to_detection(timeframe: str = Query(default="24h")) -> dict[str, Any]:
    data = _panel("compliance_effectiveness", timeframe)
    return {
        "panel": data["panel"],
        "timeframe": data["timeframe"],
        "time_to_detection": data["time_to_detection"],
    }


@app.get("/compliance/filing-accuracy", dependencies=[Depends(require_api_key)])
def filing_accuracy(timeframe: str = Query(default="24h")) -> dict[str, Any]:
    data = _panel("compliance_effectiveness", timeframe)
    return {
        "panel": data["panel"],
        "timeframe": data["timeframe"],
        "filing_accuracy": data["filing_accuracy"],
    }


@app.get("/operations/escalations", dependencies=[Depends(require_api_key)])
def escalations(timeframe: str = Query(default="24h")) -> dict[str, Any]:
    data = _panel("operational_intelligence", timeframe)
    return {
        "panel": data["panel"],
        "timeframe": data["timeframe"],
        "escalation_volume_by_tier": data["escalation_volume_by_tier"],
    }


@app.get("/operations/human-patterns", dependencies=[Depends(require_api_key)])
def human_patterns(timeframe: str = Query(default="24h")) -> dict[str, Any]:
    data = _panel("operational_intelligence", timeframe)
    return {
        "panel": data["panel"],
        "timeframe": data["timeframe"],
        "human_decision_patterns": data["human_decision_patterns"],
    }


@app.get("/operations/conflicts", dependencies=[Depends(require_api_key)])
def conflicts(timeframe: str = Query(default="24h")) -> dict[str, Any]:
    data = _panel("operational_intelligence", timeframe)
    return {
        "panel": data["panel"],
        "timeframe": data["timeframe"],
        "conflict_frequency": data["conflict_frequency"],
    }


@app.get("/operations/cost-per-detection", dependencies=[Depends(require_api_key)])
def cost_per_detection(timeframe: str = Query(default="24h")) -> dict[str, Any]:
    data = _panel("operational_intelligence", timeframe)
    return {
        "panel": data["panel"],
        "timeframe": timeframe,
        "cost_per_detection": data["cost_per_detection"],
    }


@app.get("/audit/trail", dependencies=[Depends(require_api_key)])
def audit_trail(
    trace_id: str | None = None,
    agent_id: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> dict[str, Any]:
    start_value = _parse_datetime(start) if start else datetime.now(UTC) - timedelta(days=1)
    end_value = _parse_datetime(end) if end else datetime.now(UTC)
    if start_value > end_value:
        raise HTTPException(status_code=400, detail="start must not be after end")
    try:
        entries = observability.get_audit_trail(trace_id, agent_id, start_value, end_value)
    except (AuditIntegrityError, ObservabilityError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {"entries": [entry.model_dump(mode="json") for entry in entries], "count": len(entries)}


@app.get("/audit/integrity/{start}/{end}", dependencies=[Depends(require_api_key)])
def audit_integrity(start: str, end: str) -> dict[str, Any]:
    start_value = _parse_datetime(start)
    end_value = _parse_datetime(end)
    if start_value > end_value:
        raise HTTPException(status_code=400, detail="start must not be after end")
    try:
        valid = observability.verify_audit_integrity(start_value, end_value)
    except AuditIntegrityError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {"valid": valid, "start": start_value.isoformat(), "end": end_value.isoformat()}
