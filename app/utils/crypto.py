from __future__ import annotations

import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


KDF_ITERATIONS = 390000
KDF_SALT = b"meeting-cost-timer-master-data-v1"


class CryptoError(Exception):
    pass


class DecryptionError(CryptoError):
    pass


def generate_encryption_key(license_id: str) -> bytes:
    normalized_license_id = _normalize_license_id(license_id)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=KDF_SALT,
        iterations=KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(normalized_license_id.encode("utf-8")))


def encrypt_bytes(plain_data: bytes, license_id: str) -> bytes:
    if not isinstance(plain_data, bytes):
        raise ValueError("plain_data must be bytes")
    return Fernet(generate_encryption_key(license_id)).encrypt(plain_data)


def decrypt_bytes(encrypted_data: bytes, license_id: str) -> bytes:
    if not isinstance(encrypted_data, bytes):
        raise ValueError("encrypted_data must be bytes")

    try:
        return Fernet(generate_encryption_key(license_id)).decrypt(encrypted_data)
    except InvalidToken as exc:
        raise DecryptionError("encrypted data could not be decrypted") from exc


def encrypt_text(plain_text: str, license_id: str) -> bytes:
    if not isinstance(plain_text, str):
        raise ValueError("plain_text must be a string")
    return encrypt_bytes(plain_text.encode("utf-8"), license_id)


def decrypt_text(encrypted_data: bytes, license_id: str) -> str:
    return decrypt_bytes(encrypted_data, license_id).decode("utf-8")


def _normalize_license_id(license_id: str) -> str:
    if not isinstance(license_id, str):
        raise ValueError("license_id must be a string")

    normalized = license_id.strip().upper()
    if not normalized:
        raise ValueError("license_id must not be empty")
    return normalized
