import pytest

from app.services.license_settings_service import (
    DEVICE_ROLE_MASTER,
    DEVICE_ROLE_VIEWER,
    LicenseSettingsValidationError,
    ValidatedLicenseDeviceSettings,
    calculate_license_check_digit,
    normalize_license_id,
    validate_device_role,
    validate_license_device_settings,
    validate_license_id,
)

VALID_LICENSE_ID = "MCT-202606-7K4P-Q9X2-Z"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (f" {VALID_LICENSE_ID.lower()} ", VALID_LICENSE_ID),
        ("ＭＣＴ－２０２６０６－７Ｋ４Ｐ－Ｑ９Ｘ２－Ｚ", VALID_LICENSE_ID),
        ("MCT−202606ー7K4P-Q9X2-Z", VALID_LICENSE_ID),
    ],
)
def test_normalize_license_id(value, expected):
    assert normalize_license_id(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (VALID_LICENSE_ID, VALID_LICENSE_ID),
        (f" {VALID_LICENSE_ID.lower()} ", VALID_LICENSE_ID),
        ("ＭＣＴ－２０２６０６－７Ｋ４Ｐ－Ｑ９Ｘ２－Ｚ", VALID_LICENSE_ID),
    ],
)
def test_validate_license_id_accepts_valid_values(value, expected):
    assert validate_license_id(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "LIC-ABCD-1234",
        "MCT-202613-7K4P-Q9X2-Z",
        "MCT-202606-7K4P-Q9X2-A",
        "MCT-202606-0K4P-Q9X2-Z",
        "MCT-202606-7K4P-Q9X2",
        "MCT_202606_7K4P_Q9X2_Z",
        123,
    ],
)
def test_validate_license_id_rejects_invalid_values(value):
    with pytest.raises(LicenseSettingsValidationError):
        validate_license_id(value)


def test_calculate_license_check_digit_returns_expected_value():
    assert calculate_license_check_digit("MCT2026067K4PQ9X2") == "Z"


@pytest.mark.parametrize("device_role", [DEVICE_ROLE_MASTER, DEVICE_ROLE_VIEWER])
def test_validate_device_role_accepts_master_and_viewer(device_role):
    assert validate_device_role(device_role) == device_role


@pytest.mark.parametrize("device_role", ["", "parent", "MASTER", 1])
def test_validate_device_role_rejects_invalid_values(device_role):
    with pytest.raises(LicenseSettingsValidationError):
        validate_device_role(device_role)


def test_validate_license_device_settings_returns_normalized_settings():
    settings = validate_license_device_settings(
        f" {VALID_LICENSE_ID.lower()} ",
        DEVICE_ROLE_MASTER,
    )

    assert settings == ValidatedLicenseDeviceSettings(
        license_id=VALID_LICENSE_ID,
        device_role=DEVICE_ROLE_MASTER,
    )
