from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from pathlib import Path

from app.models.common import (
    CALCULATION_MODE_DIRECT,
    CALCULATION_MODE_PRECISE,
    CALCULATION_MODE_SIMPLE,
)
from app.models.meeting import MeetingStartSettings
from app.utils.logging_config import configure_error_logging, log_exception


MCD_SCHEMA_VERSION = 1
MCD_FILE_TYPE = "meeting_cost_display"
MCD_CHECKSUM_SECRET = b"meeting-cost-timer-mcd-integrity-v1"
MCD_CALCULATION_MODES = {
    CALCULATION_MODE_PRECISE,
    CALCULATION_MODE_SIMPLE,
    CALCULATION_MODE_DIRECT,
}
DEVICE_ROLE_MASTER = "master"
DEVICE_ROLE_VIEWER = "viewer"
DEVICE_ROLES = {DEVICE_ROLE_MASTER, DEVICE_ROLE_VIEWER}
JST = timezone(timedelta(hours=9))


class McdError(Exception):
    pass


class McdValidationError(McdError):
    pass


class McdChecksumError(McdError):
    pass


class McdReadRestrictionError(McdError):
    pass


def export_mcd(
    settings: MeetingStartSettings,
    output_path: Path,
    created_device_role: str,
    license_id: str,
    created_at: datetime | None = None,
    log_file: Path | None = None,
) -> None:
    try:
        payload = create_mcd_payload(
            settings=settings,
            created_device_role=created_device_role,
            license_id=license_id,
            created_at=created_at,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:
        logger = configure_error_logging(log_file)
        log_exception("mcd_export", McdError(type(exc).__name__), output_path, logger)
        raise


def load_mcd(
    input_path: Path,
    current_device_role: str,
    current_license_id: str,
) -> MeetingStartSettings:
    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        return meeting_settings_from_mcd_payload(
            payload,
            current_device_role=current_device_role,
            current_license_id=current_license_id,
        )
    except json.JSONDecodeError as exc:
        logger = configure_error_logging()
        log_exception("mcd_load", exc, input_path, logger)
        raise McdValidationError("mcd file format is invalid") from exc
    except (OSError, McdError) as exc:
        logger = configure_error_logging()
        log_exception("mcd_load", exc, input_path, logger)
        raise


def create_mcd_payload(
    settings: MeetingStartSettings,
    created_device_role: str,
    license_id: str,
    created_at: datetime | None = None,
) -> dict:
    _validate_mcd_settings(settings)
    _require_device_role(created_device_role, "created_device_role")
    normalized_license_id = _normalize_license_id(license_id)
    timestamp = created_at or datetime.now(JST)
    if not isinstance(timestamp, datetime):
        raise McdValidationError("created_at must be a datetime")

    payload = {
        "schema_version": MCD_SCHEMA_VERSION,
        "file_type": MCD_FILE_TYPE,
        "meeting_name": settings.meeting_name.strip(),
        "calculation_mode": settings.calculation_mode,
        "total_hourly_rate": settings.total_hourly_rate,
        "created_device_role": created_device_role,
        "license_id": normalized_license_id,
        "created_at": timestamp.isoformat(),
    }
    payload["checksum"] = calculate_mcd_checksum(payload)
    return payload


def meeting_settings_from_mcd_payload(
    payload: dict,
    current_device_role: str,
    current_license_id: str,
) -> MeetingStartSettings:
    _validate_mcd_payload(payload)
    _require_device_role(current_device_role, "current_device_role")
    normalized_license_id = _normalize_license_id(current_license_id)

    expected_checksum = calculate_mcd_checksum(payload)
    if not hmac.compare_digest(payload["checksum"], expected_checksum):
        raise McdChecksumError("mcd checksum is invalid")

    if (
        current_device_role == DEVICE_ROLE_MASTER
        and payload["created_device_role"] == DEVICE_ROLE_MASTER
        and payload["license_id"] == normalized_license_id
    ):
        raise McdReadRestrictionError("same-license master mcd cannot be loaded")

    return MeetingStartSettings(
        meeting_name=payload["meeting_name"],
        calculation_mode=payload["calculation_mode"],
        total_hourly_rate=payload["total_hourly_rate"],
    )


def calculate_mcd_checksum(payload: dict) -> str:
    checksum_payload = {key: value for key, value in payload.items() if key != "checksum"}
    message = json.dumps(
        checksum_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hmac.new(MCD_CHECKSUM_SECRET, message, hashlib.sha256).hexdigest()


def _validate_mcd_settings(settings: MeetingStartSettings) -> None:
    if not isinstance(settings, MeetingStartSettings):
        raise McdValidationError("settings must be MeetingStartSettings")
    if not settings.meeting_name.strip():
        raise McdValidationError("meeting_name must not be empty")
    if settings.calculation_mode not in MCD_CALCULATION_MODES:
        raise McdValidationError("calculation_mode is invalid for mcd")


def _validate_mcd_payload(payload: dict) -> None:
    if not isinstance(payload, dict):
        raise McdValidationError("mcd payload must be an object")

    required_keys = {
        "schema_version",
        "file_type",
        "meeting_name",
        "calculation_mode",
        "total_hourly_rate",
        "created_device_role",
        "license_id",
        "created_at",
        "checksum",
    }
    if required_keys.difference(payload.keys()):
        raise McdValidationError("mcd payload is missing required keys")
    if set(payload.keys()) != required_keys:
        raise McdValidationError("mcd payload contains unsupported keys")
    if payload["schema_version"] != MCD_SCHEMA_VERSION:
        raise McdValidationError("unsupported mcd schema_version")
    if payload["file_type"] != MCD_FILE_TYPE:
        raise McdValidationError("mcd file_type is invalid")
    if not isinstance(payload["meeting_name"], str) or not payload["meeting_name"].strip():
        raise McdValidationError("meeting_name must not be empty")
    if payload["calculation_mode"] not in MCD_CALCULATION_MODES:
        raise McdValidationError("calculation_mode is invalid")
    if not isinstance(payload["total_hourly_rate"], int) or isinstance(
        payload["total_hourly_rate"], bool
    ):
        raise McdValidationError("total_hourly_rate must be an integer")
    if payload["total_hourly_rate"] < 1:
        raise McdValidationError("total_hourly_rate must be at least 1")
    _require_device_role(payload["created_device_role"], "created_device_role")
    _normalize_license_id(payload["license_id"])
    try:
        datetime.fromisoformat(payload["created_at"])
    except ValueError as exc:
        raise McdValidationError("created_at must be an ISO datetime") from exc
    if not isinstance(payload["checksum"], str) or not payload["checksum"]:
        raise McdValidationError("checksum must not be empty")


def _require_device_role(value: str, field_name: str) -> None:
    if value not in DEVICE_ROLES:
        raise McdValidationError(f"{field_name} is invalid")


def _normalize_license_id(license_id: str) -> str:
    if not isinstance(license_id, str):
        raise McdValidationError("license_id must be a string")
    normalized = license_id.strip().upper()
    if not normalized:
        raise McdValidationError("license_id must not be empty")
    return normalized
