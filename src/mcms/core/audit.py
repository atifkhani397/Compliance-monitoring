"""Cryptographic hash-chain audit trail builder for MACMS."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.mcms.core.exceptions import AuditIntegrityError

GENESIS_PREVIOUS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


class AuditEntry(BaseModel):
    """Immutable audit entry containing data payload and SHA-256 hash linkage."""

    model_config = ConfigDict(frozen=True)

    index: int = Field(ge=0, description="Sequential 0-indexed position in audit chain.")
    timestamp: str = Field(description="ISO 8601 UTC timestamp when entry was recorded.")
    previous_hash: str = Field(description="SHA-256 hex string of the preceding audit entry.")
    current_hash: str = Field(description="SHA-256 hex string of this audit entry.")
    data: dict[str, Any] = Field(description="Structured data payload recorded in audit log.")
    agent_id: str = Field(description="ID of agent recording the audit entry.")


class AuditChain:
    """Tamper-evident audit trail backed by cryptographic hash chaining."""

    def __init__(self, initial_seed: str = "MERIDIAN_GENESIS_BLOCK") -> None:
        self._entries: list[AuditEntry] = []
        self._initial_seed = initial_seed

    @property
    def entries(self) -> list[AuditEntry]:
        """Returns read-only list of audit chain entries."""
        return list(self._entries)

    def _compute_hash(
        self, previous_hash: str, timestamp: str, data: dict[str, Any], agent_id: str
    ) -> str:
        """Computes deterministic SHA-256 hash of entry elements."""
        canonical_data = json.dumps(data, sort_keys=True, separators=(",", ":"))
        hasher = hashlib.sha256()
        hasher.update(previous_hash.encode("utf-8"))
        hasher.update(timestamp.encode("utf-8"))
        hasher.update(agent_id.encode("utf-8"))
        hasher.update(canonical_data.encode("utf-8"))
        return hasher.hexdigest()

    def append(self, entry_data: dict[str, Any], agent_id: str) -> AuditEntry:
        """Appends a new audit record to the chain with deterministic cryptographic hashing."""
        index = len(self._entries)
        now_utc = datetime.now(UTC).isoformat()

        if index == 0:
            previous_hash = hashlib.sha256(self._initial_seed.encode("utf-8")).hexdigest()
        else:
            previous_hash = self._entries[-1].current_hash

        current_hash = self._compute_hash(previous_hash, now_utc, entry_data, agent_id)

        entry = AuditEntry(
            index=index,
            timestamp=now_utc,
            previous_hash=previous_hash,
            current_hash=current_hash,
            data=entry_data,
            agent_id=agent_id,
        )
        self._entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        """Verifies integrity of the entire cryptographic audit chain.

        Returns True if chain is intact.
        Raises AuditIntegrityError if any link in the chain is corrupted.
        """
        if not self._entries:
            return True

        expected_prev_hash = hashlib.sha256(self._initial_seed.encode("utf-8")).hexdigest()

        for idx, entry in enumerate(self._entries):
            if entry.index != idx:
                raise AuditIntegrityError(
                    f"Audit entry index mismatch at position {idx}: expected {idx}, got {entry.index}",
                    entry_index=idx,
                )

            if entry.previous_hash != expected_prev_hash:
                raise AuditIntegrityError(
                    f"Previous hash link mismatch at index {idx}: entry previous_hash does not match expected",
                    entry_index=idx,
                )

            recalculated_hash = self._compute_hash(
                entry.previous_hash, entry.timestamp, entry.data, entry.agent_id
            )

            if entry.current_hash != recalculated_hash:
                raise AuditIntegrityError(
                    f"Hash corruption detected at audit entry index {idx}: current_hash does not match payload hash",
                    entry_index=idx,
                )

            expected_prev_hash = entry.current_hash

        return True

    def get_entry(self, index: int) -> AuditEntry:
        """Retrieves audit entry at specified index."""
        if index < 0 or index >= len(self._entries):
            raise IndexError(
                f"Audit entry index out of bounds: {index} (chain length: {len(self._entries)})"
            )
        return self._entries[index]

    def export_to_jsonl(self) -> str:
        """Exports the entire audit chain as line-delimited JSON strings."""
        lines = [entry.model_dump_json() for entry in self._entries]
        return "\n".join(lines)
