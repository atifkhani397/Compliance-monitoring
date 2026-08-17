"""Transaction Monitor Agent skeleton for MACMS."""

from typing import Any, ClassVar

from src.mcms.agents.base import BaseAgent
from src.mcms.core.message import Message


class TransactionMonitor(BaseAgent):
    """Monitors transaction patterns, thresholds, and cross-market surveillance."""

    agent_id: ClassVar[str] = "agent-tm-001"
    capabilities: ClassVar[list[str]] = [
        "pattern_detection",
        "threshold_monitoring",
        "temporal_analysis",
        "counterparty_analysis",
        "cross_market_surveillance",
    ]

    async def process_message(self, message: Message) -> Message:
        """Process incoming message. Business logic deferred to Phase 3."""
        raise NotImplementedError(
            "TransactionMonitor.process_message: "
            "scenario business logic not yet implemented (Phase 3)"
        )

    async def analyze_transaction(self, transaction_data: dict[str, Any]) -> Message:
        """Skeleton: Analyze transaction data for anomalies."""
        raise NotImplementedError("TransactionMonitor.analyze_transaction not yet implemented")

    async def check_thresholds(self, position_data: dict[str, Any]) -> Message:
        """Skeleton: Check regulatory thresholds against position data."""
        raise NotImplementedError("TransactionMonitor.check_thresholds not yet implemented")
