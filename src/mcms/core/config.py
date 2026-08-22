"""Configuration management for MACMS with YAML file and environment variable support."""

import os
from pathlib import Path
from typing import Any

import yaml

from src.mcms.core.exceptions import ConfigError

_ENV_PREFIX = "MCMS_"


class Config:
    """Hierarchical configuration loader supporting YAML files and environment variable overrides."""

    def __init__(self, config_path: str | None = None) -> None:
        self._data: dict[str, Any] = {}
        if config_path is not None:
            self._load_from_yaml(config_path)
        self._apply_env_overrides()

    def _load_from_yaml(self, config_path: str) -> None:
        """Loads configuration from a YAML file."""
        path = Path(config_path)
        if not path.exists():
            raise ConfigError(f"Configuration file not found: {config_path}")
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data is not None and isinstance(data, dict):
                self._data = data
        except yaml.YAMLError as err:
            raise ConfigError(f"Invalid YAML in configuration file: {err}") from err

    def _apply_env_overrides(self) -> None:
        """Applies environment variable overrides with MCMS_ prefix."""
        for key, value in os.environ.items():
            if key.startswith(_ENV_PREFIX):
                config_key = key[len(_ENV_PREFIX) :].lower().replace("_", ".", 1)
                parts = config_key.split(".", 1)
                if len(parts) == 2:
                    section, field = parts
                    if section not in self._data:
                        self._data[section] = {}
                    if isinstance(self._data[section], dict):
                        # Handle comma-separated lists
                        if "," in value:
                            self._data[section][field] = [v.strip() for v in value.split(",")]
                        else:
                            self._data[section][field] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Access configuration values using dot notation (e.g., 'kafka.producer.acks')."""
        parts = key.split(".")
        current: Any = self._data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def get_agent_config(self, agent_id: str) -> dict[str, Any]:
        """Retrieve agent-specific configuration."""
        agents = self._data.get("agents", {})
        if not isinstance(agents, dict):
            return {}
        config = agents.get(agent_id, {})
        if not isinstance(config, dict):
            return {}
        return dict(config)

    def get_kafka_config(self) -> dict[str, Any]:
        """Retrieve Kafka connection configuration."""
        kafka = self._data.get("kafka", {})
        if not isinstance(kafka, dict):
            return {}
        return dict(kafka)

    def get_audit_config(self) -> dict[str, Any]:
        """Retrieve audit trail configuration."""
        audit = self._data.get("audit", {})
        if not isinstance(audit, dict):
            return {}
        return dict(audit)

    def get_consensus_config(self) -> dict[str, Any]:
        """Retrieve Phase 3 consensus configuration."""
        consensus = self._data.get("consensus", {})
        if not isinstance(consensus, dict):
            return {}
        return dict(consensus)

    def get_escalation_config(self) -> dict[str, Any]:
        """Retrieve Phase 4 escalation configuration."""
        escalation = self._data.get("escalation", {})
        if not isinstance(escalation, dict):
            return {}
        return dict(escalation)

    def get_feedback_config(self) -> dict[str, Any]:
        """Retrieve Phase 4 feedback configuration."""
        feedback = self._data.get("feedback", {})
        if not isinstance(feedback, dict):
            return {}
        return dict(feedback)
