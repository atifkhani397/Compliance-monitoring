"""Unit test suite for SecurityManager (mTLS, encryption, key rotation, nonces, PII hashing)."""

import datetime

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from src.mcms.core.exceptions import SecurityError
from src.mcms.core.security import SecurityManager


def generate_self_signed_cert(cn: str, days_valid: int = 90) -> bytes:
    """Helper to generate a self-signed X.509 certificate PEM bytes."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(x509.NameOID.COMMON_NAME, cn),
            x509.NameAttribute(x509.NameOID.ORGANIZATION_NAME, "Meridian Global Bank"),
        ]
    )
    now = datetime.datetime.now(datetime.UTC)
    if days_valid < 0:
        not_before = now + datetime.timedelta(days=days_valid - 1)
        not_after = now + datetime.timedelta(days=days_valid)
    else:
        not_before = now - datetime.timedelta(days=1)
        not_after = now + datetime.timedelta(days=days_valid)

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_before)
        .not_valid_after(not_after)
        .sign(private_key, hashes.SHA256())
    )
    return cert.public_bytes(serialization.Encoding.PEM)


class TestSecurityManager:
    """Test cases for SecurityManager operations."""

    def test_verify_mtls_valid_cert(self) -> None:
        mgr = SecurityManager()
        cert_pem = generate_self_signed_cert("agent-tm-001", days_valid=90)
        assert mgr.verify_mtls(cert_pem, "agent-tm-001") is True

    def test_verify_mtls_wrong_agent_id(self) -> None:
        mgr = SecurityManager()
        cert_pem = generate_self_signed_cert("agent-tm-001", days_valid=90)
        assert mgr.verify_mtls(cert_pem, "agent-cs-001") is False

    def test_verify_mtls_expired_cert(self) -> None:
        mgr = SecurityManager()
        cert_pem = generate_self_signed_cert("agent-tm-001", days_valid=-10)
        assert mgr.verify_mtls(cert_pem, "agent-tm-001") is False

    def test_encrypt_and_decrypt_payload(self) -> None:
        mgr = SecurityManager()
        payload = b"Confidential Compliance Data 2026"
        ciphertext = mgr.encrypt_payload(payload, "default")
        assert ciphertext != payload
        decrypted = mgr.decrypt_payload(ciphertext, "default")
        assert decrypted == payload

    def test_key_rotation(self) -> None:
        mgr = SecurityManager()
        payload = b"Trade Order Payload"
        new_key_id = mgr.rotate_key("default")
        assert new_key_id != "default"
        ciphertext = mgr.encrypt_payload(payload, new_key_id)
        decrypted = mgr.decrypt_payload(ciphertext, new_key_id)
        assert decrypted == payload

    def test_check_certificate_expiry(self) -> None:
        mgr = SecurityManager()
        cert_pem = generate_self_signed_cert("agent-ru-001", days_valid=30)
        expiry = mgr.check_certificate_expiry(cert_pem)
        assert isinstance(expiry, datetime.datetime)
        assert expiry > datetime.datetime.now(datetime.UTC)

    def test_generate_nonce_uniqueness(self) -> None:
        mgr = SecurityManager()
        nonce1 = mgr.generate_nonce(32)
        nonce2 = mgr.generate_nonce(32)
        assert len(nonce1) == 32
        assert len(nonce2) == 32
        assert nonce1 != nonce2

    def test_hash_sensitive_data_salted(self) -> None:
        mgr = SecurityManager()
        pii = "Aadhaar-1234-5678-9012"
        hash1 = mgr.hash_sensitive_data(pii, salt="custom-salt")
        hash2 = mgr.hash_sensitive_data(pii, salt="custom-salt")
        hash3 = mgr.hash_sensitive_data(pii, salt="other-salt")
        assert len(hash1) == 64
        assert hash1 == hash2
        assert hash1 != hash3

    def test_invalid_key_decryption_raises(self) -> None:
        mgr = SecurityManager()
        with pytest.raises(SecurityError, match="not found in registry"):
            mgr.decrypt_payload(b"someciphertextbytes", key_id="nonexistent_key")

    def test_tampered_payload_decryption_raises(self) -> None:
        mgr = SecurityManager()
        payload = b"Tamper Verification Test"
        ciphertext = mgr.encrypt_payload(payload, "default")
        # Tamper last byte of tag
        tampered_ciphertext = ciphertext[:-1] + bytes([ciphertext[-1] ^ 0xFF])
        with pytest.raises(SecurityError, match="failed or payload tampered"):
            mgr.decrypt_payload(tampered_ciphertext, "default")
