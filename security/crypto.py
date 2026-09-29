"""
Security: Encryption & Key Management
AES-256-GCM for data at rest; Fernet for key wrapping; HKDF for key derivation.
"""
from __future__ import annotations
import os
import base64
import secrets
import hashlib
from dataclasses import dataclass
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

# ──────────────────────────────────────────────────────────────────────────────
# Key Management
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class KeyBundle:
    """Versioned encryption keys for rotation."""
    version: int
    master_key: bytes          # 32 bytes (AES-256)
    created_at: float          # unix timestamp

class KeyManager:
    """
    Manages encryption keys with versioning for rotation.
    In production: integrate with AWS KMS / HashiCorp Vault / Azure Key Vault.
    For dev: derives from MASTER_KEY env var.
    """
    def __init__(self, master_key_b64: Optional[str] = None):
        self._keys: dict[int, KeyBundle] = {}
        self._current_version = 1
        
        if master_key_b64:
            master = base64.urlsafe_b64decode(master_key_b64)
        else:
            # Dev fallback: derive from env or generate ephemeral
            env_key = os.environ.get("MASTER_ENCRYPTION_KEY")
            if env_key:
                master = base64.urlsafe_b64decode(env_key)
            else:
                # Generate deterministic dev key from fixed salt (NOT for production)
                master = HKDF(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b"asha-vaani-dev-salt",
                    info=b"master-key-v1"
                ).derive(secrets.token_bytes(32))
        
        self._keys[1] = KeyBundle(version=1, master_key=master, created_at=__import__('time').time())

    def current(self) -> KeyBundle:
        return self._keys[self._current_version]

    def get(self, version: int) -> KeyBundle:
        if version not in self._keys:
            raise ValueError(f"Key version {version} not found")
        return self._keys[version]

    def rotate(self) -> KeyBundle:
        """Create new key version; old keys retained for decryption."""
        self._current_version += 1
        new_master = secrets.token_bytes(32)
        bundle = KeyBundle(
            version=self._current_version,
            master_key=new_master,
            created_at=__import__('time').time()
        )
        self._keys[self._current_version] = bundle
        return bundle

    def derive_data_key(self, bundle: KeyBundle, context: bytes) -> bytes:
        """Derive per-record data key using HKDF.
        Uses master_key as IKM for deterministic derivation."""
        return HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"asha-vaani-salt-v1",  # Fixed salt for determinism
            info=context
        ).derive(bundle.master_key)


# ──────────────────────────────────────────────────────────────────────────────
# Field-Level Encryption (AES-256-GCM)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EncryptedBlob:
    """Encrypted payload with metadata for decryption."""
    version: int
    nonce: bytes           # 12 bytes for GCM
    ciphertext: bytes
    tag: bytes             # 16 bytes GCM tag
    context: bytes         # Key derivation context

    def to_bytes(self) -> bytes:
        """Serialize: version(1) | nonce(12) | tag(16) | context_len(2) | context | ciphertext"""
        ctx_len = len(self.context).to_bytes(2, 'big')
        return bytes([self.version]) + self.nonce + self.tag + ctx_len + self.context + self.ciphertext

    @classmethod
    def from_bytes(cls, data: bytes) -> EncryptedBlob:
        version = data[0]
        nonce = data[1:13]
        tag = data[13:29]
        ctx_len = int.from_bytes(data[29:31], 'big')
        context = data[31:31+ctx_len]
        ciphertext = data[31+ctx_len:]
        return cls(version, nonce, ciphertext, tag, context)


