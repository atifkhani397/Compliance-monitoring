"""Tests for MCMS configuration management."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.mcms.core.config import Config
from src.mcms.core.exceptions import ConfigError


class TestConfigFromYAML:
    """Tests for YAML-based configuration loading."""

    def test_load_from_yaml_file(self, tmp_path: Path) -> None:
        config_data = {
            "agents": {"agent-tm-001": {"name": "TM"}},
            "kafka": {"bootstrap_servers": ["localhost:9092"]},
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))
        config = Config(config_path=str(config_file))
        assert config.get("agents.agent-tm-001.name") == "TM"

    def test_nested_key_access_with_dot_notation(self, tmp_path: Path) -> None:
        config_data = {"kafka": {"producer": {"batch_size": 16384, "acks": "all"}}}
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))
        config = Config(config_path=str(config_file))
        assert config.get("kafka.producer.batch_size") == 16384
        assert config.get("kafka.producer.acks") == "all"

    def test_default_value_fallback(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump({"agents": {}}))
        config = Config(config_path=str(config_file))
        assert config.get("nonexistent.key", "fallback") == "fallback"
        assert config.get("nonexistent.key") is None


class TestConfigFromEnvironment:
    """Tests for environment variable overrides."""

    def test_load_from_environment_variables(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump({"kafka": {"bootstrap_servers": ["localhost:9092"]}}))
        with patch.dict(os.environ, {"MCMS_KAFKA_BOOTSTRAP_SERVERS": "broker1:9092,broker2:9092"}):
            config = Config(config_path=str(config_file))
            result = config.get("kafka.bootstrap_servers")
            assert result == ["broker1:9092", "broker2:9092"]


class TestConfigSections:
    """Tests for section-specific config retrieval."""

    def test_agent_specific_config_retrieval(self, tmp_path: Path) -> None:
        config_data = {"agents": {"agent-tm-001": {"name": "TM", "secret_key": "key123"}}}
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))
        config = Config(config_path=str(config_file))
        agent_config = config.get_agent_config("agent-tm-001")
        assert agent_config["name"] == "TM"
        assert agent_config["secret_key"] == "key123"

    def test_kafka_config_retrieval(self, tmp_path: Path) -> None:
        config_data = {
            "kafka": {
                "bootstrap_servers": ["localhost:9092"],
                "producer": {"acks": "all"},
            }
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))
        config = Config(config_path=str(config_file))
        kafka_config = config.get_kafka_config()
        assert kafka_config["bootstrap_servers"] == ["localhost:9092"]

    def test_missing_config_file_raises_error(self) -> None:
        with pytest.raises(ConfigError):
            Config(config_path="/nonexistent/path/config.yaml")
