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
        raise LicenseSettingsValidationError("ライセンスIDを文字列で入力してください。")

    normalized = unicodedata.normalize("NFKC", license_id)
    normalized = normalized.translate(HYPHEN_TRANSLATION)
    return normalized.strip().upper()


def validate_license_id(license_id: str) -> str:
    normalized = normalize_license_id(license_id)
    if not normalized:
        raise LicenseSettingsValidationError("ライセンスIDを入力してください。")
    if not LICENSE_ID_PATTERN.fullmatch(normalized):
        raise LicenseSettingsValidationError(
            "ライセンスIDは半角英数字とハイフンで入力してください。"
        )
    return normalized


def validate_device_role(device_role: str) -> str:
    if not isinstance(device_role, str):
        raise LicenseSettingsValidationError("端末種別を選択してください。")
    if device_role not in SAVEABLE_DEVICE_ROLES:
        raise LicenseSettingsValidationError("端末種別を選択してください。")
    if device_role not in VALID_DEVICE_ROLES:
        raise LicenseSettingsValidationError("選択された端末種別は利用できません。")
    return device_role


def validate_license_device_settings(
    license_id: str,
    device_role: str,
) -> ValidatedLicenseDeviceSettings:
    return ValidatedLicenseDeviceSettings(
        license_id=validate_license_id(license_id),
        device_role=validate_device_role(device_role),
    )
