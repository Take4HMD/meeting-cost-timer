import pytest

from app.services.license_settings_service import (
    DEVICE_ROLE_MASTER,
    DEVICE_ROLE_VIEWER,
    LicenseSettingsValidationError,
    ValidatedLicenseDeviceSettings,
    normalize_license_id,
    validate_device_role,
    validate_license_device_settings,
    validate_license_id,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (" lic-abcd-1234 ", "LIC-ABCD-1234"),
        ("ＬＩＣ－ＡＢＣＤ－１２３４", "LIC-ABCD-1234"),
        ("LIC−ABCDー1234", "LIC-ABCD-1234"),
    ],
)
def test_normalize_license_id(value, expected):
    assert normalize_license_id(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("LIC-ABCD-1234", "LIC-ABCD-1234"),
        (" lic-abcd-1234 ", "LIC-ABCD-1234"),
        ("ＬＩＣ－ＡＢＣＤ－１２３４", "LIC-ABCD-1234"),
    ],
)
def test_validate_license_id_accepts_valid_values(value, expected):
    assert validate_license_id(value) == expected


@pytest.mark.parametrize("value", ["", "   ", "LIC_ABC", "LIC ABC", "LIC/ABC", 123])
def test_validate_license_id_rejects_invalid_values(value):
    with pytest.raises(LicenseSettingsValidationError):
        validate_license_id(value)


@pytest.mark.parametrize("device_role", [DEVICE_ROLE_MASTER, DEVICE_ROLE_VIEWER])
def test_validate_device_role_accepts_master_and_viewer(device_role):
    assert validate_device_role(device_role) == device_role


@pytest.mark.parametrize("device_role", ["", "parent", "MASTER", 1])
def test_validate_device_role_rejects_invalid_values(device_role):
    with pytest.raises(LicenseSettingsValidationError):
        validate_device_role(device_role)


def test_validate_license_device_settings_returns_normalized_settings():
    settings = validate_license_device_settings(" lic-abcd-1234 ", DEVICE_ROLE_MASTER)

    assert settings == ValidatedLicenseDeviceSettings(
        license_id="LIC-ABCD-1234",
        device_role=DEVICE_ROLE_MASTER,
    )