class FieldEncryptor:
    """Encrypt/decrypt individual fields (PII, patient data, etc.)."""
    def __init__(self, key_manager: KeyManager):
        self.km = key_manager

    def encrypt(self, plaintext: str, context: str, version: Optional[int] = None) -> str:
        """Encrypt string → base64 encoded blob."""
        bundle = self.km.current() if version is None else self.km.get(version)
        data_key = self.km.derive_data_key(bundle, context.encode())
        aes = AESGCM(data_key)
        nonce = secrets.token_bytes(12)
        ct = aes.encrypt(nonce, plaintext.encode(), None)
        # AESGCM returns ciphertext || tag (16 bytes)
        ciphertext, tag = ct[:-16], ct[-16:]
        blob = EncryptedBlob(bundle.version, nonce, ciphertext, tag, context.encode())
        return base64.urlsafe_b64encode(blob.to_bytes()).decode()

    def decrypt(self, encoded: str, context: str) -> str:
        """Decrypt base64 encoded blob → string."""
        blob = EncryptedBlob.from_bytes(base64.urlsafe_b64decode(encoded))
        bundle = self.km.get(blob.version)
        data_key = self.km.derive_data_key(bundle, blob.context)
        aes = AESGCM(data_key)
        ct_with_tag = blob.ciphertext + blob.tag
        plaintext = aes.decrypt(blob.nonce, ct_with_tag, None)
        return plaintext.decode()

    def encrypt_bytes(self, data: bytes, context: str, version: Optional[int] = None) -> str:
        bundle = self.km.current() if version is None else self.km.get(version)
        data_key = self.km.derive_data_key(bundle, context.encode())
        aes = AESGCM(data_key)
        nonce = secrets.token_bytes(12)
        ct = aes.encrypt(nonce, data, None)
        ciphertext, tag = ct[:-16], ct[-16:]
        blob = EncryptedBlob(bundle.version, nonce, ciphertext, tag, context.encode())
        return base64.urlsafe_b64encode(blob.to_bytes()).decode()

    def decrypt_bytes(self, encoded: str, context: str) -> bytes:
        blob = EncryptedBlob.from_bytes(base64.urlsafe_b64decode(encoded))
        bundle = self.km.get(blob.version)
        data_key = self.km.derive_data_key(bundle, blob.context)
        aes = AESGCM(data_key)
        ct_with_tag = blob.ciphertext + blob.tag
        return aes.decrypt(blob.nonce, ct_with_tag, None)


# ──────────────────────────────────────────────────────────────────────────────
# High-Level Helpers for Common Types
# ──────────────────────────────────────────────────────────────────────────────

class ProfileEncryptor:
    """Encrypt/decrypt entire ASHA profile JSON."""
    def __init__(self, field_encryptor: FieldEncryptor):
        self.fe = field_encryptor
        self.ctx = b"asha-profile"

    def encrypt(self, profile_dict: dict) -> str:
        import json
        return self.fe.encrypt(json.dumps(profile_dict, ensure_ascii=False), self.ctx.decode())

    def decrypt(self, encrypted: str) -> dict:
        import json
        return json.loads(self.fe.decrypt(encrypted, self.ctx.decode()))


class ConsentEncryptor:
    """Encrypt consent flags."""
    def __init__(self, field_encryptor: FieldEncryptor):
        self.fe = field_encryptor
        self.ctx = b"consent-flags"

    def encrypt(self, flags: dict) -> str:
        import json
        return self.fe.encrypt(json.dumps(flags), self.ctx.decode())

    def decrypt(self, encrypted: str) -> dict:
        import json
        return json.loads(self.fe.decrypt(encrypted, self.ctx.decode()))


# ──────────────────────────────────────────────────────────────────────────────
# Singleton Instances (initialized at app startup)
# ──────────────────────────────────────────────────────────────────────────────

_key_manager: Optional[KeyManager] = None
_field_encryptor: Optional[FieldEncryptor] = None
_profile_encryptor: Optional[ProfileEncryptor] = None
_consent_encryptor: Optional[ConsentEncryptor] = None


def init_crypto(master_key_b64: Optional[str] = None) -> None:
    global _key_manager, _field_encryptor, _profile_encryptor, _consent_encryptor
    _key_manager = KeyManager(master_key_b64)
    _field_encryptor = FieldEncryptor(_key_manager)
    _profile_encryptor = ProfileEncryptor(_field_encryptor)
    _consent_encryptor = ConsentEncryptor(_field_encryptor)


def get_key_manager() -> KeyManager:
    if _key_manager is None:
        init_crypto()
    return _key_manager


def get_field_encryptor() -> FieldEncryptor:
    if _field_encryptor is None:
        init_crypto()
    return _field_encryptor


def get_profile_encryptor() -> ProfileEncryptor:
    if _profile_encryptor is None:
        init_crypto()
    return _profile_encryptor


def get_consent_encryptor() -> ConsentEncryptor:
    if _consent_encryptor is None:
        init_crypto()
    return _consent_encryptor