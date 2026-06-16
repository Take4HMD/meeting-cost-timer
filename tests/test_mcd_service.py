from datetime import datetime, timezone
import pytest

from app.models.common import (
    CALCULATION_MODE_DIRECT,
    CALCULATION_MODE_DISPLAY_DATA,
    CALCULATION_MODE_PRECISE,
    CALCULATION_MODE_SIMPLE,
)
from app.models.meeting import MeetingStartSettings
from app.services.mcd_service import (
    DEVICE_ROLE_MASTER,
    DEVICE_ROLE_VIEWER,
    MCD_FILE_TYPE,
    McdChecksumError,
    McdReadRestrictionError,
    McdValidationError,
    calculate_mcd_checksum,
    create_mcd_payload,
    export_mcd,
    load_mcd,
    meeting_settings_from_mcd_payload,
)


def _settings(
    calculation_mode: str = CALCULATION_MODE_PRECISE,
) -> MeetingStartSettings:
    return MeetingStartSettings(
        meeting_name="Sales Meeting",
        calculation_mode=calculation_mode,
        total_hourly_rate=18000,
    )


def test_create_mcd_payload_contains_only_display_data_fields():
    payload = create_mcd_payload(
        settings=_settings(),
        created_device_role=DEVICE_ROLE_MASTER,
        license_id="lic-test-001",
        created_at=datetime(2026, 6, 4, 10, 0, 0, tzinfo=timezone.utc),
    )

    assert set(payload.keys()) == {
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
    assert payload["file_type"] == MCD_FILE_TYPE
    assert payload["license_id"] == "LIC-TEST-001"
    assert "participants" not in payload
    assert "role_rates" not in payload
    assert "role_counts" not in payload
    assert "hourly_rate_details" not in payload


def test_export_and_load_mcd_round_trip_for_viewer(tmp_path):
    output_path = tmp_path / "meeting.mcd"
    settings = _settings(CALCULATION_MODE_SIMPLE)

    export_mcd(
        settings=settings,
        output_path=output_path,
        created_device_role=DEVICE_ROLE_MASTER,
        license_id="LIC-TEST-001",
        created_at=datetime(2026, 6, 4, 10, 0, 0, tzinfo=timezone.utc),
    )
    loaded_settings = load_mcd(
        output_path,
        current_device_role=DEVICE_ROLE_VIEWER,
        current_license_id="LIC-TEST-001",
    )

    assert loaded_settings == settings


def test_load_mcd_allows_viewer_regardless_of_license(tmp_path):
    output_path = tmp_path / "meeting.mcd"
    export_mcd(
        settings=_settings(),
        output_path=output_path,
        created_device_role=DEVICE_ROLE_MASTER,
        license_id="LIC-TEST-001",
    )

    assert load_mcd(
        output_path,
        current_device_role=DEVICE_ROLE_VIEWER,
        current_license_id="LIC-OTHER-001",
    ) == _settings()


def test_load_mcd_rejects_same_license_master_to_master(tmp_path):
    output_path = tmp_path / "meeting.mcd"
    export_mcd(
        settings=_settings(),
        output_path=output_path,
        created_device_role=DEVICE_ROLE_MASTER,
        license_id="LIC-TEST-001",
    )

    with pytest.raises(McdReadRestrictionError):
        load_mcd(
            output_path,
            current_device_role=DEVICE_ROLE_MASTER,
            current_license_id="LIC-TEST-001",
        )


def test_load_mcd_allows_different_license_master_to_master(tmp_path):
    output_path = tmp_path / "meeting.mcd"
    export_mcd(
        settings=_settings(),
        output_path=output_path,
        created_device_role=DEVICE_ROLE_MASTER,
        license_id="LIC-TEST-001",
    )

    assert load_mcd(
        output_path,
        current_device_role=DEVICE_ROLE_MASTER,
        current_license_id="LIC-OTHER-001",
    ) == _settings()


def test_meeting_settings_from_mcd_payload_rejects_tampered_payload():
    payload = create_mcd_payload(
        settings=_settings(),
        created_device_role=DEVICE_ROLE_VIEWER,
        license_id="LIC-TEST-001",
    )
    payload["total_hourly_rate"] = 1

    with pytest.raises(McdChecksumError):
        meeting_settings_from_mcd_payload(
            payload,
            current_device_role=DEVICE_ROLE_VIEWER,
            current_license_id="LIC-TEST-001",
        )


@pytest.mark.parametrize("unsupported_key", ["participants", "role_counts", "role_rates"])
def test_meeting_settings_from_mcd_payload_rejects_unsupported_keys(
    unsupported_key,
):
    payload = create_mcd_payload(
        settings=_settings(),
        created_device_role=DEVICE_ROLE_VIEWER,
        license_id="LIC-TEST-001",
    )
    payload[unsupported_key] = []
    payload["checksum"] = calculate_mcd_checksum(payload)

    with pytest.raises(McdValidationError):
        meeting_settings_from_mcd_payload(
            payload,
            current_device_role=DEVICE_ROLE_VIEWER,
            current_license_id="LIC-TEST-001",
        )


@pytest.mark.parametrize(
    "calculation_mode",
    [CALCULATION_MODE_PRECISE, CALCULATION_MODE_SIMPLE, CALCULATION_MODE_DIRECT],
)
def test_create_mcd_payload_accepts_mcd_calculation_modes(calculation_mode):
    payload = create_mcd_payload(
        settings=_settings(calculation_mode),
        created_device_role=DEVICE_ROLE_VIEWER,
        license_id="LIC-TEST-001",
    )

    assert payload["calculation_mode"] == calculation_mode


def test_create_mcd_payload_rejects_display_data_mode():
    with pytest.raises(McdValidationError):
        create_mcd_payload(
            settings=_settings(CALCULATION_MODE_DISPLAY_DATA),
            created_device_role=DEVICE_ROLE_VIEWER,
            license_id="LIC-TEST-001",
        )


def test_create_mcd_payload_rejects_empty_meeting_name():
    with pytest.raises(McdValidationError):
        create_mcd_payload(
            settings=MeetingStartSettings(
                meeting_name="",
                calculation_mode=CALCULATION_MODE_DIRECT,
                total_hourly_rate=1000,
            ),
            created_device_role=DEVICE_ROLE_VIEWER,
            license_id="LIC-TEST-001",
        )


def test_export_mcd_logs_validation_error_without_meeting_details(tmp_path):
    output_path = tmp_path / "meeting.mcd"

    with pytest.raises(McdValidationError):
        export_mcd(
            settings=MeetingStartSettings(
                meeting_name="",
                calculation_mode=CALCULATION_MODE_DIRECT,
                total_hourly_rate=1000,
            ),
            output_path=output_path,
            created_device_role=DEVICE_ROLE_VIEWER,
            license_id="LIC-TEST-001",
            log_file=tmp_path / "logs" / "error.log",
        )

    log_content = (tmp_path / "logs" / "error.log").read_text(encoding="utf-8")
    assert "mcd_export" in log_content
    assert "McdError" in log_content
    assert "McdValidationError" in log_content
    assert "LIC-TEST-001" not in log_content
    assert "1000" not in log_content


def test_load_mcd_rejects_invalid_json(tmp_path):
    input_path = tmp_path / "broken.mcd"
    input_path.write_text("{ invalid json", encoding="utf-8")

    with pytest.raises(McdValidationError):
        load_mcd(
            input_path,
            current_device_role=DEVICE_ROLE_VIEWER,
            current_license_id="LIC-TEST-001",
        )
