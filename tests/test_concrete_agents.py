"""Tests for MCMS concrete agent skeletons."""

import pytest

from src.mcms.agents.communication_scanner import CommunicationScanner
from src.mcms.agents.regulatory_tracker import RegulatoryTracker
from src.mcms.agents.report_generator import ReportGenerator
from src.mcms.agents.transaction_monitor import TransactionMonitor


class TestTransactionMonitor:
    """Tests for TransactionMonitor agent."""

    def test_agent_id(self) -> None:
        tm = TransactionMonitor()
        assert tm.agent_id == "agent-tm-001"

    def test_capabilities(self) -> None:
        tm = TransactionMonitor()
        expected = [
            "pattern_detection",
            "threshold_monitoring",
            "temporal_analysis",
            "counterparty_analysis",
            "cross_market_surveillance",
        ]
        assert tm.capabilities == expected

    @pytest.mark.asyncio
    async def test_process_message_raises(self) -> None:
        tm = TransactionMonitor()
        with pytest.raises(NotImplementedError):
            msg = tm.heartbeat()
            await tm.process_message(msg)

    def test_heartbeat_generation(self) -> None:
        tm = TransactionMonitor()
        hb = tm.heartbeat()
        assert hb.sender_agent_id == "agent-tm-001"

    def test_health_check(self) -> None:
        tm = TransactionMonitor()
        health = tm.health_check()
        assert health["agent_id"] == "agent-tm-001"


class TestCommunicationScanner:
    """Tests for CommunicationScanner agent."""

    def test_agent_id(self) -> None:
        cs = CommunicationScanner()
        assert cs.agent_id == "agent-cs-001"

    def test_capabilities(self) -> None:
        cs = CommunicationScanner()
        expected = [
            "keyword_detection",
            "sentiment_analysis",
            "information_barrier_monitoring",
            "record_keeping_compliance",
            "privilege_detection",
        ]
        assert cs.capabilities == expected

    @pytest.mark.asyncio
    async def test_process_message_raises(self) -> None:
        cs = CommunicationScanner()
        with pytest.raises(NotImplementedError):
            msg = cs.heartbeat()
            await cs.process_message(msg)


class TestRegulatoryTracker:
    """Tests for RegulatoryTracker agent."""

    def test_agent_id(self) -> None:
        ru = RegulatoryTracker()
        assert ru.agent_id == "agent-ru-001"

    def test_capabilities(self) -> None:
        ru = RegulatoryTracker()
        expected = [
            "regulatory_feed_monitoring",
            "impact_assessment",
            "timeline_extraction",
            "cross_regulation_conflict",
            "precedent_analysis",
        ]
        assert ru.capabilities == expected

    @pytest.mark.asyncio
    async def test_process_message_raises(self) -> None:
        ru = RegulatoryTracker()
        with pytest.raises(NotImplementedError):
            msg = ru.heartbeat()
            await ru.process_message(msg)


class TestReportGenerator:
    """Tests for ReportGenerator agent."""

    def test_agent_id(self) -> None:
        rg = ReportGenerator()
        assert rg.agent_id == "agent-rg-001"

    def test_capabilities(self) -> None:
        rg = ReportGenerator()
        expected = [
            "scheduled_reports",
            "event_triggered_reporting",
            "multi_audience_adaptation",
            "evidence_compilation",
            "regulatory_filing_preparation",
        ]
        assert rg.capabilities == expected

    @pytest.mark.asyncio
    async def test_process_message_raises(self) -> None:
        rg = ReportGenerator()
        with pytest.raises(NotImplementedError):
            msg = rg.heartbeat()
            await rg.process_message(msg)


class TestSignAndVerify:
    """Tests for message signing across all agents."""

    def test_sign_and_verify_on_each_agent(self) -> None:
        agents = [
            TransactionMonitor(),
            CommunicationScanner(),
            RegulatoryTracker(),
            ReportGenerator(),
        ]
        for agent in agents:
            hb = agent.heartbeat()
            assert agent.verify_signature(hb), f"{agent.agent_id} failed signature verification"


class TestConfigLoading:
    """Tests for config propagation to agents."""

    def test_config_per_agent(self) -> None:
        config = {"secret_key": "custom-key-123"}
        agents = [
            TransactionMonitor(config=config),
            CommunicationScanner(config=config),
            RegulatoryTracker(config=config),
            ReportGenerator(config=config),
        ]
        for agent in agents:
            assert agent.secret_key == "custom-key-123"
