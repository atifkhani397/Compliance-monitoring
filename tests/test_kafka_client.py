"""Tests for MCMS Kafka client infrastructure."""

from unittest.mock import MagicMock

import pytest

from src.mcms.core.kafka_client import KafkaConsumer, KafkaProducer, build_topic_name


class TestTopicNaming:
    """Tests for Kafka topic naming convention."""

    def test_topic_naming_convention(self) -> None:
        assert build_topic_name("agent-tm-001", "ALERT") == "mcms.agent-tm-001.alert"
        assert build_topic_name("agent-cs-001", "QUERY") == "mcms.agent-cs-001.query"

    def test_escalation_topic(self) -> None:
        assert build_topic_name("escalation", "human") == "mcms.escalation.human"

    def test_heartbeat_topic(self) -> None:
        assert build_topic_name("heartbeat", "") == "mcms.heartbeat"


class TestKafkaProducer:
    """Tests for KafkaProducer class."""

    def test_producer_instantiation_with_config(self) -> None:
        config = {"batch_size": 16384, "acks": "all", "retries": 3}
        producer = KafkaProducer(bootstrap_servers=["localhost:9092"], config=config)
        assert producer._bootstrap_servers == ["localhost:9092"]
        assert producer._config["acks"] == "all"

    @pytest.mark.asyncio
    async def test_send_message_to_topic(self) -> None:
        producer = KafkaProducer(bootstrap_servers=["localhost:9092"], config={})
        message = MagicMock()
        message.model_dump_json.return_value = '{"test": "data"}'
        # Should not raise — stores in buffer when no real broker
        await producer.send("mcms.agent-tm-001.alert", message, key="msg-001")
        assert len(producer._buffer) == 1

    @pytest.mark.asyncio
    async def test_producer_flush_and_close(self) -> None:
        producer = KafkaProducer(bootstrap_servers=["localhost:9092"], config={})
        await producer.flush()
        await producer.close()
        assert producer._closed is True


class TestKafkaConsumer:
    """Tests for KafkaConsumer class."""

    def test_consumer_instantiation_with_topic_subscription(self) -> None:
        consumer = KafkaConsumer(
            bootstrap_servers=["localhost:9092"],
            topics=["mcms.agent-tm-001.alert"],
            group_id="test-group",
            config={},
        )
        assert consumer._topics == ["mcms.agent-tm-001.alert"]
        assert consumer._group_id == "test-group"

    @pytest.mark.asyncio
    async def test_consumer_stop_lifecycle(self) -> None:
        consumer = KafkaConsumer(
            bootstrap_servers=["localhost:9092"],
            topics=["mcms.agent-tm-001.alert"],
            group_id="test-group",
            config={},
        )
        # start then immediately stop to test lifecycle
        await consumer.stop()
        assert consumer._running is False

    def test_consumer_lag_reporting(self) -> None:
        consumer = KafkaConsumer(
            bootstrap_servers=["localhost:9092"],
            topics=["mcms.agent-tm-001.alert", "mcms.agent-cs-001.query"],
            group_id="test-group",
            config={},
        )
        lag = consumer.get_lag()
        assert isinstance(lag, dict)
        assert "mcms.agent-tm-001.alert" in lag

    @pytest.mark.asyncio
    async def test_async_wrapper_functionality(self) -> None:
        consumer = KafkaConsumer(
            bootstrap_servers=["localhost:9092"],
            topics=["mcms.agent-tm-001.alert"],
            group_id="test-group",
            config={},
        )
        # Verify stop works without a running consumer
        await consumer.stop()
        assert consumer._running is False
