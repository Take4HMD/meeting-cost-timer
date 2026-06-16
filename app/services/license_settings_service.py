from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from config.settings import VALID_DEVICE_ROLES


DEVICE_ROLE_MASTER = "master"
DEVICE_ROLE_VIEWER = "viewer"
SAVEABLE_DEVICE_ROLES = {DEVICE_ROLE_MASTER, DEVICE_ROLE_VIEWER}
LICENSE_ID_PREFIX = "MCT"
LICENSE_ID_RANDOM_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
LICENSE_ID_CHECK_SOURCE_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LICENSE_ID_CHECK_WEIGHTS = (3, 5, 7, 11, 13, 17, 19)
LICENSE_ID_PATTERN = re.compile(
    rf"^{LICENSE_ID_PREFIX}-(\d{{6}})-"
    rf"([{LICENSE_ID_RANDOM_ALPHABET}]{{4}})-"
    rf"([{LICENSE_ID_RANDOM_ALPHABET}]{{4}})-"
    rf"([{LICENSE_ID_RANDOM_ALPHABET}])$"
)
LICENSE_ID_FORMAT_ERROR_MESSAGE = (
    "ライセンスIDは MCT-YYYYMM-XXXX-XXXX-C 形式で入力してください。"
)
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


def calculate_license_check_digit(license_id_body: str) -> str:
    body = license_id_body.replace("-", "").upper()
    total = 0
    for index, char in enumerate(body):
        try:
            char_value = LICENSE_ID_CHECK_SOURCE_CHARS.index(char)
        except ValueError as exc:
            raise LicenseSettingsValidationError(
                LICENSE_ID_FORMAT_ERROR_MESSAGE
            ) from exc
        total += char_value * LICENSE_ID_CHECK_WEIGHTS[
            index % len(LICENSE_ID_CHECK_WEIGHTS)
        ]
    return LICENSE_ID_RANDOM_ALPHABET[total % len(LICENSE_ID_RANDOM_ALPHABET)]


def validate_license_id(license_id: str) -> str:
    normalized = normalize_license_id(license_id)
    if not normalized:
        raise LicenseSettingsValidationError("ライセンスIDを入力してください。")
    match = LICENSE_ID_PATTERN.fullmatch(normalized)
    if not match:
        raise LicenseSettingsValidationError(LICENSE_ID_FORMAT_ERROR_MESSAGE)

    issue_yyyymm, random_part_1, random_part_2, check_digit = match.groups()
    issue_month = int(issue_yyyymm[4:6])
    if issue_month < 1 or issue_month > 12:
        raise LicenseSettingsValidationError(LICENSE_ID_FORMAT_ERROR_MESSAGE)

    expected_check_digit = calculate_license_check_digit(
        f"{LICENSE_ID_PREFIX}{issue_yyyymm}{random_part_1}{random_part_2}"
    )
    if check_digit != expected_check_digit:
        raise LicenseSettingsValidationError(
            "ライセンスIDのチェック桁が正しくありません。"
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
