from datetime import datetime, timedelta

import pytest

from app.models import (
    CALCULATION_MODE_DIRECT,
    CALCULATION_MODE_DISPLAY_DATA,
    CALCULATION_MODE_PRECISE,
    CALCULATION_MODE_SIMPLE,
    UNSET_MEETING_NAME,
    MeetingResult,
    MeetingStartSettings,
    Participant,
    RoleRate,
)


def test_participant_model_accepts_spec_fields():
    participant = Participant(
        participant_id="P-000001",
        is_active=True,
        name="Yamada Taro",
        department="Sales",
        position="Manager",
        display_name="Tokyo",
        hourly_rate=6000,
        sort_order=1,
    )

    assert participant.identity_key == ("Yamada Taro", "Sales", "Manager", "Tokyo")


def test_participant_model_requires_name_and_positive_hourly_rate():
    with pytest.raises(TypeError):
        Participant(
            participant_id="P-000001",
            is_active=True,
            name="Yamada Taro",
        )

    with pytest.raises(ValueError):
        Participant(
            participant_id="P-000001",
            is_active=True,
            name="",
            hourly_rate=6000,
        )

    with pytest.raises(ValueError):
        Participant(
            participant_id="P-000001",
            is_active=True,
            name="Yamada Taro",
            hourly_rate=0,
        )


def test_role_rate_model_accepts_spec_fields():
    role_rate = RoleRate(
        role_rate_id="R-000001",
        is_active=True,
        role_name="Manager",
        hourly_rate=6000,
        sort_order=1,
    )

    assert role_rate.role_name == "Manager"
    assert role_rate.hourly_rate == 6000


def test_role_rate_model_requires_role_name_and_positive_hourly_rate():
    with pytest.raises(ValueError):
        RoleRate(
            role_rate_id="R-000001",
            is_active=True,
            role_name="",
            hourly_rate=6000,
        )

    with pytest.raises(ValueError):
        RoleRate(
            role_rate_id="R-000001",
            is_active=True,
            role_name="Manager",
            hourly_rate=0,
        )


@pytest.mark.parametrize(
    "calculation_mode",
    [
        CALCULATION_MODE_PRECISE,
        CALCULATION_MODE_SIMPLE,
        CALCULATION_MODE_DISPLAY_DATA,
        CALCULATION_MODE_DIRECT,
    ],
)
def test_meeting_start_settings_accepts_supported_modes(calculation_mode):
    settings = MeetingStartSettings(
        meeting_name="",
        calculation_mode=calculation_mode,
        total_hourly_rate=18000,
    )

    assert settings.display_meeting_name == UNSET_MEETING_NAME


def test_meeting_start_settings_rejects_invalid_values():
    with pytest.raises(ValueError):
        MeetingStartSettings(
            meeting_name="Sales Meeting",
            calculation_mode="unsupported",
            total_hourly_rate=18000,
        )

    with pytest.raises(ValueError):
        MeetingStartSettings(
            meeting_name="Sales Meeting",
            calculation_mode=CALCULATION_MODE_DIRECT,
            total_hourly_rate=0,
        )


def test_meeting_result_model_accepts_output_fields():
    start_datetime = datetime(2026, 6, 4, 10, 0, 0)
    end_datetime = start_datetime + timedelta(minutes=30)

    result = MeetingResult(
        meeting_name="Sales Meeting",
        calculation_mode=CALCULATION_MODE_SIMPLE,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        actual_count_seconds=1800,
        total_hourly_rate=12000,
        meeting_cost=6000.5,
    )

    assert result.display_meeting_name == "Sales Meeting"


def test_meeting_result_model_rejects_invalid_result_values():
    start_datetime = datetime(2026, 6, 4, 10, 0, 0)

    with pytest.raises(ValueError):
        MeetingResult(
            meeting_name="Sales Meeting",
            calculation_mode=CALCULATION_MODE_SIMPLE,
            start_datetime=start_datetime,
            end_datetime=start_datetime - timedelta(seconds=1),
            actual_count_seconds=0,
            total_hourly_rate=12000,
            meeting_cost=0,
        )

    with pytest.raises(ValueError):
        MeetingResult(
            meeting_name="Sales Meeting",
            calculation_mode=CALCULATION_MODE_SIMPLE,
            start_datetime=start_datetime,
            end_datetime=start_datetime,
            actual_count_seconds=-1,
            total_hourly_rate=12000,
            meeting_cost=0,
        )
