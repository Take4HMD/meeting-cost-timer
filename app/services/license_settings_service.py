from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from config.settings import VALID_DEVICE_ROLES


DEVICE_ROLE_MASTER = "master"
DEVICE_ROLE_VIEWER = "viewer"
SAVEABLE_DEVICE_ROLES = {DEVICE_ROLE_MASTER, DEVICE_ROLE_VIEWER}
LICENSE_ID_PATTERN = re.compile(r"^[A-Z0-9-]+$")
HYPHEN_TRANSLATION = str.maketrans(
    {
        "‐": "-",
        "‑": "-",
        "‒": "-",
        "–": "-",
        "—": "-",
        "―": "-",
        "−": "-",
        "ー": "-",
    }
)


class LicenseSettingsValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ValidatedLicenseDeviceSettings:
    license_id: str
    device_role: str


def normalize_license_id(license_id: str) -> str:
    if not isinstance(license_id, str):
        raise LicenseSettingsValidationError("license_id must be a string")

    normalized = unicodedata.normalize("NFKC", license_id)
    normalized = normalized.translate(HYPHEN_TRANSLATION)
    return normalized.strip().upper()


def validate_license_id(license_id: str) -> str:
    normalized = normalize_license_id(license_id)
    if not normalized:
        raise LicenseSettingsValidationError("license_id must not be empty")
    if not LICENSE_ID_PATTERN.fullmatch(normalized):
        raise LicenseSettingsValidationError("license_id format is invalid")
    return normalized


def validate_device_role(device_role: str) -> str:
    if not isinstance(device_role, str):
        raise LicenseSettingsValidationError("device_role must be a string")
    if device_role not in SAVEABLE_DEVICE_ROLES:
        raise LicenseSettingsValidationError("device_role is invalid")
    if device_role not in VALID_DEVICE_ROLES:
        raise LicenseSettingsValidationError("device_role is not supported")
    return device_role


def validate_license_device_settings(
    license_id: str,
    device_role: str,
) -> ValidatedLicenseDeviceSettings:
    return ValidatedLicenseDeviceSettings(
        license_id=validate_license_id(license_id),
        device_role=validate_device_role(device_role),
    )
