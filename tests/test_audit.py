"""Test cases for MACMS AuditChain cryptographic verification."""

import json

import pytest

from src.mcms.core.audit import AuditChain, AuditEntry
from src.mcms.core.exceptions import AuditIntegrityError


def test_single_entry_append():
    chain = AuditChain()
    entry = chain.append({"action": "AGENT_STARTUP", "status": "OK"}, agent_id="agent-tm-001")
    assert isinstance(entry, AuditEntry)
    assert entry.index == 0
    assert len(entry.current_hash) == 64
    assert len(chain.entries) == 1


def test_valid_chain_integrity_verification():
    chain = AuditChain()
    chain.append({"event": "TRADE_INGESTED", "trade_id": "T-100"}, agent_id="agent-tm-001")
    chain.append({"event": "NLP_SCAN_COMPLETE", "matches": 0}, agent_id="agent-cs-001")
    chain.append({"event": "CIRCULAR_INGESTED", "circular_id": "RBI-99"}, agent_id="agent-ru-001")

    assert chain.verify_chain() is True


def test_tampered_data_fails_chain_verification():
    chain = AuditChain()
    chain.append({"event": "INITIAL"}, agent_id="agent-tm-001")
    chain.append({"event": "SECOND"}, agent_id="agent-cs-001")

    # Manually tamper with internal entry data
    tampered_entry = AuditEntry(
        index=chain._entries[1].index,
        timestamp=chain._entries[1].timestamp,
        previous_hash=chain._entries[1].previous_hash,
        current_hash=chain._entries[1].current_hash,
        data={"event": "TAMPERED_DATA"},  # Data altered!
        agent_id=chain._entries[1].agent_id,
    )
    chain._entries[1] = tampered_entry

    with pytest.raises(AuditIntegrityError) as exc_info:
        chain.verify_chain()
    assert exc_info.value.entry_index == 1
    assert "Hash corruption detected" in exc_info.value.message


def test_empty_chain_verification():
    chain = AuditChain()
    assert chain.verify_chain() is True
    assert len(chain.entries) == 0


def test_export_to_jsonl_format():
    chain = AuditChain()
    chain.append({"event": "LOG_1"}, agent_id="agent-tm-001")
    chain.append({"event": "LOG_2"}, agent_id="agent-cs-001")

    jsonl_output = chain.export_to_jsonl()
    lines = jsonl_output.strip().split("\n")
    assert len(lines) == 2

    parsed_line_1 = json.loads(lines[0])
    assert parsed_line_1["index"] == 0
    assert parsed_line_1["data"]["event"] == "LOG_1"


def test_deterministic_hash_generation():
    chain1 = AuditChain(initial_seed="TEST_SEED")
    chain2 = AuditChain(initial_seed="TEST_SEED")

    # Append entries with identical timestamps and data
    fixed_time = "2026-08-17T12:00:00.000000+00:00"
    data = {"metric": "CPU_UTIL", "val": 42}

    h1 = chain1._compute_hash("PREV", fixed_time, data, "agent-tm-001")
    h2 = chain2._compute_hash("PREV", fixed_time, data, "agent-tm-001")

    assert h1 == h2


def test_get_entry_bounds():
    chain = AuditChain()
    chain.append({"event": "ENTRY_0"}, agent_id="agent-tm-001")
    assert chain.get_entry(0).data == {"event": "ENTRY_0"}

    with pytest.raises(IndexError):
        chain.get_entry(5)
