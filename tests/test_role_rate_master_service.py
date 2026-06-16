import pytest

from app.models.role_rate import RoleRate
from app.services.role_rate_master_service import (
    RoleRateMasterDecryptionError,
    RoleRateMasterDuplicateError,
    RoleRateMasterService,
)


def _role_rate(
    role_rate_id: str,
    role_name: str = "Manager",
    hourly_rate: int = 6000,
) -> RoleRate:
    return RoleRate(
        role_rate_id=role_rate_id,
        is_active=True,
        role_name=role_name,
        hourly_rate=hourly_rate,
    )


def test_load_role_rates_returns_empty_list_when_file_missing(tmp_path):
    service = RoleRateMasterService(
        tmp_path / "data" / "role_rates.enc",
        tmp_path / "logs" / "error.log",
    )

    assert service.load_role_rates("LIC-TEST-001") == []


def test_save_and_load_role_rates_round_trip_encrypted_file(tmp_path):
    master_path = tmp_path / "data" / "role_rates.enc"
    service = RoleRateMasterService(master_path, tmp_path / "logs" / "error.log")
    role_rates = [
        _role_rate("R-000001", role_name="Manager", hourly_rate=6000),
        _role_rate("R-000002", role_name="Staff", hourly_rate=3000),
    ]

    service.save_role_rates(role_rates, "LIC-TEST-001")
    loaded_role_rates = service.load_role_rates("LIC-TEST-001")

    assert loaded_role_rates == role_rates
    encrypted_bytes = master_path.read_bytes()
    assert b"Manager" not in encrypted_bytes
    assert b"6000" not in encrypted_bytes


def test_save_role_rates_rejects_duplicate_role_name(tmp_path):
    log_file = tmp_path / "logs" / "error.log"
    service = RoleRateMasterService(
        tmp_path / "data" / "role_rates.enc",
        log_file,
    )
    role_rates = [
        _role_rate("R-000001", role_name="Manager"),
        _role_rate("R-000002", role_name=" Manager "),
    ]

    with pytest.raises(RoleRateMasterDuplicateError):
        service.save_role_rates(role_rates, "LIC-TEST-001")

    log_content = log_file.read_text(encoding="utf-8")
    assert "role_rate_master_save" in log_content
    assert "RoleRateMasterError" in log_content
    assert "RoleRateMasterDuplicateError" in log_content
    assert "Manager" not in log_content
    assert "6000" not in log_content


def test_load_role_rates_raises_decryption_error_for_wrong_license_id(tmp_path):
    service = RoleRateMasterService(
        tmp_path / "data" / "role_rates.enc",
        tmp_path / "logs" / "error.log",
    )
    service.save_role_rates([_role_rate("R-000001")], "LIC-TEST-001")

    with pytest.raises(RoleRateMasterDecryptionError):
        service.load_role_rates("LIC-TEST-002")


def test_load_role_rates_raises_decryption_error_for_invalid_payload(tmp_path):
    master_path = tmp_path / "data" / "role_rates.enc"
    master_path.parent.mkdir(parents=True)
    master_path.write_bytes(b"not encrypted data")
    service = RoleRateMasterService(master_path, tmp_path / "logs" / "error.log")

    with pytest.raises(RoleRateMasterDecryptionError):
        service.load_role_rates("LIC-TEST-001")
