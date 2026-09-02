"""Security architecture management for MACMS inter-agent communication, mTLS, encryption, and PII protection."""

import datetime
import hashlib
import os
import secrets
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from src.mcms.core.exceptions import SecurityError


class SecurityManager:
    """Production-grade security manager handling mTLS, AES-256-GCM encryption, key rotation, nonces, and PII hashing."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config: dict[str, Any] = config or {}
        self._keys: dict[str, bytes] = {}
        # Initialize default master key using 100,000 PBKDF2 iterations
        master_secret = self.config.get("master_key", "default-macms-master-key-2026").encode(
            "utf-8"
        )
        salt = self.config.get("pbkdf2_salt", "meridian-global-salt").encode("utf-8")
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        self._keys["default"] = kdf.derive(master_secret)

    def verify_mtls(self, cert: bytes, expected_agent_id: str) -> bool:
        """Verifies client X.509 certificate for agent identity binding and expiration."""
        try:
            try:
                x509_cert = x509.load_pem_x509_certificate(cert)
            except Exception:
                x509_cert = x509.load_der_x509_certificate(cert)

            # Check Common Name (CN)
            cns = x509_cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
            if not cns or cns[0].value != expected_agent_id:
                return False

            # Check expiration
            now = datetime.datetime.now(datetime.UTC)
            not_before = x509_cert.not_valid_before_utc
            not_after = x509_cert.not_valid_after_utc
            return not_before <= now <= not_after
        except Exception as err:
            raise SecurityError(f"Certificate parsing/verification failed: {err}") from err

    def encrypt_payload(self, payload: bytes, key_id: str = "default") -> bytes:
        """Encrypts payload with AES-256-GCM."""
        if key_id not in self._keys:
            raise SecurityError(f"Encryption key identifier '{key_id}' not found in registry.")
        try:
            aesgcm = AESGCM(self._keys[key_id])
            nonce = os.urandom(12)
            ciphertext = aesgcm.encrypt(nonce, payload, None)
            # Prefix 12-byte nonce to ciphertext
            return nonce + ciphertext
        except Exception as err:
            raise SecurityError(f"Payload encryption failed: {err}") from err

    def decrypt_payload(self, ciphertext: bytes, key_id: str = "default") -> bytes:
        """Decrypts AES-256-GCM ciphertext and verifies authenticity tag."""
        if key_id not in self._keys:
            raise SecurityError(f"Decryption key identifier '{key_id}' not found in registry.")
        if len(ciphertext) < 28:  # 12-byte nonce + 16-byte tag
            raise SecurityError("Ciphertext payload too short or corrupted.")
        try:
            aesgcm = AESGCM(self._keys[key_id])
            nonce = ciphertext[:12]
            actual_ciphertext = ciphertext[12:]
            return aesgcm.decrypt(nonce, actual_ciphertext, None)
        except Exception as err:
            raise SecurityError(f"Payload decryption failed or payload tampered: {err}") from err

    def rotate_key(self, key_id: str) -> str:
        """Generates a new AES-256 key, registers it under key_id_v2, and returns the new key ID."""
        new_key = AESGCM.generate_key(bit_length=256)
        new_key_id = f"{key_id}_v{len(self._keys) + 1}"
        self._keys[new_key_id] = new_key
        return new_key_id

    def check_certificate_expiry(self, cert: bytes) -> datetime.datetime:
        """Parses certificate and returns UTC expiration datetime."""
        try:
            try:
                x509_cert = x509.load_pem_x509_certificate(cert)
            except Exception:
                x509_cert = x509.load_der_x509_certificate(cert)
            return x509_cert.not_valid_after_utc
        except Exception as err:
            raise SecurityError(f"Failed to parse certificate expiry: {err}") from err

    def generate_nonce(self, length: int = 32) -> str:
        """Generates a cryptographically secure random hex nonce string of given byte length."""
        return secrets.token_hex(length // 2 if length % 2 == 0 else length)

    def hash_sensitive_data(self, data: str, salt: str | None = None) -> str:
        """Hashes PII string using SHA-256 with salt."""
        effective_salt = salt or self.config.get("pii_salt", "macms-pii-salt-2026")
        salted = f"{effective_salt}:{data}".encode()
        return hashlib.sha256(salted).hexdigest()
