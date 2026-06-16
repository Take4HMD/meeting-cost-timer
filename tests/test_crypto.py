import pytest

from app.utils.crypto import (
    DecryptionError,
    decrypt_bytes,
    decrypt_text,
    encrypt_bytes,
    encrypt_text,
    generate_encryption_key,
)


def test_generate_encryption_key_is_stable_for_same_license_id():
    assert generate_encryption_key(" lic-test-001 ") == generate_encryption_key(
        "LIC-TEST-001"
    )


def test_generate_encryption_key_changes_by_license_id():
    assert generate_encryption_key("LIC-TEST-001") != generate_encryption_key(
        "LIC-TEST-002"
    )


def test_generate_encryption_key_rejects_empty_license_id():
    with pytest.raises(ValueError):
        generate_encryption_key("")


def test_encrypt_and_decrypt_bytes_round_trip():
    plain_data = b'{"schema_version":1,"participants":[]}'

    encrypted_data = encrypt_bytes(plain_data, "LIC-TEST-001")
    decrypted_data = decrypt_bytes(encrypted_data, "LIC-TEST-001")

    assert encrypted_data != plain_data
    assert decrypted_data == plain_data


def test_encrypt_and_decrypt_text_round_trip():
    plain_text = '{"schema_version":1,"role_rates":[]}'

    encrypted_data = encrypt_text(plain_text, "LIC-TEST-001")
    decrypted_text = decrypt_text(encrypted_data, "LIC-TEST-001")

    assert decrypted_text == plain_text


def test_decrypt_bytes_raises_decryption_error_for_wrong_license_id():
    encrypted_data = encrypt_bytes(b"secret", "LIC-TEST-001")

    with pytest.raises(DecryptionError):
        decrypt_bytes(encrypted_data, "LIC-TEST-002")


def test_decrypt_bytes_raises_decryption_error_for_invalid_payload():
    with pytest.raises(DecryptionError):
        decrypt_bytes(b"not encrypted data", "LIC-TEST-001")


def test_encrypt_bytes_rejects_non_bytes_payload():
    with pytest.raises(ValueError):
        encrypt_bytes("plain text", "LIC-TEST-001")


def test_encrypt_text_rejects_non_string_payload():
    with pytest.raises(ValueError):
        encrypt_text(b"plain text", "LIC-TEST-001")
